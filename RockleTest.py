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

import os



################################ INIT VARIABLES ############################
# Where will be stored the database management base system
tempoDirectory = TEMPO_DIRECTORY
tempoDirectory = "/home/decide/Téléchargements"

# Define dictionaries of input and output relative directories
inputDataRel = {}
outputDataRel = {}
# Input geometries (buildings and vegetation)

inputDataRel["buildings"] = "./Ressources/buildingSelection.shp"
inputDataRel["vegetation"] = "./Ressources/vegetation.shp"

# Rotated geometries
outputDataRel["stacked_blocks"] = "./Ressources/stackedBlocks.geojson"
outputDataRel["rotated_vegetation"] = "./Ressources/vegetationRotated.geojson"
outputDataRel["facades"] = "./Ressources/facades.geojson"

# Created zones
outputDataRel["displacement"] = "./Ressources/displacementZones.geojson"
outputDataRel["displacement_vortex"] = "./Ressources/displacementVortexZones.geojson"
outputDataRel["cavity"] = "./Ressources/cavity.geojson"
outputDataRel["wake"] = "./Ressources/wake.geojson"
outputDataRel["street_canyon"] = "./Ressources/streetCanyon.geojson"
outputDataRel["rooftop_perpendicular"] = "./Ressources/rooftopPerp.geojson"
outputDataRel["rooftop_corner"] = "./Ressources/rooftopCorner.geojson"
outputDataRel["vegetation_built"] = "./Ressources/vegetationBuilt.geojson"
outputDataRel["vegetation_open"] = "./Ressources/vegetationOpen.geojson"

# Grid points
outputDataRel["point_BuildZone"] = "./Ressources/point_BuildZone"
outputDataRel["point3D_BuildZone"] = "./Ressources/point3D_BuildZone"
outputDataRel["point_VegZone"] = "./Ressources/point_VegZone"
outputDataRel["point3D_VegZone"] = "./Ressources/point3D_VegZone"

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
                                            dbInstanceDir = tempoDirectory,
                                            instanceName = "myDbH2")

#Load buildings and vegetation into H2GIS
cursor.execute("""DROP TABLE IF EXISTS {0}, {2}; CALL SHPREAD('{1}','{0}');
                   CALL SHPREAD('{3}','{2}')""".format(tableBuildingTestName,
                                                           inputDataAbs["buildings"],
                                                           tableVegetationTestName,
                                                           inputDataAbs["vegetation"]))



# -----------------------------------------------------------------------------------
# 2. CREATES OBSTACLE GEOMETRIES AND CALCULATES THE MAXIMUM SKETCH HEIGHT------------
# -----------------------------------------------------------------------------------
# Create the stacked blocks
blockTable, stackedBlockTable = \
    CreatesGeometries.Obstacles.createsBlocks(cursor = cursor, 
                                              inputBuildings = tableBuildingTestName)

# Calculates the height of the top of the "sketch"
obstacleMaxHeight = CalculatesIndicators.maxObstacleHeight(cursor = cursor, 
                                                           stackedBlockTable = stackedBlockTable,
                                                           vegetationTable = tableVegetationTestName)
sketchHeight = obstacleMaxHeight + VERTICAL_EXTEND

# -----------------------------------------------------------------------------------
# 3. ROTATES OBSTACLES TO THE RIGHT DIRECTION AND CALCULATES GEOMETRY PROPERTIES ----
# -----------------------------------------------------------------------------------
# Define a set of obstacles in a dictionary before the rotation
dicOfObstacles = {tableBuildingTestName     : stackedBlockTable,
                  tableVegetationTestName   : tableVegetationTestName}

# Rotate obstacles
windDirection = 270
dicRotatedTables, rotationCenterCoordinates = \
    CreatesGeometries.Obstacles.windRotation(cursor = cursor,
                                             dicOfInputTables = dicOfObstacles,
                                             rotateAngle = windDirection,
                                             rotationCenterCoordinates = None)

# Get the rotated block and vegetation table names
rotatedStackedBlocks = dicRotatedTables[tableBuildingTestName]
rotatedVegetation = dicRotatedTables[tableVegetationTestName]

