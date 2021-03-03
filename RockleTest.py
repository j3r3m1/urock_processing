#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 21 11:39:39 2021

@author: Jérémy Bernard, University of Gothenburg
"""

import H2gisConnection
import CreatesGeometries
import CalculatesIndicators
import InitWindField
import DataUtil

import os
import tempfile

from GlobalVariables import * 



################################ INIT VARIABLES ############################
# Where will be stored the database management base system
dbDir = tempfile.gettempdir()

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
H2gisConnection.downloadH2gis(dbDirectory = dbDir)
#Initialize a H2GIS database connection
cursor = H2gisConnection.startH2gisInstance(dbDirectory = dbDir,
                                            dbInstanceDir = dbDir,
                                            instanceName = "myDbH2")

#Load buildings and vegetation into H2GIS
cursor.execute("""DROP TABLE IF EXISTS {0}, {2}; CALL SHPREAD('{1}','{0}');
                   CALL SHPREAD('{3}','{2}')""".format(tableBuildingTestName,
                                                           inputDataAbs["buildings"],
                                                           tableVegetationTestName,
                                                           inputDataAbs["vegetation"]))



# -----------------------------------------------------------------------------------
# 2. CREATES OBSTACLE GEOMETRIES ----------------------------------------------------
# -----------------------------------------------------------------------------------
# Create the stacked blocks
blockTable, stackedBlockTable = \
    CreatesGeometries.Obstacles.createsBlocks(cursor = cursor, 
                                              inputBuildings = tableBuildingTestName)



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
upwindTable = \
    CreatesGeometries.Obstacles.initUpwindFacades(cursor = cursor,
                                                  obstaclesTable = rotatedPropStackedBlocks)
# Save the upwind facades as geojson
DataUtil.saveTable(cursor = cursor              , tableName = upwindTable,
          filedir = outputDataAbs["facades"]    , delete = True)


# Calculates obstacles properties
obstaclePropertiesTable = \
    CalculatesIndicators.obstacleProperties(cursor = cursor,
                                            obstaclesTable = rotatedPropStackedBlocks)

# Calculates obstacle zone properties
zonePropertiesTable = \
    CalculatesIndicators.zoneProperties(cursor = cursor,
                                        obstaclePropertiesTable = obstaclePropertiesTable)





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

# Creates the displacement zone (upwind)
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



# -----------------------------------------------------------------------------------
# 5. INITIALIZE THE 3D WIND FIELD IN THE ROCKLE ZONES -------------------------------
# -----------------------------------------------------------------------------------
# Creates the grid of points
gridPoint = InitWindField.createGrid(cursor = cursor, 
                                     dicOfInputTables = dicRotatedTables)

# Define a dictionary of all Rockle zones
dicOfRockleZoneTable = {DISPLACEMENT_NAME       : displacementZonesTable,
                        DISPLACEMENT_VORTEX_NAME: displacementVortexZonesTable,
                        CAVITY_NAME             : cavityZonesTable,
                        WAKE_NAME               : wakeZonesTable,
                        STREET_CANYON_NAME      : streetCanyonTable,
                        ROOFTOP_PERP_NAME       : rooftopPerpendicularZoneTable,
                        ROOFTOP_CORN_NAME       : rooftopCornerZoneTable}
# Affects each point to a Rockle zone and calculates relative distances
dicOfOutputTables = \
    InitWindField.affectsPointToZone(cursor = cursor, 
                                     gridTable = gridPoint,
                                     dicOfRockleZoneTable = dicOfRockleZoneTable)