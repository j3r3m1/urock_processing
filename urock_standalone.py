#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 19 16:25:11 2021

@author: Jérémy Bernard, University of Gothenburg
"""

import os

from . import MainCalculation
from .GlobalVariables import *
from .H2gisConnection import getJavaDir, setJavaDir, saveJavaDir


# A directory where will be saved the H2GIS database used for calculations
# and the file defining Java environment variables
model_directory = TEMPO_DIRECTORY

z_ref = 10
v_ref = 2
windDirection = 45
meshSize = 2
dz = 2

# Get building file directory (as string) and srid (as int)
build_file = INPUT_DIRECTORY + os.sep + "StreetCanyon" + os.sep + BUILDING_FILENAME
srid_build = 3857

# Get vegetation file directory (as string) - None if none...
veg_file = None

# Cannot be used right now (need GDAL because some specific methods are applied at the end)
outputRaster = None

idBuild = ID_FIELD_BUILD
heightBuild = HEIGHT_FIELD
idVeg = ID_VEGETATION
baseHeightVeg = VEGETATION_CROWN_BASE_HEIGHT
topHeightVeg = VEGETATION_CROWN_TOP_HEIGHT
attenuationVeg = VEGETATION_ATTENUATION_FACTOR
prefix = ""

# A list of output levels
z_out = [1,3,5,7,9,11,13,15,17,19,21]
outputDirectory = OUTPUT_DIRECTORY
outputFilename = "test_standalone"

# Note that the raster can not be used right now (need GDAL)
saveRaster = False
saveVector = True
saveNetcdf = True

#############################################################################
# ------------------- DEAL WITH JAVA ENVIRONMENT VARIABLE -------------------
#############################################################################
# Get the default value of the Java environment path if already exists or given by the user
javaDirDefault = getJavaDir(model_directory)

# Inform the user that the Java version should be 64 bits
if "Program Files (x86)" in javaDirDefault:
    print(""""Only a 32 bits version of Java has been found \
          on your computer. Please consider installing Java 64 bits.""")
else:
    # Set a Java dir if not exist and save it into a file in the plugin repository
    setJavaDir(javaDirDefault)
    saveJavaDir(javaPath = javaDirDefault,
                pluginDirectory = model_directory)


#############################################################################
# ------------------- MAKE THE CALCULATIONS ---------------------------------
#############################################################################
u, v, w, u0, v0, w0, x, y, z, buildingCoordinates, cursor, gridName,\
rotationCenterCoordinates, verticalWindProfile = \
    MainCalculation.main(javaEnvironmentPath = javaDirDefault,
                         pluginDirectory = model_directory,
                         outputFilePathAndNameBase = outputDirectory + os.sep + outputFilename,
                         buildingFilePath = build_file,
                         vegetationFilePath = veg_file,
                         srid = srid_build,
                         z_ref = z_ref,
                         v_ref = v_ref,
                         windDirection = windDirection,
                         prefix = prefix,
                         meshSize = meshSize,
                         dz = dz,
                         alongWindZoneExtend = ALONG_WIND_ZONE_EXTEND,
                         crossWindZoneExtend = CROSS_WIND_ZONE_EXTEND,
                         verticalExtend = VERTICAL_EXTEND,
                         cadTriangles = "",
                         cadTreesIntersection = "",
                         tempoDirectory = TEMPO_DIRECTORY,
                         onlyInitialization = ONLY_INITIALIZATION,
                         maxIterations = MAX_ITERATIONS,
                         thresholdIterations = THRESHOLD_ITERATIONS,
                         idFieldBuild = idBuild,
                         buildingHeightField = heightBuild,
                         vegetationBaseHeight = baseHeightVeg,
                         vegetationTopHeight = topHeightVeg,
                         idVegetation = idVeg,
                         vegetationAttenuationFactor = attenuationVeg,
                         saveRockleZones = SAVE_ROCKLE_ZONES,
                         outputRaster = outputRaster,
                         feedback = None,
                         saveRaster = saveRaster,
                         saveVector = saveVector,
                         saveNetcdf = saveNetcdf,
                         z_out = z_out)