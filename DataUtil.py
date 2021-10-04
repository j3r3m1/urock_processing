# -*- coding: utf-8 -*-
import zipfile
import os
import shutil
import errno
import numpy as np
import netCDF4 as nc4

from GlobalVariables import *


def decompressZip(dirPath, inputFileName, outputFileBaseName=None, 
                  deleteZip = False):
    """
    Decompress zip file.

    Parameters
    _ _ _ _ _ _ _ _ _ _ 
        dirPath: String
            Directory path where is located the zip file    
        inputFileName: String
            Name of the file to unzip (with .zip at the end)
        outputFileBaseName: String
            Base name of the file to unzip (without extension)
        deleteZip: boolean, default False
            Whether or not the input zip file should be removed

    Returns
    -------
        None
    """
    print("Start decompressing zip file")
    
    with open(os.path.join(dirPath,inputFileName), "rb") as zipsrc:
        zfile = zipfile.ZipFile(zipsrc)
        for member in zfile.infolist():
            print(member.filename+" is being decompressed" )
            if outputFileBaseName is None:
                target_path=os.path.join(dirPath,member.filename)
            else:
                # Initialize output file path
                target_path = os.path.join(dirPath, outputFileBaseName)
                extension = "." + member.filename.split(".")[-1]
                target_path+=extension
            
            # Create a folder if needed
            if target_path.endswith('/'):  # folder entry, create
                try:
                    os.makedirs(target_path)
                except (OSError, IOError) as err:
                    # Windows may complain if the folders already exist
                    if err.errno != errno.EEXIST:
                        raise
                continue
            with open(target_path, 'wb') as outfile, zfile.open(member) as infile:
                shutil.copyfileobj(infile, outfile)
    
    return None

def degToRad(angleDeg, origin = 0, direction = "CLOCKWISE"):
    """Convert angle arrays from degrees to radian.
    
    Parameters
	_ _ _ _ _ _ _ _ _ _ 
		angleDeg : float
			Angle in degrees
		origin : float, default 0
			Origin of the input degree coordinates (given in a reference North clockwise coordinate system)
		direction : {"CLOCKWISE", "COUNTER-CLOCKWISE"}, default "CLOCKWISE"
			Direction where go the input coordinate
    
    Returns
	_ _ _ _ _ _ _ _ _ _ 	
		angle in radian (trigonometric reference).
    """
    if direction == "CLOCKWISE":
        d = 1
    if direction == "COUNTER-CLOCKWISE":
        d = -1
    
    return (angleDeg+d*origin)*np.pi/180

def postfix(tableName, suffix = None, separator = "_"):
    """ Add a suffix to an input table name
    
    Parameters
	_ _ _ _ _ _ _ _ _ _ 
		tableName : String
			Name of the input table
        suffix : String, default None (then current datetime is used as string)
            Suffix to add to the table name
        separator : String, default "_"
            Character to separate tableName from suffix
            
    
    Returns
	_ _ _ _ _ _ _ _ _ _ 	
		The input table name with the suffix"""
    if suffix is None:
        suffix = datetime.now().strftime("%Y%m%d%H%M%S")
    
    return tableName+separator+suffix

def prefix(tableName, prefix = PREFIX_NAME, separator = "_"):
    """ Add a suffix to an input table name
    
    Parameters
	_ _ _ _ _ _ _ _ _ _ 
		tableName : String
			Name of the input table
        prefix : String
            Prefix to add to the table name
        separator : String, default "_"
            Character to separate prefix from tableName 
    
    Returns
	_ _ _ _ _ _ _ _ _ _ 	
		The input table name with the prefix"""
        
    return prefix+separator+tableName

def getColumns(cursor, tableName):
    """ Get the column name of a table into a list
    
    Parameters
	_ _ _ _ _ _ _ _ _ _ 
        cursor: conn.cursor
            A cursor object, used to perform spatial SQL queries
		tableName : String
			Name of the input table
    
    Returns
	_ _ _ _ _ _ _ _ _ _ 	
		columnNames: list
            A list of the table column names"""
    cursor.execute("""SELECT * FROM {0}""".format(tableName))
    columnNames = [info[0] for info in cursor.description]
    
    return columnNames

