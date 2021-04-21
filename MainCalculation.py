#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 21 11:39:39 2021

@author: Jérémy Bernard, University of Gothenburg
"""

from GlobalVariables import * 

import H2gisConnection
import CreatesGeometries
import CalculatesIndicators
import InitWindField
import DataUtil
import WindSolver
import time

import os

def main(z_ref = Z_REF,
         v_ref = V_REF,
         windDirection = WIND_DIRECTION,
         prefix = PREFIX_NAME,
         meshSize = MESH_SIZE,
         dz = DZ,
         alongWindZoneExtend = ALONG_WIND_ZONE_EXTEND,
         crossWindZoneExtend = CROSS_WIND_ZONE_EXTEND,
         verticalExtend = VERTICAL_EXTEND,
         tempoDirectory = TEMPO_DIRECTORY,
         inputBuildingFilename = INPUT_BUILDING_FILENAME,
         inputVegetationFilename = INPUT_VEGETATION_FILENAME):

    # Need to avoid vegetation related calculations if there is not vegetation file...
    vegetationBool = True
    if inputVegetationFilename=="":
        vegetationBool = False
    
    ################################ INIT VARIABLES ############################
    # Define dictionaries of input and output relative directories
    inputDataRel = {}
    outputDataRel = {}
    
    # Input geometries (buildings and vegetation)
    inputDataRel["buildings"] = os.path.join(INPUT_DIRECTORY, inputBuildingFilename)
    if vegetationBool:
        inputDataRel["vegetation"] = os.path.join(INPUT_DIRECTORY, inputVegetationFilename)

    # Stacked blocks
    outputDataRel["stacked_blocks"] = os.path.join(OUTPUT_DIRECTORY, "stackedBlocks.geojson")

    # Rotated geometries
    outputDataRel["rotated_stacked_blocks"] = os.path.join(OUTPUT_DIRECTORY, "rotated_stacked_blocks.geojson")
    outputDataRel["rotated_vegetation"] = os.path.join(OUTPUT_DIRECTORY, "vegetationRotated.geojson")
    outputDataRel["facades"] = os.path.join(OUTPUT_DIRECTORY, "facades.geojson")
    
    # Created zones
    outputDataRel["displacement"] = os.path.join(OUTPUT_DIRECTORY, "displacementZones.geojson")
    outputDataRel["displacement_vortex"] = os.path.join(OUTPUT_DIRECTORY, "displacementVortexZones.geojson")
    outputDataRel["cavity"] = os.path.join(OUTPUT_DIRECTORY, "cavity.geojson")
    outputDataRel["wake"] = os.path.join(OUTPUT_DIRECTORY, "wake.geojson")
    outputDataRel["street_canyon"] = os.path.join(OUTPUT_DIRECTORY, "streetCanyon.geojson")
    outputDataRel["rooftop_perpendicular"] = os.path.join(OUTPUT_DIRECTORY, "rooftopPerp.geojson")
    outputDataRel["rooftop_corner"] = os.path.join(OUTPUT_DIRECTORY, "rooftopCorner.geojson")
    outputDataRel["vegetation_built"] = os.path.join(OUTPUT_DIRECTORY, "vegetationBuilt.geojson")
    outputDataRel["vegetation_open"] = os.path.join(OUTPUT_DIRECTORY, "vegetationOpen.geojson")
    
    # Grid points
    outputDataRel["point_BuildZone"] = os.path.join(OUTPUT_DIRECTORY, "point_BuildZone")
    outputDataRel["point3D_BuildZone"] = os.path.join(OUTPUT_DIRECTORY, "point3D_BuildZone")
    outputDataRel["point_VegZone"] = os.path.join(OUTPUT_DIRECTORY, "point_VegZone")
    outputDataRel["point3D_VegZone"] = os.path.join(OUTPUT_DIRECTORY, "point3D_VegZone")
    outputDataRel["point3D_All"] = os.path.join(OUTPUT_DIRECTORY, "point3D_All")
    
    # Input table names
    tableBuildingTestName = "BUILDINGS"
    tableVegetationTestName = "VEGETATION"
    
    # Convert relative to absolute paths
    inputDataAbs = {i : os.path.abspath(inputDataRel[i]) for i in inputDataRel}
    outputDataAbs = {i : os.path.abspath(outputDataRel[i]) for i in outputDataRel}
    
    ############################################################################
    ################################ SCRIPT ####################################
    ############################################################################
    # ----------------------------------------------------------------------
    # 1. SET H2GIS DATABASE ENVIRONMENT AND LOAD DATA
    #Download H2GIS
    H2gisConnection.downloadH2gis(dbDirectory = tempoDirectory)
    #Initialize a H2GIS database connection
    cursor = H2gisConnection.startH2gisInstance(dbDirectory = tempoDirectory,
                                                dbInstanceDir = tempoDirectory)
    
    #Load buildings and vegetation into H2GIS
    importQuery = """DROP TABLE IF EXISTS {0}; CALL SHPREAD('{1}','{0}');
                    """.format( tableBuildingTestName,
                                inputDataAbs["buildings"])
    if vegetationBool:
        importQuery += """DROP TABLE IF EXISTS {0}; CALL SHPREAD('{1}','{0}')
                        """.format( tableVegetationTestName,
                                    inputDataAbs["vegetation"])
    else:
        importQuery += """ DROP TABLE IF EXISTS {0};
                           CREATE TABLE {0}(PK INTEGER, {1} GEOMETRY,
                                            {2} DOUBLE, {3} DOUBLE,
                                            {4} INTEGER, {5} DOUBLE)
                        """.format( tableVegetationTestName,
                                    GEOM_FIELD,
                                    VEGETATION_CROWN_BASE_HEIGHT,
                                    VEGETATION_CROWN_TOP_HEIGHT,
                                    ID_VEGETATION,
                                    VEGETATION_ATTENUATION_FACTOR)
    cursor.execute(importQuery)
    
    
    timeStartCalculation = time.time()
    
    # -----------------------------------------------------------------------------------
    # 2. CREATES OBSTACLE GEOMETRIES ----------------------------------------------------
    # -----------------------------------------------------------------------------------
    # Create the stacked blocks
    blockTable, stackedBlockTable = \
        CreatesGeometries.Obstacles.createsBlocks(cursor = cursor, 
                                                  inputBuildings = tableBuildingTestName,
                                                  prefix = prefix)
    
    # Save the stacked blocks as geojson
    if DEBUG:
        DataUtil.saveTable(cursor = cursor                      , tableName = stackedBlockTable,
                  filedir = outputDataAbs["stacked_blocks"]     , delete = True)
    
    # -----------------------------------------------------------------------------------
    # 3. ROTATES OBSTACLES TO THE RIGHT DIRECTION AND CALCULATES GEOMETRY PROPERTIES ----
    # -----------------------------------------------------------------------------------
    # Define a set of obstacles in a dictionary before the rotation
    dicOfObstacles = {tableBuildingTestName     : stackedBlockTable,
                      tableVegetationTestName   : tableVegetationTestName}
    
    # Rotate obstacles
    dicRotatedTables, rotationCenterCoordinates = \
        CreatesGeometries.Obstacles.windRotation(cursor = cursor,
                                                 dicOfInputTables = dicOfObstacles,
                                                 rotateAngle = windDirection,
                                                 rotationCenterCoordinates = None,
                                                 prefix = prefix)
    
    # Get the rotated block and vegetation table names
    rotatedStackedBlocks = dicRotatedTables[tableBuildingTestName]
    rotatedVegetation = dicRotatedTables[tableVegetationTestName]
    
    # Calculates base block height and base of block cavity zone
    rotatedPropStackedBlocks = \
        CreatesGeometries.Obstacles.identifyBlockAndCavityBase(cursor, rotatedStackedBlocks,
                                                               prefix = prefix)
        
    # Save the rotating tables as geojson
    if DEBUG:
        DataUtil.saveTable(cursor = cursor                          , tableName = rotatedPropStackedBlocks,
                  filedir = outputDataAbs["rotated_stacked_blocks"] , delete = True)
        DataUtil.saveTable(cursor = cursor                         , tableName = rotatedVegetation,
                  filedir = outputDataAbs["rotated_vegetation"]    , delete = True)
    
    # Init the upwind facades
    upwindInitedTable = \
        CreatesGeometries.Obstacles.initUpwindFacades(cursor = cursor,
                                                      obstaclesTable = rotatedPropStackedBlocks,
                                                      prefix = prefix)
    # Update base height of upwind facades (if shared with the building below)
    upwindTable = \
        CreatesGeometries.Obstacles.updateUpwindFacadeBase(cursor = cursor,
                                                           upwindTable = upwindInitedTable,
                                                           prefix = prefix)
    # Save the upwind facades as geojson
    if DEBUG:
        DataUtil.saveTable(cursor = cursor                      , tableName = upwindTable,
                           filedir = outputDataAbs["facades"]   , delete = True)
    
    # Calculates obstacles properties
    obstaclePropertiesTable = \
        CalculatesIndicators.obstacleProperties(cursor = cursor,
                                                obstaclesTable = rotatedPropStackedBlocks,
                                                prefix = prefix)
    
    # Calculates obstacle zone properties
    zonePropertiesTable = \
        CalculatesIndicators.zoneProperties(cursor = cursor,
                                            obstaclePropertiesTable = obstaclePropertiesTable,
                                            prefix = prefix)
    
    # Calculates roughness properties of the study area
    z0, d = \
        CalculatesIndicators.studyAreaProperties(cursor = cursor, 
                                                 upwindTable = upwindInitedTable, 
                                                 stackedBlockTable = rotatedStackedBlocks, 
                                                 vegetationTable = rotatedVegetation)
    
    
    # -----------------------------------------------------------------------------------
    # 4. CREATES THE 2D ROCKLE ZONES ----------------------------------------------------
    # -----------------------------------------------------------------------------------
    # Creates the displacement zone (upwind)
    displacementZonesTable, displacementVortexZonesTable = \
        CreatesGeometries.Zones.displacementZones(cursor = cursor,
                                                  upwindTable = upwindTable,
                                                  zonePropertiesTable = zonePropertiesTable,
                                                  prefix = prefix)
    
    
    # Save the resulting displacement zones as geojson
    if DEBUG:
        DataUtil.saveTable(cursor = cursor                      , tableName = displacementZonesTable,
                  filedir = outputDataAbs["displacement"]       , delete = True)
        DataUtil.saveTable(cursor = cursor                          , tableName = displacementVortexZonesTable,
                  filedir = outputDataAbs["displacement_vortex"]    , delete = True)
    
    # Creates the cavity and wake zones
    cavityZonesTable, wakeZonesTable = \
        CreatesGeometries.Zones.cavityAndWakeZones(cursor = cursor, 
                                                   zonePropertiesTable = zonePropertiesTable,
                                                   prefix = prefix)
    
    # Save the resulting displacement zones as geojson
    if DEBUG:
        DataUtil.saveTable(cursor = cursor             , tableName = cavityZonesTable,
                  filedir = outputDataAbs["cavity"]    , delete = True)
        DataUtil.saveTable(cursor = cursor           , tableName = wakeZonesTable,
                  filedir = outputDataAbs["wake"]    , delete = True)
    
    
    # Creates the street canyon zones
    streetCanyonTable = \
        CreatesGeometries.Zones.streetCanyonZones(cursor = cursor,
                                                  cavityZonesTable = cavityZonesTable,
                                                  zonePropertiesTable = zonePropertiesTable,
                                                  upwindTable = upwindTable,
                                                  prefix = prefix)
    
    # Save the resulting street canyon zones as geojson
    if DEBUG:
        DataUtil.saveTable(cursor = cursor                    , tableName = streetCanyonTable,
                  filedir = outputDataAbs["street_canyon"]    , delete = True)
    
    # Creates the rooftop zones
    rooftopPerpendicularZoneTable, rooftopCornerZoneTable = \
        CreatesGeometries.Zones.rooftopZones(cursor = cursor,
                                             upwindTable = upwindTable,
                                             zonePropertiesTable = zonePropertiesTable,
                                             prefix = prefix)
    # Save the resulting rooftop zones as geojson
    if DEBUG:
        DataUtil.saveTable(cursor = cursor                              , tableName = rooftopPerpendicularZoneTable,
                  filedir = outputDataAbs["rooftop_perpendicular"]      , delete = True)
        DataUtil.saveTable(cursor = cursor                      , tableName = rooftopCornerZoneTable,
                  filedir = outputDataAbs["rooftop_corner"]     , delete = True)
    
    # Creates the vegetation zones
    vegetationBuiltZoneTable, vegetationOpenZoneTable = \
        CreatesGeometries.Zones.vegetationZones(cursor = cursor,
                                                vegetationTable = rotatedVegetation,
                                                wakeZonesTable = wakeZonesTable,
                                                prefix = prefix)
    if DEBUG:
        DataUtil.saveTable(cursor = cursor                      , tableName = vegetationBuiltZoneTable,
                  filedir = outputDataAbs["vegetation_built"]   , delete = True)
        DataUtil.saveTable(cursor = cursor                      , tableName = vegetationOpenZoneTable,
                  filedir = outputDataAbs["vegetation_open"]    , delete = True)
    
    
    # -----------------------------------------------------------------------------------
    # 5. INITIALIZE THE 3D WIND FIELD IN THE ROCKLE ZONES -------------------------------
    # -----------------------------------------------------------------------------------
    # Define a dictionary of all building Rockle zones and same for veg
    dicOfBuildRockleZoneTable = {DISPLACEMENT_NAME       : displacementZonesTable,
                                DISPLACEMENT_VORTEX_NAME: displacementVortexZonesTable,
                                CAVITY_NAME             : cavityZonesTable,
                                WAKE_NAME               : wakeZonesTable,
                                STREET_CANYON_NAME      : streetCanyonTable,
                                ROOFTOP_PERP_NAME       : rooftopPerpendicularZoneTable,
                                ROOFTOP_CORN_NAME       : rooftopCornerZoneTable}
    dicOfVegRockleZoneTable = {VEGETATION_BUILT_NAME   : vegetationBuiltZoneTable,
                               VEGETATION_OPEN_NAME    : vegetationOpenZoneTable}

    # Creates the grid of points
    gridPoint = InitWindField.createGrid(cursor = cursor, 
                                         dicOfInputTables = dict(dicOfBuildRockleZoneTable,**dicOfVegRockleZoneTable),
                                         alongWindZoneExtend = alongWindZoneExtend, 
                                         crossWindZoneExtend = crossWindZoneExtend, 
                                         meshSize = meshSize,
                                         prefix = prefix)
    
    # Affects each point to a build Rockle zone and calculates needed variables for 3D wind speed factors
    dicOfBuildZoneGridPoint = \
        InitWindField.affectsPointToBuildZone(  cursor = cursor, 
                                                gridTable = gridPoint,
                                                dicOfBuildRockleZoneTable = dicOfBuildRockleZoneTable,
                                                prefix = prefix)
    if DEBUG:
        for t in dicOfBuildZoneGridPoint:
            cursor.execute("""DROP TABLE IF EXISTS point_Buildzone_{0};
                           CREATE INDEX IF NOT EXISTS id_{1}_{3} ON {3} USING BTREE({1});
                           CREATE INDEX IF NOT EXISTS id_{1}_{4} ON {4} USING BTREE({1});
                           CREATE TABLE point_Buildzone_{0}
                               AS SELECT   a.{2}, b.*
                               FROM {3} AS a RIGHT JOIN {4} AS b
                                           ON a.{1} = b.{1}
                               WHERE b.{1} IS NOT NULL
                               """.format(t, ID_POINT, GEOM_FIELD, gridPoint, dicOfBuildZoneGridPoint[t]))
            DataUtil.saveTable(cursor = cursor,
                               tableName = "point_Buildzone_"+t,
                               filedir = outputDataAbs["point_BuildZone"]+t+".geojson",
                               delete = True)
        
    # Same for vegetation Röckle zones
    dicOfVegZoneGridPoint = \
        InitWindField.affectsPointToVegZone(cursor = cursor, 
                                            gridTable = gridPoint,
                                            dicOfVegRockleZoneTable = dicOfVegRockleZoneTable,
                                            prefix = prefix)
    
    
        
    # Calculates the 3D wind speed factors for each building Röckle zone
    dicOfBuildZone3DWindFactor, maxHeight = \
        InitWindField.calculates3dBuildWindFactor(cursor = cursor,
                                                  dicOfBuildZoneGridPoint = dicOfBuildZoneGridPoint,
                                                  dz = dz,
                                                  prefix = prefix)
        
    # Calculates the height of the top of the "sketch"
    sketchHeight = maxHeight + verticalExtend
    if DEBUG:
        for t in dicOfBuildZone3DWindFactor:
            cursor.execute("""DROP TABLE IF EXISTS point3D_Buildzone_{0};
                           CREATE INDEX IF NOT EXISTS id_{1}_{3} ON {3} USING BTREE({1});
                           CREATE INDEX IF NOT EXISTS id_{1}_{4} ON {4} USING BTREE({1});
                           CREATE TABLE point3D_Buildzone_{0}
                               AS SELECT   a.{2}, b.*
                               FROM {3} AS a RIGHT JOIN {4} AS b
                                           ON a.{1} = b.{1}
                               WHERE b.{1} IS NOT NULL
                               """.format(t, ID_POINT, GEOM_FIELD, gridPoint, dicOfBuildZone3DWindFactor[t]))
            DataUtil.saveTable(cursor = cursor,
                               tableName = "point3D_Buildzone_"+t,
                               filedir = outputDataAbs["point3D_BuildZone"]+t+".geojson",
                               delete = True)
        
    # Calculates the 3D wind speed factors of the vegetation (considering all zone types)
    vegetationWeightFactorTable = \
        InitWindField.calculates3dVegWindFactor(cursor = cursor,
                                                dicOfVegZoneGridPoint = dicOfVegZoneGridPoint,
                                                sketchHeight = sketchHeight,
                                                z0 = z0,
                                                d = d,
                                                dz = dz,
                                                prefix = prefix)
    if DEBUG:
        cursor.execute("""DROP TABLE IF EXISTS point3D_AllVegZone;
                       CREATE INDEX IF NOT EXISTS id_{0}_{2} ON {2} USING BTREE({0});
                       CREATE INDEX IF NOT EXISTS id_{0}_{3} ON {3} USING BTREE({0});
                       CREATE TABLE point3D_AllVegZone
                           AS SELECT   a.{1}, b.*
                           FROM {2} AS a RIGHT JOIN {3} AS b
                                       ON a.{0} = b.{0}
                           WHERE b.{0} IS NOT NULL
                           """.format(ID_POINT, GEOM_FIELD, gridPoint, vegetationWeightFactorTable))
        DataUtil.saveTable(cursor = cursor,
                           tableName = "point3D_AllVegZone",
                           filedir = outputDataAbs["point3D_VegZone"]+".geojson",
                           delete = True)
    
    
    # ----------------------------------------------------------------
    # 5. DEALS WITH SUPERIMPOSED ZONES -------------------------------
    # ----------------------------------------------------------------
    # Calculates the final weighting factor for each point, dealing with duplicates (superimposition)
    dicAllWeightFactorsTables = dicOfBuildZone3DWindFactor.copy()
    dicAllWeightFactorsTables[ALL_VEGETATION_NAME] = vegetationWeightFactorTable
    allZonesPointFactor = \
        InitWindField.manageSuperimposition(cursor = cursor,
                                            dicAllWeightFactorsTables = dicAllWeightFactorsTables,
                                            upstreamPriorityTables = UPSTREAM_PRIORITY_TABLES,
                                            upstreamWeightingTables = UPSTREAM_WEIGHTING_TABLES,
                                            upstreamWeightingInterRules = UPSTREAM_WEIGHTING_INTER_RULES,
                                            upstreamWeightingIntraRules = UPSTREAM_WEIGHTING_INTRA_RULES,
                                            downstreamWeightingTable = DOWNSTREAM_WEIGTHING_TABLE,
                                            prefix = prefix)
    if DEBUG:
        cursor.execute("""DROP TABLE IF EXISTS point3D_All;
                       CREATE INDEX IF NOT EXISTS id_{0}_{2} ON {2} USING BTREE({0});
                       CREATE INDEX IF NOT EXISTS id_{0}_{3} ON {3} USING BTREE({0});
                       CREATE TABLE point3D_All
                           AS SELECT   a.{1}, b.*
                           FROM {2} AS a RIGHT JOIN {3} AS b
                                       ON a.{0} = b.{0}
                           WHERE b.{0} IS NOT NULL
                           """.format(ID_POINT, GEOM_FIELD, gridPoint, allZonesPointFactor))
        DataUtil.saveTable(cursor = cursor,
                           tableName = "point3D_All",
                           filedir = outputDataAbs["point3D_All"]+".geojson",
                           delete = True)        
    
    
    # ----------------------------------------------------------------
    # 6. 3D WIND SPEED CALCULATION -----------------------------------
    # ----------------------------------------------------------------
    # Identify 3D grid points intersected by buildings
    df_gridBuil = \
        InitWindField.identifyBuildPoints(cursor = cursor,
                                          gridPoint = gridPoint,
                                          stackedBlocksWithBaseHeight = rotatedPropStackedBlocks,
                                          dz = dz,
                                          tempoDirectory = tempoDirectory)
    
    # Set the initial 3D wind speed field
    df_wind0, nPoints = \
        InitWindField.setInitialWindField(cursor = cursor, 
                                          initializedWindFactorTable = allZonesPointFactor,
                                          gridPoint = gridPoint,
                                          df_gridBuil = df_gridBuil,
                                          z0 = z0,
                                          sketchHeight = sketchHeight,
                                          meshSize = meshSize,
                                          dz = dz, 
                                          z_ref = z_ref,
                                          V_ref = v_ref, 
                                          tempoDirectory = tempoDirectory)
    
    # Set the ground as "building" (understand solid wall) - after getting grid size
    nx, ny, nz = nPoints.values()
    df_gridBuil = df_gridBuil.reindex(df_gridBuil.index.append(pd.MultiIndex.from_product([range(1,nx-1),
                                                                                          range(1,ny-1),
                                                                                          [0]])))

    # Set the buildGrid3D object to zero when a cell intersect a building 
    buildGrid3D = pd.Series(1, index = df_wind0.index, dtype = np.int32)
    buildGrid3D.loc[df_gridBuil.index] = 0
    
    # Convert to numpy matrix...
    buildGrid3D = np.array([buildGrid3D.xs(i, level = 0).unstack().values for i in range(0,nx)])
    # Identify grid cells having lambda not need to be updated in the calculations 
    # (values at open boundaries, near ground or inside buildings...)
    indices = np.transpose(np.where(buildGrid3D == 1))
    indices = indices[indices[:, 0] > 0]
    indices = indices[indices[:, 1] > 0]
    indices = indices[indices[:, 2] > 0]
    indices = indices[indices[:, 0] < nx - 1]
    indices = indices[indices[:, 1] < ny - 1]
    indices = indices[indices[:, 2] < nz - 1]
    indices = indices.astype(np.int32)
    buildIndexB = np.stack(np.where(buildGrid3D==0)).astype(np.int32)
    # Note that v axis direction is changed since we first use Röckle schemes
    # considering wind speed coming from North thus axis facing South
    un = np.array([df_wind0[U].xs(i, level = 0).unstack().values for i in range(0,nx)])
    vn = -np.array([df_wind0[V].xs(i, level = 0).unstack().values for i in range(0,nx)])
    wn = np.array([df_wind0[W].xs(i, level = 0).unstack().values for i in range(0,nx)])
    
    # Interpolation is made in order to have wind speed located on the face of
    # each grid cell
    un[1:nx, :, :] =   (un[0:nx-1, :, :] + un[1:nx, :, :])/2
    vn[:, 1:ny, :] =   (vn[:, 0:ny-1, :] + vn[:,1:ny,:])/2
    wn[:, :, 1:nz] =   (wn[:, :, 0:nz-1] + wn[:, :, 1:nz])/2
    # Reset input and output wind speed to zero for building cells
    indicesBuild = np.transpose(np.where(buildGrid3D == 0))
    for i,j,k in indicesBuild:
        un[i,j,k] = 0
        un[i+1,j,k]=0
        vn[i,j,k] = 0
        vn[i,j+1,k]=0
        wn[i,j,k] = 0
        wn[i,j,k+1]=0
    
    u = np.zeros((nx, ny, nz))
    v = np.zeros((nx, ny, nz))
    w = np.zeros((nx, ny, nz))
    
    print("Time spent for wind speed initialization: {0} s".format(time.time()-timeStartCalculation))
    
    # Apply a mass-flow balance to have a more physical 3D wind speed field
    return WindSolver.solver(   dx = meshSize               , dy = meshSize         , dz = dz, 
                                nx = nx                     , ny = ny               , nz = nz, 
                                un = un                     , vn = vn               , wn = wn,
                                u = u                       , v = v                 , w = w, 
                                buildIndexB = buildIndexB   , indices = indices     , indicesBuild = indicesBuild,
                                iterations = 15)