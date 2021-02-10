#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 14:34:12 2021

@author: Jérémy Bernard, University of Gothenburg
"""

import URock.DataUtil as DataUtil
import pandas as pd
from URock.GlobalVariables import *

def obstacleProperties(cursor, obstaclesTable):
    """ Calculates obstacle properties (effective width and length) 
    for a wind coming from North (thus you first need to rotate your
                                  obstacles to make them facing north if you 
                                  want to study a different wind direction).
    The calculation method is based on Figure 1 of Nelson et al. (2008). Note
    that it is however adapted to our specific geometries which are sometimes
    far from rectangles...
    
    References:
        Nelson, Matthew, Bhagirath Addepalli, Fawn Hornsby, Akshay Gowardhan, 
        Eric Pardyjak, et Michael Brown. « 5.2 Improvements to a Fast-Response 
        Urban Wind Model », 2008.

		Parameters
		_ _ _ _ _ _ _ _ _ _ 

            cursor: conn.cursor
                A cursor object, used to perform spatial SQL queries
            obstaclesTable: String
                Name of the table containing the obstacle geometries to characterize
            
		Returns
		_ _ _ _ _ _ _ _ _ _ 

            obstaclePropertiesTable: String
                Name of the table containing the properties of each obstacle"""
    print("Calculates obstacle properties")
    
    # Output base name
    outputBaseName = "PROPERTIES"
    
    # Name of the output table
    obstaclePropertiesTable = DataUtil.prefix(outputBaseName)
    
    # Calculates the effective width (Weff) and effective length (Leff)
    # of each obstacle, respectively  based on their maximum cross-wind and
    # along-wind extends of the obstacle, weighted by the area ratio between
    # obstacle area and envelope area
    query = """
       DROP TABLE IF EXISTS {0};
       CREATE TABLE {0}
           AS SELECT   {1},
                       {2},
                       {3},
                       {4},
                       (ST_XMAX(ST_ENVELOPE({3}))-ST_XMIN({3}))*ST_AREA({3})/ST_AREA(ST_ENVELOPE({3})) AS {6},
                       (ST_YMAX(ST_ENVELOPE({3}))-ST_YMIN({3}))*ST_AREA({3})/ST_AREA(ST_ENVELOPE({3})) AS {7}
           FROM {5}""".format(obstaclePropertiesTable, 
                               ID_FIELD_STACKED_BLOCK,
                               ID_FIELD_BLOCK,
                               GEOM_FIELD,
                               HEIGHT_FIELD,
                               obstaclesTable,
                               EFFECTIVE_WIDTH_FIELD, 
                               EFFECTIVE_LENGTH_FIELD)
    cursor.execute(query)
    
    return obstaclePropertiesTable

def zoneProperties(cursor, obstaclePropertiesTable):
    """ Calculates properties of the "Röckle" (some are not) zones:
        - for displacement: length Lf and vortex length Lfv (Bagal et al. - 2004),
        - for cavity: length Lr (equation 3 in Kaplan et al. - 1996),
        - for wake: length Lw (3*Lr, Kaplan et al. - 1996)
        - for rooftop perpendicular: height Hcm and length Lc (Pol et al. 2006)
        - for rooftop corner: wind speed factor C1 (Bagal et al. 2004 "Implementation of rooftop...)
    Note that L and W in the equation are respectively replaced by the 
    effective length and width of each obstacle.
    
    References:
            Bagal, N, ER Pardyjak, et MJ Brown. « Improved upwind cavity 
       parameterization for a fast response urban wind model ». In 84th Annual
       AMS Meeting. Seattle, WA, 2004.
            Kaplan, H., et N. Dinar. « A Lagrangian Dispersion Model for Calculating
       Concentration Distribution within a Built-up Domain ». Atmospheric 
       Environment 30, nᵒ 24 (1 décembre 1996): 4197‑4207.
       https://doi.org/10.1016/1352-2310(96)00144-6.

		Parameters
		_ _ _ _ _ _ _ _ _ _ 

            cursor: conn.cursor
                A cursor object, used to perform spatial SQL queries
            obstaclePropertiesTable: String
                Name  of the table containing the obstacle properties Weff, Leff
                and height
            
		Returns
		_ _ _ _ _ _ _ _ _ _ 

            zonePropertiesTable: String
                Name of the table containing the properties of each obstacle zones"""
    print("Calculates zone properties")
    
    # Output base name
    outputBaseName = "ZONE_LENGTH"
    
    # Name of the output table
    zoneLengthTable = DataUtil.prefix(outputBaseName)
    
    # Calculates the length (and sometimes height) of each zone:
    #   - for displacement: Lf and Lfv (Bagal et al. - 2004),
    #   - for cavity: Lr (equation 3 in Kaplan et al. - 1996),
    #   - for wake: Lw (3*Lr, Kaplan et al. - 1996)
    #   - rooftop perpendicular: Hcm and Lc (Pol et al. 2006)
    #   - rooftop corner: C1 (Bagal et al. 2004 "Implementation of rooftop...)
    query = """
       DROP TABLE IF EXISTS {0};
       CREATE TABLE {0}
           AS SELECT   {1},
                       {2},
                       {3},
                       1.5*{9}/(1+0.8*{9}/{3}) AS {4},
                       0.6*{9}/(1+0.8*{9}/{3}) AS {10},
                       1.8*{9}/(POWER({8}/{3},0.3)*(1+0.24*{9}/{3})) AS {5},
                       3*1.8*{9}/(POWER({8}/{3},0.3)*(1+0.24*{9}/{3})) AS {6},
                       0.22*(0.67*LEAST({3},{9})+0.33*GREATEST({3},{9})) AS {11},
                       0.9*(0.67*LEAST({3},{9})+0.33*GREATEST({3},{9})) AS {12},
                       1+0.05*{9}/{3} AS {13}
           FROM {7}""".format(zoneLengthTable,
                               ID_FIELD_STACKED_BLOCK,
                               GEOM_FIELD, 
                               HEIGHT_FIELD, 
                               DISPLACEMENT_LENGTH_FIELD, 
                               CAVITY_LENGTH_FIELD,
                               WAKE_LENGTH_FIELD, 
                               obstaclePropertiesTable,
                               EFFECTIVE_LENGTH_FIELD,
                               EFFECTIVE_WIDTH_FIELD,
                               DISPLACEMENT_LENGTH_VORTEX_FIELD,
                               ROOFTOP_PERP_HEIGHT,
                               ROOFTOP_PERP_LENGTH,
                               ROOFTOP_WIND_FACTOR)
    cursor.execute(query)
    
    return zoneLengthTable