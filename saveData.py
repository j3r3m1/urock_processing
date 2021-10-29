#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  4 13:59:31 2021

@author: Jérémy Bernard, University of Gothenburg
"""
import pandas as pd
import numpy as np
from .DataUtil import radToDeg, windDirectionFromXY, createIndex
from osgeo.gdal import Grid, GridOptions
from .GlobalVariables import HORIZ_WIND_DIRECTION, HORIZ_WIND_SPEED, WIND_SPEED,\
    ID_POINT, TEMPO_DIRECTORY, TEMPO_HORIZ_WIND_FILE, VERT_WIND_SPEED, GEOM_FIELD,\
    OUTPUT_DIRECTORY, MESH_SIZE, OUTPUT_FILENAME, DELETE_OUTPUT_IF_EXISTS,\
    OUTPUT_RASTER_EXTENSION, OUTPUT_VECTOR_EXTENSION, OUTPUT_NETCDF_EXTENSION
from datetime import datetime
import netCDF4 as nc4
import os

def saveBasicOutputs(cursor, z_out, dz, u, v, w, gridName, 
                     rotationCenterCoordinates, windDirection,
                     verticalWindProfile, outputFilePathAndNameBase,
                     meshSize, outputRaster = None, saveRaster = True,
                     saveVector = True, saveNetcdf = True):

    # -------------------------------------------------------------------
    # SAVE NETCDF -------------------------------------------------------
    # ------------------------------------------------------------------- 
    if saveNetcdf:    
        # Get the srid of the input geometry
        cursor.execute(""" SELECT ST_SRID({0}) AS srid FROM {1} LIMIT 1
                       """.format( GEOM_FIELD,
                                   gridName))
        srid = cursor.fetchall()[0][0]
        # Get the coordinate in lat/lon of each point
        cursor.execute(""" 
           SELECT ST_X({0}) AS LON, ST_Y({0}) AS LAT FROM 
           (SELECT ST_TRANSFORM(ST_SETSRID({0},{2}), 4326) AS {0} FROM {1})
           """.format( GEOM_FIELD,
                       gridName,
                       srid))
        coord = np.array(cursor.fetchall())
        # Convert to a 2D (X, Y) array
        nx = u.shape[0]
        ny = u.shape[1]
        longitude = np.array([[coord[i*ny+j,0] for j in range(ny)] for i in range(nx)])
        latitude = np.array([[coord[i*ny+j,1] for j in range(ny)] for i in range(nx)])
        
    
        # Save the data into a NetCDF file
        # If delete = False, add a suffix to the file
        if os.path.isfile(outputFilePathAndNameBase + OUTPUT_NETCDF_EXTENSION) \
            and not DELETE_OUTPUT_IF_EXISTS :
            outputFilePathAndNameBase = renameFileIfExists(filedir = outputFilePathAndNameBase,
                                                           extension = OUTPUT_NETCDF_EXTENSION)    
        saveToNetCDF(longitude = longitude,
                     latitude = latitude,
                     x = range(nx),
                     y = range(ny),
                     z = verticalWindProfile.index,
                     u = u,
                     v = v,
                     w = w,
                     verticalWindProfile = verticalWindProfile.values,
                     path = outputFilePathAndNameBase)

    for z_i in z_out:
        # Keep only wind field for a single horizontal plan (and convert carthesian
        # wind speed into polar at least for horizontal)
        tempoTable = "TEMPO_HORIZ"
        horizOutputUrock = "HORIZ_OUTPUT_UROCK"
        if z_i % dz % (dz / 2) == 0:
            n_lev = int(z_i / dz) + 1
            ufin = u[:,:,n_lev]
            vfin = v[:,:,n_lev]
            wfin = w[:,:,n_lev]
        else:
            n_lev = int(z_i / dz) + 1
            n_lev1 = n_lev + 1
            weight1 = (z_i - (n_lev - 0.5) * dz) / dz
            weight = 1 - weight1
            ufin = (weight * u[:,:,n_lev] + weight1 * u[:,:,n_lev1])
            vfin = (weight * v[:,:,n_lev] + weight1 * v[:,:,n_lev1])
            wfin = (weight * w[:,:,n_lev] + weight1 * w[:,:,n_lev1])
        df = pd.DataFrame({HORIZ_WIND_SPEED: ((ufin ** 2 + vfin ** 2) ** 0.5).flatten("F"),
                           WIND_SPEED: ((ufin ** 2 + vfin ** 2 + wfin ** 2) ** 0.5).flatten("F"), 
                           HORIZ_WIND_DIRECTION: radToDeg(windDirectionFromXY(ufin, vfin)).flatten("F"), 
                           VERT_WIND_SPEED: wfin.flatten("F")}).rename_axis(ID_POINT)
        
        # Rotate the grid back to initial and save horizontal wind speed, 
        # wind direction and vertical wind speed in a vector file
        df.to_csv(TEMPO_DIRECTORY + os.sep + TEMPO_HORIZ_WIND_FILE)
        cursor.execute(
            """
            DROP TABLE IF EXISTS {9};
            CREATE TABLE {9}({3} INTEGER, {5} DOUBLE, {6} DOUBLE, {7} DOUBLE, {14} DOUBLE)
                AS SELECT {3}, {5}, {6}, {7}, {14} FROM CSVREAD('{13}');
            {0}{1}
            DROP TABLE IF EXISTS {2};
            CREATE TABLE {2}
                AS SELECT   a.{3}, ST_ROTATE(a.{4}, {10}, {11}, {12}) as {4}, b.{5}, 
                            b.{6}, b.{7}, b.{14}
                FROM {8} AS a
                LEFT JOIN {9} AS b
                ON a.{3} = b.{3}
            """.format(createIndex(tableName=gridName, 
                                            fieldName=ID_POINT,
                                            isSpatial=False),
                        createIndex(tableName=tempoTable, 
                                             fieldName=ID_POINT,
                                             isSpatial=False),
                        horizOutputUrock            , ID_POINT,
                        GEOM_FIELD                  , HORIZ_WIND_SPEED,
                        HORIZ_WIND_DIRECTION        , VERT_WIND_SPEED,
                        gridName                    , tempoTable,
                        -windDirection/180*np.pi    , rotationCenterCoordinates[0],
                        rotationCenterCoordinates[1], TEMPO_DIRECTORY + os.sep + TEMPO_HORIZ_WIND_FILE,
                        WIND_SPEED))
        
        # -------------------------------------------------------------------
        # SAVE VECTOR -------------------------------------------------------
        # ------------------------------------------------------------------- 
        if saveVector or saveRaster:
            outputVectorFile = saveTable(cursor = cursor,
                                         tableName = horizOutputUrock,
                                         filedir = outputFilePathAndNameBase +\
                                                   str(z_i).replace(".","_")+\
                                                   OUTPUT_VECTOR_EXTENSION,
                                         delete = DELETE_OUTPUT_IF_EXISTS)
            # -------------------------------------------------------------------
            # SAVE RASTER -------------------------------------------------------
            # -------------------------------------------------------------------     
            if saveRaster:
                # Save the wind speed into a Raster
                # If delete = False, add a suffix to the filename
                if (os.path.isfile(outputFilePathAndNameBase + OUTPUT_RASTER_EXTENSION)) \
                    and (not DELETE_OUTPUT_IF_EXISTS):
                    outputFilePathAndNameBaseRaster = renameFileIfExists(filedir = outputFilePathAndNameBase\
                                                                                   + str(z_i).replace(".","_"),
                                                                         extension = OUTPUT_RASTER_EXTENSION)
                else:
                    outputFilePathAndNameBaseRaster = outputFilePathAndNameBase + str(z_i).replace(".","_")
                # Whether or not a raster output is given as input, the rasterization process is slightly different
                if outputRaster:
                    outputRasterExtent = outputRaster.extent()
                    Grid(destName = outputFilePathAndNameBaseRaster + OUTPUT_RASTER_EXTENSION,
                         srcDS = outputVectorFile,
                         options = GridOptions(format = OUTPUT_RASTER_EXTENSION.split(".")[-1],
                                               zfield = WIND_SPEED, 
                                               width = outputRaster.width(), 
                                               height = outputRaster.height(),
                                               outputBounds = [outputRasterExtent.xMinimum(),
                                                               outputRasterExtent.yMaximum(),
                                                               outputRasterExtent.xMaximum(),
                                                               outputRasterExtent.yMinimum()],
                                               algorithm = "average:radius1={0}:radius2={0}".format(1.1*meshSize)))
                else:
                    cursor.execute(
                        """
                        SELECT  ST_XMIN({0}) AS XMIN, ST_XMAX({0}) AS XMAX,
                                ST_YMIN({0}) AS YMIN, ST_YMAX({0}) AS YMAX
                        FROM    (SELECT ST_ACCUM({0}) AS {0} FROM {1})
                        """.format(GEOM_FIELD            , horizOutputUrock))     
                    vectorBounds = cursor.fetchall()[0]
                    width = int((vectorBounds[1] - vectorBounds[0]) / meshSize) + 1
                    height = int((vectorBounds[3] - vectorBounds[2]) / meshSize) + 1
                    Grid(destName = outputFilePathAndNameBaseRaster + OUTPUT_RASTER_EXTENSION,
                         srcDS = outputVectorFile,
                         options = GridOptions(format = OUTPUT_RASTER_EXTENSION.split(".")[-1],
                                               zfield = WIND_SPEED, 
                                               width = width, 
                                               height = height,
                                               outputBounds = [vectorBounds[0] - float(meshSize) / 2,
                                                               vectorBounds[3] + float(meshSize) / 2,
                                                               vectorBounds[0] + meshSize * (width - 0.5),
                                                               vectorBounds[3] - meshSize * (height + 0.5)],
                                               algorithm = "average:radius1={0}:radius2={0}".format(1.1*meshSize)))
    
def saveToNetCDF(longitude,
                 latitude,
                 x,
                 y,
                 z,
                 u,
                 v,
                 w,
                 verticalWindProfile,
                 path):
    """
    Create a netCDF file and save wind speed, direction and initial 
    vertical wind profile in it (based on https://pyhogs.github.io/intro_netcdf4.html )
    
    Parameters
    _ _ _ _ _ _ _ _ _ _ 
        longitude: np.array (2D - X, Y)
            Longitude of each of the (X, Y) points
        latitude: np.array (2D - X, Y)
            Longitude of each of the (X, Y) points
        x: np.array (1D)
            X grid coordinates in local referential
        y: np.array (1D)
            Y grid coordinates in local referential
        u: np.array (3D)
            Wind speed along East axis
        v: 2D (X, Y) array
            Wind speed along North axis
        w: 2D (X, Y) array
            Wind speed along vertical axis
        verticalWindSpeedProfile: pd.Series
            Initial wind speed profile along a vertical axis z
        path: String
            Path and filename to save NetCDF file
    
    Returns
    -------
        pd.Series containing the wind direction from East counterclockwise.
    """
     # Opens a netCDF file in writing mode ('w')
    f = nc4.Dataset(path + OUTPUT_NETCDF_EXTENSION,'w', format='NETCDF4')
    
    # 3D WIND SPEED DATA
    # Creates a group within this file for the 3D wind speed
    wind3dGrp = f.createGroup('3D_wind')
    
    # Creates dimensions within this group
    wind3dGrp.createDimension('rlon', len(x))
    wind3dGrp.createDimension('rlat', len(y))
    wind3dGrp.createDimension('z', len(z))
    wind3dGrp.createDimension('u', None)
    wind3dGrp.createDimension('v', None)
    wind3dGrp.createDimension('w', None)
    
    # Build the variables
    rlon = wind3dGrp.createVariable('rlon', 'i4', 'rlon')
    rlat = wind3dGrp.createVariable('rlat', 'i4', 'rlat')
    lon = wind3dGrp.createVariable('lon', 'f4', ('rlon', 'rlat'))
    lat = wind3dGrp.createVariable('lat', 'f4', ('rlon', 'rlat'))
    levels = wind3dGrp.createVariable('Levels', 'i4', 'z')
    windSpeed_x = wind3dGrp.createVariable('windSpeed_x', 'f4', ('rlon', 'rlat', 'z'))
    windSpeed_y = wind3dGrp.createVariable('windSpeed_y', 'f4', ('rlon', 'rlat', 'z'))  
    windSpeed_z = wind3dGrp.createVariable('windSpeed_z', 'f4', ('rlon', 'rlat', 'z'))
    
    # Fill the variables
    rlon[:] = x
    rlat[:] = y
    lon[:,:] = longitude
    lat[:,:] = latitude
    levels[:] = z
    windSpeed_x[:,:,:] = u
    windSpeed_y[:,:,:] = v
    windSpeed_z[:,:,:] = w
    
    # VERTICAL WIND PROFILE DATA
    # Creates a group within this file for the vertical wind profile
    vertWindProfGrp = f.createGroup('vertWind')
    
    # Creates dimensions within this group
    vertWindProfGrp.createDimension('z', len(z))
    
    # Build the variables 
    profileLevels = vertWindProfGrp.createVariable('profileLevels', 'i4', 'z')
    WindSpeed = vertWindProfGrp.createVariable('WindSpeed', 'f4', ('z'))
    
    # Fill the variables
    profileLevels[:] = z
    WindSpeed[:] = verticalWindProfile
    
    
    # ADD METADATA
    #Add local attributes to variable instances
    lon.units = 'degrees east'
    lat.units = 'degrees north'
    windSpeed_x.units = 'meter per second'
    windSpeed_y.units = 'meter per second'
    windSpeed_z.units = 'meter per second'
    levels.units = 'meters'
    WindSpeed.units = 'meter per second'
    profileLevels.units = 'meters'

    #Add global attributes
    f.description = "URock dataset containing one group of 3D wind field value and one group of input vertical wind speed profile"
    f.history = "Created " + datetime.today().strftime("%y-%m-%d")
    
    f.close()
    
def saveTable(cursor, tableName, filedir, delete = False):
    """ Save a table in .geojson or .shp
    
    Parameters
	_ _ _ _ _ _ _ _ _ _ 
        cursor: conn.cursor
            A cursor object, used to perform spatial SQL queries
		tableName : String
			Name of the table to save
        filedir: String
            Directory (including filename and extension) of the file where to 
            store the table
        delete: Boolean, default False
            Whether or not the file is delete if exist
    
    Returns
	_ _ _ _ _ _ _ _ _ _ 	
		output_filedir: String
            Directory (including filename and extension) of the saved file
            (could be different from input 'filedir' since the file may 
             have been renamed if exists)"""
    # Get extension
    extension = "." + filedir.split(".")[-1]
    filedirWithoutExt = ".".join(filedir.split(".")[0:-1])
    
    # Define the H2GIS function depending on extension
    if extension.upper() == ".GEOJSON":
        h2_function = "GEOJSONWRITE"
    elif extension.upper() == ".SHP":
        h2_function = "SHPWRITE"
    else:
        print("The extension should be .geojson or .shp")
    # Delete files if exists and delete = True
    if delete and os.path.isfile(filedir):
        output_filedir = filedir
        os.remove(filedir)
        if extension.upper() == ".SHP":
            os.remove(filedirWithoutExt+".dbf")
            os.remove(filedirWithoutExt+".shx")
            if os.path.isfile(filedirWithoutExt+".prj"):
                os.remove(filedirWithoutExt+".prj")
    # If delete = False, add a suffix to the file
    elif os.path.isfile(filedir):
        output_filedir = renameFileIfExists(filedir = filedirWithoutExt,
                                            extension = extension) + extension
    else:
        output_filedir = filedir
    # Write files
    cursor.execute("""CALL {0}('{1}','{2}')""".format(h2_function,
                                                      output_filedir,
                                                      tableName))
    return output_filedir

def renameFileIfExists(filedir, extension):
    """ Rename a file with a numbering prefix if exists.
    
    Parameters
	_ _ _ _ _ _ _ _ _ _ 
        filedir: String
            Directory (including filename but without extension) of the file
    
    Returns
	_ _ _ _ _ _ _ _ _ _ 	
		newFileDir: String
            Directory with renamed file"""
    i = 1
    newFileDir = filedir
    while(os.path.isfile(newFileDir + extension)):
        newFileDir = filedir + "({0})".format(i)
        i += 1
    return newFileDir