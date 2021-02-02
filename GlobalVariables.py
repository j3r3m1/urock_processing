#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 25 16:26:24 2021

@author: Jérémy Bernard, University of Gothenburg
"""
from datetime import datetime

GEOM_FIELD = "THE_GEOM"
ID_FIELD_BUILD = "ID_BUILD"
ID_FIELD_BLOCK = "ID_BLOCK"
ID_FIELD_STACKED_BLOCK = "ID_STACKED_BLOCK"
HEIGHT_FIELD = "HEIGHT_ROO"
UPSTREAM_HEIGHT_FIELD = "UPSTREAM_HEIGHT"
DOWNSTREAM_HEIGHT_FIELD = "DOWNSTREAM_HEIGHT"
UPWIND_FACADE_ANGLE_FIELD = "THETA_WIND"
UPWIND_FACADE_FIELD = "UPWIND_FACADE_ID"
EFFECTIVE_LENGTH_FIELD = "L_EFF"
EFFECTIVE_WIDTH_FIELD = "W_EFF"
DISPLACEMENT_LENGTH_FIELD = "Lf"
CAVITY_LENGTH_FIELD = "Lr"
WAKE_LENGTH_FIELD = "Lw"
PERPENDICULAR_FIELD = "PERPENDICULAR"
PREFIX_NAME = "BUILDINGS"
SUFFIX_NAME = datetime.now().strftime("%Y%m%d%H%M%S")

PERPENDICULAR_THRESHOLD_ANGLE = 10
ELLIPSOID_MIN_LENGTH = 0.1
SNAPPING_TOLERANCE = 0.1
GEOMETRY_SIMPLIFICATION_DISTANCE = 0.25
# Note that the number of points of an ellipse is only used to identify whether
# the upper or lower part of an ellipse should be used (fro displacement zones),
# the number of points used to create an ellipse can not be chosen yet
# Need to create this variable in H2GIS 
# https://github.com/locationtech/jts/blob/9d4097312d68cb8f9ae591bec69ce3b403e41e98/modules/core/src/main/java/org/locationtech/jts/util/GeometricShapeFactory.java#L101
NPOINTS_ELLIPSE = 100