# Calculates base block height and base of block cavity zone
rotatedPropStackedBlocks = \
    CreatesGeometries.Obstacles.identifyBlockAndCavityBase(cursor, rotatedStackedBlocks)
    
# Save the rotating tables as geojson
DataUtil.saveTable(cursor = cursor                      , tableName = rotatedPropStackedBlocks,
          filedir = outputDataAbs["stacked_blocks"]     , delete = True)
DataUtil.saveTable(cursor = cursor                         , tableName = rotatedVegetation,
          filedir = outputDataAbs["rotated_vegetation"]    , delete = True)

# Init the upwind facades
upwindInitedTable = \
    CreatesGeometries.Obstacles.initUpwindFacades(cursor = cursor,
                                                  obstaclesTable = rotatedPropStackedBlocks)
# Update base height of upwind facades (if shared with the building below)
upwindTable = \
    CreatesGeometries.Obstacles.updateUpwindFacadeBase(cursor = cursor,
                                                       upwindTable = upwindInitedTable)
# Save the upwind facades as geojson
DataUtil.saveTable(cursor = cursor                      , tableName = upwindTable,
                   filedir = outputDataAbs["facades"]   , delete = True)


# Calculates obstacles properties
obstaclePropertiesTable = \
    CalculatesIndicators.obstacleProperties(cursor = cursor,
                                            obstaclesTable = rotatedPropStackedBlocks)

# Calculates obstacle zone properties
zonePropertiesTable = \
    CalculatesIndicators.zoneProperties(cursor = cursor,
                                        obstaclePropertiesTable = obstaclePropertiesTable)

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
                                              zonePropertiesTable = zonePropertiesTable)


# Save the resulting displacement zones as geojson
DataUtil.saveTable(cursor = cursor                      , tableName = displacementZonesTable,
          filedir = outputDataAbs["displacement"]       , delete = True)
DataUtil.saveTable(cursor = cursor                          , tableName = displacementVortexZonesTable,
          filedir = outputDataAbs["displacement_vortex"]    , delete = True)

# Creates the cavity and wake zones
cavityZonesTable, wakeZonesTable = \
    CreatesGeometries.Zones.cavityAndWakeZones(cursor = cursor, 
                                               zonePropertiesTable = zonePropertiesTable)

# Save the resulting displacement zones as geojson
DataUtil.saveTable(cursor = cursor             , tableName = cavityZonesTable,
          filedir = outputDataAbs["cavity"]    , delete = True)
DataUtil.saveTable(cursor = cursor           , tableName = wakeZonesTable,
          filedir = outputDataAbs["wake"]    , delete = True)


# Creates the street canyon zones
streetCanyonTable = \
    CreatesGeometries.Zones.streetCanyonZones(cursor = cursor,
                                              cavityZonesTable = cavityZonesTable,
                                              zonePropertiesTable = zonePropertiesTable,
                                              upwindTable = upwindTable)

# Save the resulting street canyon zones as geojson
DataUtil.saveTable(cursor = cursor                    , tableName = streetCanyonTable,
          filedir = outputDataAbs["street_canyon"]    , delete = True)

# Creates the rooftop zones
rooftopPerpendicularZoneTable, rooftopCornerZoneTable = \
    CreatesGeometries.Zones.rooftopZones(cursor = cursor,
                                         upwindTable = upwindTable,
                                         zonePropertiesTable = zonePropertiesTable)
# Save the resulting rooftop zones as geojson
DataUtil.saveTable(cursor = cursor                              , tableName = rooftopPerpendicularZoneTable,
          filedir = outputDataAbs["rooftop_perpendicular"]      , delete = True)
DataUtil.saveTable(cursor = cursor                      , tableName = rooftopCornerZoneTable,
          filedir = outputDataAbs["rooftop_corner"]     , delete = True)

# Creates the vegetation zones
vegetationBuiltZoneTable, vegetationOpenZoneTable = \
    CreatesGeometries.Zones.vegetationZones(cursor = cursor,
                                            vegetationTable = rotatedVegetation,
                                            wakeZonesTable = wakeZonesTable)
DataUtil.saveTable(cursor = cursor                      , tableName = vegetationBuiltZoneTable,
          filedir = outputDataAbs["vegetation_built"]   , delete = True)
