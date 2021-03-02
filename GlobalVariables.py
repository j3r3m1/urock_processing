#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 25 16:26:24 2021

@author: Jérémy Bernard, University of Gothenburg
"""
from datetime import datetime

# Note that the number of points of an ellipse is only used to identify whether
# the upper or lower part of an ellipse should be used (fro displacement zones),
# the number of points used to create an ellipse can not be chosen yet
# Need to create this variable in H2GIS 
# https://github.com/locationtech/jts/blob/9d4097312d68cb8f9ae591bec69ce3b403e41e98/modules/core/src/main/java/org/locationtech/jts/util/GeometricShapeFactory.java#L101
NPOINTS_ELLIPSE = 100
MESH_SIZE = 3
ALONG_WIND_ZONE_EXTEND = 75
CROSS_WIND_ZONE_EXTEND = 20

# The "perpendicular vortex scheme" for rooftop and displacement zones is activated
# if the wind angle if more or less 'PERPENDICULAR_THRESHOLD_ANGLE' ° higher
# or lower than 90° (20° is given in Bagal et al. - 2004 and 15° in Pol et al. - 2006)
PERPENDICULAR_THRESHOLD_ANGLE = 15
# "Corner wind" rooftop recirculation is activated when a facade is 30 to 70° to
# the perpendicular to the wind direction (Bagal et al., 2004)
CORNER_THRESHOLD_ANGLE = [30, 70]
ELLIPSOID_MIN_LENGTH = float(MESH_SIZE)/4
GEOMETRY_MERGE_TOLERANCE = 0.25
SNAPPING_TOLERANCE = 0.001
GEOMETRY_SIMPLIFICATION_DISTANCE = 0.25

GEOM_FIELD = "THE_GEOM"
ID_FIELD_BUILD = "ID_BUILD"
ID_FIELD_BLOCK = "ID_BLOCK"
ID_FIELD_STACKED_BLOCK = "ID_STACKED_BLOCK"
ID_UPSTREAM_STACKED_BLOCK = "ID_UPSTREAM_STACKED_BLOCK"
ID_DOWNSTREAM_STACKED_BLOCK = "ID_DOWNSTREAM_STACKED_BLOCK"
ID_POINT = "ID_POINT"
ID_POINT_X = "ID_X"
ID_POINT_Y = "ID_Y"

HEIGHT_FIELD = "HEIGHT_ROO"
BASE_HEIGHT_FIELD = "BASE_HEIGHT"
CAVITY_BASE_HEIGHT_FIELD = "CAVITY_BASE_HEIGHT"
UPSTREAM_HEIGHT_FIELD = "UPSTREAM_HEIGHT"
DOWNSTREAM_HEIGHT_FIELD = "DOWNSTREAM_HEIGHT"
UPWIND_FACADE_ANGLE_FIELD = "THETA_WIND"
UPWIND_FACADE_FIELD = "UPWIND_FACADE_ID"
EFFECTIVE_LENGTH_FIELD = "L_EFF"
EFFECTIVE_WIDTH_FIELD = "W_EFF"
DISPLACEMENT_LENGTH_FIELD = "Lf"
DISPLACEMENT_LENGTH_VORTEX_FIELD = "Lfv"
CAVITY_LENGTH_FIELD = "Lr"
WAKE_LENGTH_FIELD = "Lw"
ROOFTOP_PERP_LENGTH = "Lc"
ROOFTOP_PERP_HEIGHT = "Hcm"
ROOFTOP_WIND_FACTOR = "C1"

PREFIX_NAME = "BUILDINGS"
SUFFIX_NAME = datetime.now().strftime("%Y%m%d%H%M%S")
DISTANCE_BUILD_TO_POINT_FIELD = "DY_0"
LENGTH_ZONE_FIELD = "DY_N"

DISPLACEMENT_NAME = "DISPLACEMENT"
DISPLACEMENT_VORTEX_NAME = "DISPLACEMENT_VORTEX"
CAVITY_NAME = "CAVITY"
WAKE_NAME = "WAKE"
STREET_CANYON_NAME = "STREET_CANYON"

DEBUG = True