def saveTable(cursor, tableName, filedir, delete):
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
		None"""
    # Get extension
    extension = filedir.split(".")[-1]
    
    # Define the H2GIS function depending on extension
    if extension.upper() == "GEOJSON":
        h2_function = "GEOJSONWRITE"
    elif extension.upper() == "SHP":
        h2_function = "SHPWRITE"
    else:
        print("The extension should be .geojson or .shp")
    
    # Delete files
    if delete and os.path.isfile(filedir):
        os.remove(filedir)
        if extension.upper() == "SHP":
            filedirWithoutExt = filedir.split(".")[0]
            os.remove(filedirWithoutExt+".dbf")
            os.remove(filedirWithoutExt+".shx")
            if os.path.isfile(filedir+".prj"):
                os.remove(filedirWithoutExt+".prj")
                
    # Write files
    cursor.execute("""CALL {0}('{1}','{2}')""".format(h2_function,
                                                      filedir,
                                                      tableName))
    
    return None

def readFunction(extension):
    """ Return the name of the right H2GIS function to use depending of the file extension
    
    Parameters
	_ _ _ _ _ _ _ _ _ _ 
        extension: String
            Extension of the vector file (shp or geojson)
    
    Returns
	_ _ _ _ _ _ _ _ _ _ 	
		h2gisFunctionName: String
            Return the name of the H2GIS function to use"""
    if extension.lower() == "shp":
        return "SHPREAD"
    elif extension.lower() == "geojson":
        return "GEOJSONREAD"
    
def createIndex(tableName, fieldName, isSpatial):
    """ Return the SQL query needed to create an index on a given field of a
    given table. The index should be indicated as spatial if the field is
    a geometry field.
    
    Parameters
	_ _ _ _ _ _ _ _ _ _ 
        tableName: String
            Name of the table
        fieldName: String
            Name of the field the index will be created on
        isSpatial: boolean
            Whether or not the index is a spatial index (should be True if
                                                         the field is a geometry field)
    
    Returns
	_ _ _ _ _ _ _ _ _ _ 	
		query: String
            Return the SQL query needed to create the index"""
    spatialKeyWord = ""
    if isSpatial:
        spatialKeyWord = " SPATIAL "
    query = "CREATE {0} INDEX IF NOT EXISTS id_{1}_{2} ON {2}({1});".format(spatialKeyWord,
                                                                           fieldName,
                                                                           tableName)
    return query

def radToDeg(data, origin = 90, direction = "CLOCKWISE"):
    """Convert angle arrays from radian to degree.
    
    Parameters
	_ _ _ _ _ _ _ _ _ _ 
		data : pd.Series()
			Array containing the angle values to convert from radian to degree.
		origin : float
			Origin of the output coordinate (given in a reference trigonometric coordinate)
		direction : {"CLOCKWISE", "COUNTER-CLOCKWISE"}, default "CLOCKWISE"
			Direction where go the output coordinate
    
    Returns
	_ _ _ _ _ _ _ _ _ _ 	
		Array containing the data in degree coordinate.
    """
    if direction == "CLOCKWISE":
        degree = (360 - data * 180 / np.pi) + origin
    if direction == "COUNTER-CLOCKWISE":
        degree = (data * 180 / np.pi) - origin
    
    degree[degree>360] = degree[degree>360] - 360
    degree[degree<0] = degree[degree<0] + 360
    
    return degree

def windDirectionFromXY(windSpeedEast, windSpeedNorth):
    """
    Calculates wind direction from wind speeds in carthesian coordinates.
    
    Parameters
    _ _ _ _ _ _ _ _ _ _ 
        windSpeedEast: pd.Series
            Wind speed along a West->East axis (m/s)
        windSpeedNorth: pd.Series
            Wind speed along a South->North axis (m/s)
    
    Returns
    -------
        pd.Series containing the wind direction from East counterclockwise.
    """
    # Calculate the angle in Radian in a [-pi/2, pi/2]
    radAngle = np.zeros(windSpeedEast.shape)
    radAngle[windSpeedEast==0] = 0
    if type(windSpeedEast) == type(pd.Series()):
        radAngle[windSpeedEast!=0] = np.arctan(windSpeedNorth[windSpeedEast!=0]\
                                               .divide(windSpeedEast[windSpeedEast!=0]))
    else:
        radAngle[windSpeedEast!=0] = np.arctan(windSpeedNorth[windSpeedEast!=0]
                                               /windSpeedEast[windSpeedEast!=0])
    
    # Add or subtract pi.2 for left side trigonometric circle vectors
    radAngle[(windSpeedEast<=0)&(windSpeedNorth>0)] = \
        radAngle[(windSpeedEast<=0)&(windSpeedNorth>0)] + np.pi
    radAngle[(windSpeedEast<0)&(windSpeedNorth<=0)] = \
        radAngle[(windSpeedEast<0)&(windSpeedNorth<=0)] + np.pi
    radAngle[(windSpeedEast>=0)&(windSpeedNorth<0)] = \
        radAngle[(windSpeedEast>=0)&(windSpeedNorth<0)] + 2*np.pi
    
    return radAngle

# https://pyhogs.github.io/intro_netcdf4.html
def saveToNetCDF(longitude,
                 latitude,
                 x,
                 y,
                 z,
                 u,
                 v,
                 w,
                 verticalWindProfile,
                 path = OUTPUT_DIRECTORY + os.sep + OUTPUT_NETCDF_FILE):
    """
    Create a netCDF file and save wind speed, direction and initial 
    vertical wind profile in it.
    
    Parameters
    _ _ _ _ _ _ _ _ _ _ 
        windSpeedEast: pd.Series
            Wind speed along a West->East axis (m/s)
        windSpeedNorth: pd.Series
            Wind speed along a South->North axis (m/s)
    
    Returns
    -------
        pd.Series containing the wind direction from East counterclockwise.
    """
     # Opens a netCDF file in writing mode ('w')
    f = nc4.Dataset(path+'.nc','w', format='NETCDF4')
    
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