DataUtil.saveTable(cursor = cursor                      , tableName = vegetationOpenZoneTable,
          filedir = outputDataAbs["vegetation_open"]    , delete = True)


# -----------------------------------------------------------------------------------
# 5. INITIALIZE THE 3D WIND FIELD IN THE ROCKLE ZONES -------------------------------
# -----------------------------------------------------------------------------------
# Creates the grid of points
gridPoint = InitWindField.createGrid(cursor = cursor, 
                                     dicOfInputTables = dicRotatedTables)

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

# Affects each point to a Rockle zone and calculates needed variables for 3D wind speed factors
dicOfBuildZoneGridPoint = \
    InitWindField.affectsPointToBuildZone(  cursor = cursor, 
                                            gridTable = gridPoint,
                                            dicOfBuildRockleZoneTable = dicOfBuildRockleZoneTable)
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
                                        dicOfVegRockleZoneTable = dicOfVegRockleZoneTable)


    
# Calculates the 3D wind speed factors for each building Röckle zone
dicOfBuildZone3DWindFactor = \
    InitWindField.calculates3dBuildWindFactor(cursor = cursor,
                                              dicOfBuildZoneGridPoint = dicOfBuildZoneGridPoint,
                                              maxHeight = obstacleMaxHeight)
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
                                            d = d)

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
                                        downstreamWeightingTable = DOWNSTREAM_WEIGTHING_TABLE)

# ----------------------------------------------------------------
# 6. 3D WIND SPEED CALCULATION -----------------------------------
# ----------------------------------------------------------------
# Identify 3D grid points intersected by buildings
df_gridBuil = \
    InitWindField.identifyBuildPoints(cursor = cursor,
                                      gridPoint = gridPoint,
                                      stackedBlocksWithBaseHeight = rotatedPropStackedBlocks,
                                      dz = DZ,
                                      tempoDirectory = tempoDirectory)

# Set the initial 3D wind speed field
df_wind0, nPoints = \
    InitWindField.setInitialWindField(cursor = cursor, 
                                      initializedWindFactorTable = allZonesPointFactor,
                                      gridPoint = gridPoint,
                                      df_gridBuil = df_gridBuil,
                                      z0 = z0,
                                      sketchHeight = sketchHeight,
                                      meshSize = MESH_SIZE,
                                      dz = DZ, 
                                      z_ref = Z_REF,
                                      V_ref = V_REF, 
                                      tempoDirectory = tempoDirectory)

# Apply a mass-flow balance to have a more physical 3D wind speed field
buildGrid3D = pd.Series(1, index = df_wind0.index, dtype = np.int32)
buildGrid3D.loc[df_gridBuil.index] = 0
nx, ny, nz = nPoints.values()

# Convert to numpy matrix...
buildGrid3D = np.array([buildGrid3D.xs(i, level = 1).unstack().values for i in range(0,nx-1)])
indices = np.transpose(np.where(buildGrid3D == 1))
indices = indices[indices[:, 0] > 0]
indices = indices[indices[:, 1] > 0]
indices = indices[indices[:, 2] > 0]
indices = indices[indices[:, 0] < nx - 1]
indices = indices[indices[:, 1] < ny - 1]
indices = indices[indices[:, 2] < nz - 1]
indices = indices.astype(np.int32)
buildIndexB = np.stack(np.where(buildGrid3D==0)).astype(np.int32)
un = np.array([df_wind0[U].xs(i, level = 0).unstack().values for i in range(0,nx)])
vn = np.array([df_wind0[V].xs(i, level = 0).unstack().values for i in range(0,nx)])
wn = np.array([df_wind0[W].xs(i, level = 0).unstack().values for i in range(0,nx)])

u = np.zeros((nx, ny, nz))
v = np.zeros((nx, ny, nz))
w = np.zeros((nx, ny, nz))

u, v, w, x, y, z, e, lambdaM1  = \
    WindSolver.solver(  dx = MESH_SIZE              , dy = MESH_SIZE        , dz = DZ, 
                        nx = nx                     , ny = ny               , nz = nz, 
                        un = un                     , vn = vn               , wn = wn,
                        u = u                       , v = v                 , w = w, 
                        buildIndexB = buildIndexB   , indices = indices     , iterations = 15)

