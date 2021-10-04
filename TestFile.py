#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 30 14:21:04 2021

@author: Jérémy Bernard, University of Gothenburg
"""
import os
import MainCalculation
import DataUtil
import matplotlib.colors as colors
import matplotlib.pylab as plt
from processing import gdal

from GlobalVariables import * 

# -----------------------------------------------------------------------------------
# SET INPUT PARAMETERS --------------------------------------------------------------
# -----------------------------------------------------------------------------------
# Geographical input data
caseToRun = "BigArea"
inputGeometries = {"buildingFileName" : "buildings.shp",
                    "vegetationFileName" : "",
                    "cadTriangles" : "",
                    "cadTreesIntersection" : ""}
# inputGeometries = {"buildingFileName" : "",
#                     "vegetationFileName" : "",
#                     "cadTriangles" : "AllTriangles.shp",
#                     "cadTreesIntersection" : "treesIntersection.shp"}
idFieldBuild = ID_FIELD_BUILD
buildingHeightField = "HEIGHT_ROO"

vegetationBaseHeight = "trunk_mean"
vegetationTopHeight = "tot_height"
idVegetation = None
vegetationAttenuationFactor = None

# Meteorological input data
v_ref = 2
windDirection = 296
z_ref = 10

# Meshing properties
alongWindZoneExtend = 30
crossWindZoneExtend = 25
verticalExtend = 20
meshSize = 4
dz = 4

# Other simulation parameters
onlyInitialization = False
saveRockleZones = False
maxIterations = MAX_ITERATIONS
thresholdIterations = THRESHOLD_ITERATIONS
tempoDirectory = TEMPO_DIRECTORY

# Visualization in a GIS parameters
z_gis = 1.5

# Plotting options
plotBoolean = True
isInitialField = True
levelList = [2, 21]

isStream = False
streamDensity = 3
streamWidthFactor = 3

headwidth = 3
headlength = 1.5
headaxislength = 1.5

xRange = [10, 70]
yRange = [60, 140]
zRange = [0, 40]


# -----------------------------------------------------------------------------------
# MAIN CALCULATIONS -----------------------------------------------------------------
# -----------------------------------------------------------------------------------
u, v, w, u0, v0, w0, x, y, z, buildingCoordinates, cursor, gridName,\
rotationCenterCoordinates, verticalWindProfile = \
    MainCalculation.main(   z_ref = z_ref,
                            v_ref = v_ref,
                            windDirection = windDirection,
                            prefix = caseToRun,
                            meshSize = meshSize,
                            dz = dz,    
                            alongWindZoneExtend = alongWindZoneExtend,
                            crossWindZoneExtend = crossWindZoneExtend,
                            verticalExtend = verticalExtend,
                            inputGeometries = inputGeometries,
                            tempoDirectory = tempoDirectory,
                            onlyInitialization = onlyInitialization,
                            maxIterations = maxIterations,
                            thresholdIterations = thresholdIterations,
                            idFieldBuild = idFieldBuild,
                            buildingHeightField = buildingHeightField,
                            vegetationBaseHeight = vegetationBaseHeight,
                            vegetationTopHeight = vegetationTopHeight,
                            idVegetation = idVegetation,
                            vegetationAttenuationFactor = vegetationAttenuationFactor,
                            saveRockleZones = saveRockleZones)

# Keep only a horizontal domain (interpolate linearly instead of using the type of profile)
testPath = "/tmp/test_urock.csv"
finalPath = "/tmp/table_urock.geojson"
testTable = "df_urock"
tableUrock = "table_urock"
horiz_wind_speed = "HWS"
theta = "theta"
if z_gis % dz == 0:
    n_lev = z_gis/dz
    ufin = u[:,:,n_lev]
    vfin = v[:,:,n_lev]
    wfin = w[:,:,n_lev]
else:
    n_lev = int(z_gis/dz)
    n_lev1 = n_lev+1
    weight1 = (z_gis-n_lev*dz)/dz
    weight = 1-weight1
    ufin = (weight*u[:,:,n_lev]+weight1*u[:,:,n_lev1])
    vfin = (weight*v[:,:,n_lev]+weight1*v[:,:,n_lev1])
    wfin = (weight*w[:,:,n_lev]+weight1*w[:,:,n_lev1])
df = pd.DataFrame({horiz_wind_speed: ((ufin**2+vfin**2)**0.5).flatten("F"), 
                   theta: DataUtil.radToDeg(DataUtil.windDirectionFromXY(ufin, vfin)).flatten("F"), 
                   W: wfin.flatten("F")}).rename_axis(ID_POINT)

# Save horizontal wind speed, wind direction and vertical wind speed in a vector file
df.to_csv(testPath)
cursor.execute(
    """
    DROP TABLE IF EXISTS {14};
    CREATE TABLE {14}({3} INTEGER, {5} DOUBLE, {6} DOUBLE, {7} DOUBLE)
        AS SELECT {3}, {5}, {6}, {7} FROM CSVREAD('{13}');
    {0}{1}
    DROP TABLE IF EXISTS {2};
    CREATE TABLE {2}
        AS SELECT a.{3}, ST_ROTATE(a.{4}, {10}, {11}, {12}) as {4}, b.{5}, b.{6}, b.{7}
        FROM {8} AS a
        LEFT JOIN {9} AS b
        ON a.{3} = b.{3}
    """.format(DataUtil.createIndex(tableName=gridName, 
                                    fieldName=ID_POINT,
                                    isSpatial=False),
                DataUtil.createIndex(tableName=testTable, 
                                     fieldName=ID_POINT,
                                     isSpatial=False),
                tableUrock                  , ID_POINT,
                GEOM_FIELD                  , horiz_wind_speed,
                theta                       , W,
                gridName                    , testTable,
                -windDirection/180*np.pi    , rotationCenterCoordinates[0],
                rotationCenterCoordinates[1], testPath,
                testTable))
DataUtil.saveTable(cursor = cursor,
                   tableName = tableUrock,
                   filedir = finalPath,
                   delete = True)

#A MODIFIER POUR AVOIR 3D WIND SPEED AND SAVE AS FLOAT
# Save the wind speed into a Raster
gdal.Rasterize(destNameOrDestDS = "/tmp/test.GTiff",
          srcDS = "/tmp/table_urock.geojson", 
          options = gdal.RasterizeOptions(format = "GTiff", 
                                                     attribute = "HWS", 
                                                     width = 200, 
                                                     height = 200))

# Get the srid of the input geometry
cursor.execute(""" SELECT ST_SRID({0}) AS srid FROM {1} LIMIT 1
               """.format( GEOM_FIELD,
                           gridName))
srid = cursor.fetchall()[0][0]
# Get the coordinate in lat/lon of each point
cursor.execute(""" SELECT ST_X({0}) AS LON, ST_Y({0}) AS LAT FROM 
               (SELECT ST_TRANSFORM(ST_SETSRID({0},{2}), 4326) AS {0} FROM {1})
               """.format( GEOM_FIELD,
                           tableUrock,
                           srid))
coord = np.array(cursor.fetchall())
# Convert to a 2D (X, Y) array
nx = u.shape[0]
ny = u.shape[1]
longitude = np.array([[coord[i*ny+j,0] for j in range(ny)] for i in range(nx)])
latitude = np.array([[coord[i*ny+j,1] for j in range(ny)] for i in range(nx)])

# Save the data into a NetCDF file
DataUtil.saveToNetCDF(longitude = longitude,
                      latitude = latitude,
                      x = range(nx),
                      y = range(ny),
                      z = verticalWindProfile.index,
                      u = u,
                      v = v,
                      w = w,
                      verticalWindProfile = verticalWindProfile.values,
                      path = OUTPUT_DIRECTORY + os.sep + OUTPUT_NETCDF_FILE)

if plotBoolean:
    # -----------------------------------------------------------------------------------
    # POST-PROCESSING -------------------------------------------------------------------
    # -----------------------------------------------------------------------------------
    if isInitialField:
        u_plot = u0
        v_plot = v0
        w_plot = w0
    else:
        u_plot = u
        v_plot = v
        w_plot = w
    # Convert building coordinates to a 3D multiindex object
    iterables = [np.arange(0,x.size), np.arange(0,y.size), np.arange(0,z.size)]
    cells = pd.Series(dtype = "float64",
                      index = pd.MultiIndex.from_product(iterables, names=('x', 'y', 'z')))
    cells.loc[pd.MultiIndex.from_arrays(buildingCoordinates, names=('x', 'y', 'z'))] = 1.
    
    # Calculates wind speed for each cell
    ws_plot = (u_plot**2+v_plot**2+w_plot**2)**0.5
    
    # -----------------------------------------------------------------------------------
    # PLOT FIGURES ----------------------------------------------------------------------
    # -----------------------------------------------------------------------------------
    nrows = int((len(levelList))**0.5)
    ncols = int(len(levelList)/nrows)
    if nrows*ncols < len(levelList):
        ncols += 1
    # 1. Wind field in an (X,Y) plan ----------------------------------------------
    # -----------------------------------------------------------------------------------   
    fig, ax = plt.subplots(nrows = nrows, ncols = ncols, sharex = True, sharey=True)
    for i in range(0,nrows):
        for j, lev in enumerate(levelList[i*ncols:ncols+i*ncols]):
            if nrows>1:
                ax_ij = ax[i]
                if ncols>1:
                    ax_ij = ax[i][j]
            elif ncols>1:
                ax_ij = ax[j]
            else:
                ax_ij = ax
            n_lev = int((lev+dz/2)/dz)
            if isStream:
                lw = streamWidthFactor * ws_plot[:,:,n_lev].transpose() / ws_plot[:,:,n_lev].max()
                ax_ij.streamplot(x, y, u = u_plot[:,:,n_lev].transpose(), 
                                 v = v_plot[:,:,n_lev].transpose(),
                                 density = streamDensity,
                                 linewidth = lw)
            else:
                Q = ax_ij.quiver(x, y, u_plot[:,:,n_lev].transpose(), 
                                 v_plot[:,:,n_lev].transpose(), 
                                 units = 'xy', scale = dz, headwidth = 6,
                                 headlength = 3, headaxislength = 2.5)
                ax_ij.quiverkey(Q, 0.9, 0.9, 1, r'$1 \frac{m}{s}$', labelpos='E',
                                coordinates='figure')
            if len(xRange)==2:
                ax_ij.set_xlim(xRange[0],xRange[1])
            if len(yRange)==2:
                ax_ij.set_ylim(yRange[0],yRange[1])
            
            # Get buildings for the z level considered
            buildZ = cells.xs(n_lev, level = 2)
            
            # Set building pixels in color
            ax_ij.pcolor(buildZ.index.unique(0)*meshSize,
                            buildZ.index.unique(1)*meshSize,
                            buildZ.unstack().transpose().values,
                            shading = "nearest",
                            alpha = 0.8)
            ax_ij.set_title("{0} m".format(n_lev*dz-float(dz)/2))
            
    # -----------------------------------------------------------------------------------    
    # 2. Wind speed in an (X,Y) plan ----------------------------------------------------
    # -----------------------------------------------------------------------------------
    fig, ax = plt.subplots(nrows = nrows, ncols = ncols, sharex = True, sharey=True)
    for i in range(0,nrows):
        for j, lev in enumerate(levelList[i*ncols:ncols+i*ncols]):
            if nrows>1:
                ax_ij = ax[i]
                if ncols>1:
                    ax_ij = ax[i][j]
            elif ncols>1:
                ax_ij = ax[j]
            else:
                ax_ij = ax
            n_lev = int((lev+dz/2)/dz)
            # Set building pixels in black
            pcol = ax_ij.pcolor(ws_plot[:,:,n_lev].transpose(), 
                            cmap = "coolwarm")
            if len(xRange)==2:
                ax_ij.set_xlim(xRange[0],xRange[1])
            if len(yRange)==2:
                ax_ij.set_ylim(yRange[0],yRange[1])
            
            
            # Get buildings for the z level considered
            buildZ = cells.xs(n_lev, level = 2)
            
            # Set building pixels in black
            ax_ij.pcolor(buildZ.index.unique(0),
                            buildZ.index.unique(1),
                            buildZ.unstack().transpose().values,
                            shading = "nearest")
            ax_ij.set_title("{0} m".format(n_lev*dz-float(dz)/2))
            plt.colorbar(pcol, ax = ax_ij)
    
    # ----------------------------------------------------------------------------- 
    # 3. Wind field in an (Y,Z) plan ----------------------------------------------
    # ----------------------------------------------------------------------------- 
    i_plan = int(x.size/2)
    fig, ax = plt.subplots(sharex = True, sharey=True)
    if isStream:
        ax.streamplot(y, z-float(dz)/2, v_plot[i_plan,:,:].transpose(),
                      w_plot[i_plan,:,:].transpose(),
                      density = streamDensity)
    else:
        Q = ax.quiver(y, z-float(dz)/2, v_plot[i_plan,:,:].transpose(),
                      w_plot[i_plan,:,:].transpose(), 
                      units = 'xy', scale = dz, headwidth = headwidth, 
                      headlength = headlength,
                      headaxislength = headaxislength)
        ax.quiverkey(Q, 0.9, 0.9, 1, r'$1 \frac{m}{s}$', labelpos='E',
                     coordinates='figure')
    
    buildZ = cells.xs(i_plan, level = 0)
    
    # Set building pixels in color
    ax.pcolor(  buildZ.index.unique(0)*meshSize,
                buildZ.index.unique(1)*dz-float(dz)/2,
                buildZ.unstack().transpose().values,
                shading = "nearest",
                alpha = 0.8)
    if len(yRange)==2:
        ax.set_xlim(yRange[0],yRange[1])
    if len(zRange)==2:
        ax.set_ylim(zRange[0],zRange[1])