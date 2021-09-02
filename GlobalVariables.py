#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 25 16:26:24 2021

@author: Jérémy Bernard, University of Gothenburg
"""
from datetime import datetime
import pandas as pd
import numpy as np
import tempfile
import math
import os

# Wind input measurement height
Z_REF = 10
V_REF = 2.0
WIND_DIRECTION = 270

# If the solver should go descending order along y (does not work yet...)
DESCENDING_Y = False

# Temporary directory where are saved database and specific files exchanged between
# the H2Database and Python
TEMPO_DIRECTORY = tempfile.gettempdir()
INPUT_DIRECTORY = os.path.join("./Ressources","Inputs")
OUTPUT_DIRECTORY = os.path.join("./Ressources","Outputs")
INPUT_GEOMETRIES_FILENAME = {  "buildingFileName" : "buildings.shp",
                               "vegetationFileName" : "vegetation.shp",
                               "cadTriangles" : "",
                               "cadTreesIntersection" : ""}
BUILDING_TABLE_NAME = "BUILDINGS"
VEGETATION_TABLE_NAME = "VEGETATION"
CAD_TRIANGLE_NAME = "CAD_TRIANGLES"
CAD_VEG_INTERSECTION = "CAD_VEG_INTERSECTION"

# Informations to set the DB used for geographical calculations
INSTANCE_NAME = "myDbH2"
INSTANCE_ID ="sa"
INSTANCE_PASS = "sa"
NEW_DB = True

# Where to save the current JAVA path
JAVA_PATH_FILE = os.path.join("./","JavaPath.csv")

# If debug is True, keep intermediate tables (within each process) and save
# intermediate tables (such as Röckle zones) as GIS file
DEBUG = True
ONLY_INITIALIZATION = False
SAVE_ROCKLE_ZONES = True
MAX_ITERATIONS = 10000      # Based on Pardyjak et Brown  (2003)
THRESHOLD_ITERATIONS = 1e-6 # Based on Pardyjak et Brown  (2003)

# Note that the number of points of an ellipse is only used to identify whether
# the upper or lower part of an ellipse should be used (fro displacement zones),
# the number of points used to create an ellipse can not be chosen yet
# Need to create this variable in H2GIS 
# https://github.com/locationtech/jts/blob/9d4097312d68cb8f9ae591bec69ce3b403e41e98/modules/core/src/main/java/org/locationtech/jts/util/GeometricShapeFactory.java#L101
NPOINTS_ELLIPSE = 100
MESH_SIZE = 2
DZ = 2
ALONG_WIND_ZONE_EXTEND = 30
CROSS_WIND_ZONE_EXTEND = 25
VERTICAL_EXTEND = 20

# The "perpendicular vortex scheme" for rooftop and displacement zones is activated
# if the wind angle if more or less 'PERPENDICULAR_THRESHOLD_ANGLE' ° higher
# or lower than 90° (20° is given in Bagal et al. - 2004 and 15° in Pol et al. - 2006)
PERPENDICULAR_THRESHOLD_ANGLE = 15
# "Corner wind" rooftop recirculation is activated when a facade is 30 to 70° to
# the perpendicular to the wind direction (Bagal et al., 2004)
CORNER_THRESHOLD_ANGLE_MIN = 30
CORNER_THRESHOLD_ANGLE_MAX = 70
CORNER_THRESHOLD_ANGLE = [CORNER_THRESHOLD_ANGLE_MIN, CORNER_THRESHOLD_ANGLE_MAX]
ELLIPSOID_MIN_LENGTH = float(MESH_SIZE)/4
GEOMETRY_MERGE_TOLERANCE = 0.05
SNAPPING_TOLERANCE = 0.3
GEOMETRY_SIMPLIFICATION_DISTANCE = 0.25

GEOM_FIELD = "THE_GEOM"
ID_FIELD_BUILD = "ID_BUILD"
ID_FIELD_BLOCK = "ID_BLOCK"
ID_FIELD_STACKED_BLOCK = "ID_STACKED_BLOCK"
ID_UPSTREAM_STACKED_BLOCK = "ID_UPSTREAM_STACKED_BLOCK"
ID_DOWNSTREAM_STACKED_BLOCK = "ID_DOWNSTREAM_STACKED_BLOCK"
ID_FIELD_CANYON = "ID_CANYON"
ID_VEGETATION = "ID_VEG"
ID_ZONE_VEGETATION = "ID_ZONE_VEG"
ID_POINT = "ID_POINT"
ID_POINT_X = "ID_X"
ID_POINT_Y = "ID_Y"
ID_POINT_Z = "ID_Z"

HEIGHT_FIELD = "HEIGHT_ROO"
BASE_HEIGHT_FIELD = "BASE_HEIGHT"
CAVITY_BASE_HEIGHT_FIELD = "CAVITY_BASE_HEIGHT"
VEGETATION_CROWN_BASE_HEIGHT = "MIN_HEIGHT"
VEGETATION_CROWN_TOP_HEIGHT = "MAX_HEIGHT"
TOP_CANOPY_HEIGHT_POINT = "MAX_CANOPY_HEIGHT"
VEGETATION_ATTENUATION_FACTOR = "ATTENUATIO"
UPSTREAM_HEIGHT_FIELD = "UPSTREAM_HEIGHT"
DOWNSTREAM_HEIGHT_FIELD = "DOWNSTREAM_HEIGHT"
MAX_CANYON_HEIGHT_FIELD = "Hc"
UPWIND_FACADE_ANGLE_FIELD = "THETA_WIND"
UPWIND_FACADE_FIELD = "UPWIND_FACADE_ID"
EFFECTIVE_LENGTH_FIELD = "L_EFF"
EFFECTIVE_WIDTH_FIELD = "W_EFF"
DISPLACEMENT_LENGTH_FIELD = "Lf"
DISPLACEMENT_LENGTH_VORTEX_FIELD = "Lfv"
CAVITY_LENGTH_FIELD = "Lr"
WAKE_LENGTH_FIELD = "Lw"
ROOFTOP_PERP_LENGTH = "Lcp"
ROOFTOP_CORNER_FACADE_LENGTH = "Lfc"
ROOFTOP_CORNER_LENGTH = "Lcc"
ROOFTOP_PERP_HEIGHT = "Hcm"
ROOFTOP_WIND_FACTOR = "C1"
ROOFTOP_PERP_VAR_HEIGHT = "Hr"
ROOFTOP_CORNER_VAR_HEIGHT = "Hccp"

PREFIX_NAME = "BigArea"
Y_WALL = "Y_WALL"
DISTANCE_BUILD_TO_POINT_FIELD = "DY"
LENGTH_ZONE_FIELD = "D_0"
POINT_RELATIVE_POSITION_FIELD = "DY_D0"
WAKE_RELATIVE_POSITION_FIELD = "D0W_DY_15"

DISPLACEMENT_NAME = "DISPLACEMENT"
DISPLACEMENT_VORTEX_NAME = "DISPLACEMENT_VORTEX"
CAVITY_NAME = "CAVITY"
WAKE_NAME = "WAKE"
STREET_CANYON_NAME = "STREET_CANYON"
ROOFTOP_PERP_NAME = "ROOFTOP_PERPENDICULAR"
ROOFTOP_CORN_NAME = "ROOFTOP_CORNER"
VEGETATION_BUILT_NAME = "VEGETATION_BUILT"
VEGETATION_OPEN_NAME = "VEGETATION_OPEN"
ALL_VEGETATION_NAME = "VEGETATION_ALL"

UPPER_VERTICAL_THRESHOLD = "Z_UP_THRESH"
LOWER_VERTICAL_THRESHOLD = "Z_DOWN_THRESH"
U = "U"
V = "V"
W = "W"
VEGETATION_FACTOR = "VEGETATION_FACTOR"

X = "X"
Y = "Y"
Z = "Z"
# Coefficients for displacement zone calculation
C_DZ = 0.4
P_DZ = 0.16
# Coefficient for rooftop perpendicular
P_RTP = 0.16
# Default vegetation attenuation factor
DEFAULT_VEG_ATTEN_FACT = 2.8

# Defines priorities (column "priority") when the zone comes from a same 
# obstacle of same height. Also contains a column "ref_height" to
# know by which wind speed height should be multiplied a weigthing factor
# (1: "Associated building height", 
#  2: "Reference wind speed measurement height Z_REF",
#  3: "Point height")
REF_HEIGHT_FIELD = "REF_HEIGHT"
PRIORITY_FIELD = "PRIORITY"
REF_HEIGHT_UPSTREAM_WEIGHTING = 3
REF_HEIGHT_DOWNSTREAM_WEIGHTING = 3
UPSTREAM_PRIORITY_TABLES = pd.DataFrame({PRIORITY_FIELD: [1, 2, 3, 3, 3, 4, 5], 
                                         REF_HEIGHT_FIELD: [1, 1, 2, 2, 1, 1, 3]},
                                        index = [STREET_CANYON_NAME, 
                                                 CAVITY_NAME, 
                                                 ROOFTOP_PERP_NAME,
                                                 ROOFTOP_CORN_NAME, 
                                                 DISPLACEMENT_VORTEX_NAME, 
                                                 DISPLACEMENT_NAME,
                                                 WAKE_NAME])
UPSTREAM_WEIGHTING_TABLES = [WAKE_NAME]
UPSTREAM_WEIGHTING_INTRA_RULES = "upstream"
UPSTREAM_WEIGHTING_INTER_RULES = "upstream"
DOWNSTREAM_WEIGTHING_TABLE = ALL_VEGETATION_NAME

ID_3D_POINT = "ID"