#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 14:34:12 2021

@author: Jérémy Bernard, University of Gothenburg
"""

from . import DataUtil as DataUtil
import pandas as pd
from .GlobalVariables import *

def obstacleProperties(cursor, obstaclesTable, prefix = PREFIX_NAME):
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
            prefix: String, default PREFIX_NAME
                Prefix to add to the output table name
            
		Returns
		_ _ _ _ _ _ _ _ _ _ 

            obstaclePropertiesTable: String
                Name of the table containing the properties of each obstacle"""
    print("Calculates obstacle properties")
    
    # Output base name
    outputBaseName = "PROPERTIES"
    
    # Name of the output table
    obstaclePropertiesTable = DataUtil.prefix(outputBaseName,
                                              prefix = prefix)
    
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

def zoneProperties(cursor, obstaclePropertiesTable, prefix = PREFIX_NAME):
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
            prefix: String, default PREFIX_NAME
                Prefix to add to the output table name
            
		Returns
		_ _ _ _ _ _ _ _ _ _ 

            zonePropertiesTable: String
                Name of the table containing the properties of each obstacle zones"""
    print("Calculates zone properties")
    
    # Output base name
    outputBaseName = "ZONE_LENGTH"
    
    # Name of the output table
    zoneLengthTable = DataUtil.prefix(outputBaseName, 
                                      prefix = prefix)
    
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

def studyAreaProperties(cursor, upwindTable, stackedBlockTable, vegetationTable):
    """ Calculates roughness height (z0) and displacement length (d) of the study area 
    for a wind coming from North (thus you first need to rotate your
                                  obstacles to make them facing north if you 
                                  want to study a different wind direction).
    The calculation method is based on Equations 17a to 18c from Hanna and 
    Britter (2002). For building, each facade facing the wind is considered
    while the calculation is simplified for vegetation : the frontal area is
    simply calculated as the cross wind width of each vegetation patch 
    multiplied by its crown vegetation height.
    
    WARNING: Hanna and Britter (2002) say that: "It is suggested that an upper limit to H,
    should be 20 m and an upper limit to z, is therefore about 3 m. Conse-
    quently these methods should not be used for skyscrapers in a large city
    center or for the Rocky Mountains"
    
    References:
        Hanna, SR, et RE Britter. « Wind flow and vapor cloud dispersion at
        industrial sites. Am. Inst ». Chem Eng, New York, 2002.


		Parameters
		_ _ _ _ _ _ _ _ _ _ 

            cursor: conn.cursor
                A cursor object, used to perform spatial SQL queries
            upwindTable: String
                Name of the table containing the obstacle upwind facades
                (WARNING : WITH BASE HEIGHT NOT UPDATED)
            stackedBlockTable: String
                Name of the table containing the stacked blocks
            vegetationTable: String
                Name of the table containing the vegetation patches
            
		Returns
		_ _ _ _ _ _ _ _ _ _ 

            z0: float
                Value of the study area roughness height
            d: float
                Value of the study area displacement length
            Hr: float
                Value of the study area geometric mean height
            lambda_f: float
                Value of the study area frontal density"""
    print("Calculates study area properties")
    
    # Calculate the area of the study area
    cursor.execute("""
           SELECT ST_AREA(ST_BUFFER(ST_EXTENT({0}), 15))
           FROM   (SELECT    {0}
                  FROM {1}
                  UNION ALL
                  SELECT    {0}
                  FROM {2}) AS STUDY_AREA_AREA_TAB
           """.format(  GEOM_FIELD, 
                        stackedBlockTable,
                        vegetationTable))
    area = cursor.fetchall()[0][0]
    
    # Calculates the obstacle (stacked blocks and vegetation) 
    # geometric mean height (H_r)
    cursor.execute("""
           {0};
           """.format(DataUtil.createIndex(  tableName=stackedBlockTable, 
                                             fieldName=ID_FIELD_BLOCK,
                                             isSpatial=False)))
    cursor.execute("""
           SELECT   EXP(1.0/COUNT(OBSTACLE_HEIGHT_TAB.*)*
                        SUM(LOG(OBSTACLE_HEIGHT_TAB.HEIGHT))) AS H_r,
            FROM (SELECT MAX({0}) AS HEIGHT
                  FROM {1}
                  GROUP BY {4}
                  UNION ALL
                  SELECT {2} AS HEIGHT
                  FROM {3}) AS OBSTACLE_HEIGHT_TAB;""".format(HEIGHT_FIELD, 
                    stackedBlockTable,
                    VEGETATION_CROWN_TOP_HEIGHT,
                    vegetationTable,
                    ID_FIELD_BLOCK))
    H_r = cursor.fetchall()[0][0]
    
    # Calculates the obstacle (stacked blocks and vegetation) 
    # and frontal density (lambda_f)
    cursor.execute("""
            SELECT  SUM(FRONTAL_AREA_TAB.CROSS_WIND_LENGTH*
                        FRONTAL_AREA_TAB.CROSS_WIND_HEIGHT)/{7}
                     AS LAMBDA_f
            FROM    (SELECT    ST_XMAX({3})- ST_XMIN({3}) AS CROSS_WIND_LENGTH,
                            {0}-{4} AS CROSS_WIND_HEIGHT
                      FROM {5}
                      UNION ALL
                      SELECT    ST_XMAX({3})- ST_XMIN({3}) AS CROSS_WIND_LENGTH,
                                {1}-{6} AS CROSS_WIND_HEIGHT
                      FROM {2}) AS FRONTAL_AREA_TAB
         """.format(HEIGHT_FIELD,
                    VEGETATION_CROWN_TOP_HEIGHT,
                    vegetationTable,
                    GEOM_FIELD,
                    BASE_HEIGHT_FIELD, 
                    upwindTable,
                    VEGETATION_CROWN_BASE_HEIGHT,
                    area))
    lambda_f = cursor.fetchall()[0][0]
    
    # Calculates z0 and d according to Hanna and Britter (2002) Equations 16-17
    z0 = 0
    d = 0
    if lambda_f<=0.15:
        z0 = lambda_f*H_r
        if lambda_f<=0.05:
            d = 3*lambda_f*H_r
        else:
            d = 0.15+5.5*(lambda_f-0.05)
    elif lambda_f>0.15:
        if lambda_f>1:
            lambda_f = 1
        z0 = 0.15*H_r
        d = 0.7+0.35*(lambda_f-0.15)
    
    return z0, d, H_r, lambda_f

def maxObstacleHeight(cursor, stackedBlockTable, vegetationTable):
    """ Calculates the maximum height of the obstacles within the study area.

		Parameters
		_ _ _ _ _ _ _ _ _ _ 

            cursor: conn.cursor
                A cursor object, used to perform spatial SQL queries
            stackedBlockTable: String
                Name of the table containing the stacked blocks
            vegetationTable: String
                Name of the table containing the vegetation patches
            
		Returns
		_ _ _ _ _ _ _ _ _ _ 

            Hmax: float
                Value of the maximum obstacle height within the study area"""
    print("Calculates maximum obstacle height within the study area")
    
    # Calculates the obstacle (stacked blocks and vegetation) 
    # maximum height (Hmax)
    cursor.execute("""
           SELECT   MAX(HEIGHT) AS Hmax,
            FROM (SELECT MAX({0}) AS HEIGHT
                  FROM {1}
                  UNION ALL
                  SELECT MAX({2}) AS HEIGHT
                  FROM {3}) AS OBSTACLE_HEIGHT_TAB;""".format(HEIGHT_FIELD, 
                    stackedBlockTable,
                    VEGETATION_CROWN_TOP_HEIGHT,
                    vegetationTable))
    H_max = cursor.fetchall()[0][0]
    
    return H_max