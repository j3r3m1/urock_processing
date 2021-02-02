#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 25 15:27:25 2021

@author: Jérémy Bernard, University of Gothenburg
"""
import URock.DataUtil as DataUtil
import pandas as pd
from URock.GlobalVariables import *


def calculatesObstacleProperties(cursor, dicOfInputTables):
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
            dicOfInputTables: dictionary of String
                Dictionary of String with type of obstacle as key and as value
                input table name (tables containing the geometries 
                                  to characterize)
            
		Returns
		_ _ _ _ _ _ _ _ _ _ 

            dicOfPropertiesTables: dictionary
                Map of initial table names as keys and geometric properties 
                table names as values"""
    print("Calculates obstacle properties")
    
    # Name of the output tables
    dicOfPropertiesTables = {t: dicOfInputTables[t]+"_PROPERTIES" 
                             for t in dicOfInputTables.keys()}
    
    # Calculates the effective width (Weff) and effective length (Leff)
    # of each obstacle, respectively  based on their maximum cross-wind and
    # along-wind extends of the obstacle, weighted by the area ratio between
    # obstacle area and envelope area
    listOfQueries = ["""
       DROP TABLE IF EXISTS {0};
       CREATE TABLE {0}
           AS SELECT   {1},
                       {2},
                       {3},
                       {4},
                       (ST_XMAX(ST_ENVELOPE({3}))-ST_XMIN({3}))*ST_AREA({3})/ST_AREA(ST_ENVELOPE({3})) AS {6},
                       (ST_YMAX(ST_ENVELOPE({3}))-ST_YMIN({3}))*ST_AREA({3})/ST_AREA(ST_ENVELOPE({3})) AS {7}
           FROM {5}""".format(dicOfPropertiesTables[t], 
                               ID_FIELD_STACKED_BLOCK,
                               ID_FIELD_BLOCK,
                               GEOM_FIELD,
                               HEIGHT_FIELD,
                               dicOfInputTables[t],
                               EFFECTIVE_WIDTH_FIELD, 
                               EFFECTIVE_LENGTH_FIELD) for t in dicOfPropertiesTables.keys()]
    cursor.execute(";".join(listOfQueries))
    
    return dicOfPropertiesTables

def calculatesZoneLength(cursor, dicOfInputTables):
    """ Calculates the length of the displacement zone (Lf), the cavity zone (Lr)
    and the wake zone (3*Lr) based on Kaplan et al. (1996) formulae. Note that
    L and W in the equation are respectively replaced by the effective length
    and width of each obstacle.
    
    References:
       Kaplan, H., et N. Dinar. « A Lagrangian Dispersion Model for Calculating
       Concentration Distribution within a Built-up Domain ». Atmospheric 
       Environment 30, nᵒ 24 (1 décembre 1996): 4197‑4207.
       https://doi.org/10.1016/1352-2310(96)00144-6.

		Parameters
		_ _ _ _ _ _ _ _ _ _ 

            cursor: conn.cursor
                A cursor object, used to perform spatial SQL queries
            dicOfInputTables: dictionary of String
                Dictionary of String with type of obstacle as key and as value
                input table name (tables containing the obstacle properties
                                  Weff, Leff and height)
            
		Returns
		_ _ _ _ _ _ _ _ _ _ 

            dicOfZoneLengthTables: dictionary
                Map of initial table names as keys and geometric properties 
                table names as values"""
    print("Calculates zone length of each obstacle")
    
    # Name of the output tables
    dicOfZoneLengthTables = {t: dicOfInputTables[t]+"_ZONE_LENGTH" 
                             for t in dicOfInputTables.keys()}
    
    # Calculates the length of each zone based on Kaplan et Dinard (1996)
    # Lf - equation (1), Lr - equation (3), Lw - 3*Lr
    listOfQueries = ["""
       DROP TABLE IF EXISTS {0};
       CREATE TABLE {0}
           AS SELECT   {1},
                       {2},
                       {3},
                       2*{9}/(1+0.8*{9}/{3}) AS {4},
                       1.8*{9}/(POWER({8}/{3},0.3)*(1+0.24*{9}/{3})) AS {5},
                       3*1.8*{9}/(POWER({8}/{3},0.3)*(1+0.24*{9}/{3})) AS {6}
           FROM {7}""".format(dicOfZoneLengthTables[t],
                               ID_FIELD_STACKED_BLOCK,
                               GEOM_FIELD, 
                               HEIGHT_FIELD, 
                               DISPLACEMENT_LENGTH_FIELD, 
                               CAVITY_LENGTH_FIELD,
                               WAKE_LENGTH_FIELD, 
                               dicOfInputTables[t],
                               EFFECTIVE_LENGTH_FIELD,
                               EFFECTIVE_WIDTH_FIELD) 
                     for t in dicOfZoneLengthTables.keys()]
    cursor.execute(";".join(listOfQueries))
    
    return dicOfZoneLengthTables

def initUpwindFacades(cursor, dicOfInputTables):
    """ Identify upwind facades, convert them to lines (they are initially
    included within polygons) and calculates their direction from wind speed 
    (90° for a facade perpendicular from the upwind).

		Parameters
		_ _ _ _ _ _ _ _ _ _ 

            cursor: conn.cursor
                A cursor object, used to perform spatial SQL queries
            dicOfInputTables: dictionary of String
                Dictionary of String with type of obstacle as key and as value
                input table name as value (tables containing the input geometries)
            
		Returns
		_ _ _ _ _ _ _ _ _ _ 

            dicOfUpwindTables: dictionary
                Map of initial table names as keys and upwind facade table names as values"""
    print("Initializes upwind facades")
    
    # Name of the output tables
    dicOfUpwindTables = {t: dicOfInputTables[t]+"_UPWIND" for t in dicOfInputTables.keys()}
    
    listOfQueries = ["""
       DROP TABLE IF EXISTS {0};
       CREATE TABLE {0}({5} SERIAL, {1} INTEGER, {2} GEOMETRY, {3} DOUBLE, {6} INTEGER)
           AS SELECT   NULL AS {5},
                       {1},
                       {2} AS {2},
                       ST_AZIMUTH(ST_STARTPOINT({2}), 
                                  ST_ENDPOINT({2})) AS {3},
                       {6},
           FROM ST_EXPLODE('(SELECT ST_TOMULTISEGMENTS({2}) AS {2},
                                  {1},
                                  {6}
                                  FROM {4})')
           WHERE ST_AZIMUTH(ST_STARTPOINT({2}), 
                            ST_ENDPOINT({2})) < PI()
           """.format(dicOfUpwindTables[t], 
                       ID_FIELD_STACKED_BLOCK,
                       GEOM_FIELD, 
                       UPWIND_FACADE_ANGLE_FIELD, 
                       dicOfInputTables[t], 
                       UPWIND_FACADE_FIELD) for t in dicOfUpwindTables.keys()]
    cursor.execute(";".join(listOfQueries))
    
    return dicOfUpwindTables

def createsDisplacementZones(cursor, dicOfInputGeometryTables, dicOfInputLengthTables):
    """ Creates the displacement zone for each of the building upwind facade
    based on Kaplan et Dinar (1996) for the equations of the ellipsoid 
        - Equation 2 when the facade is perpendicular to the wind,
        - Figure 2 and Table 1 when the facade has an angle Theta with the wind.
    
    Obstacle length and width in the equations are given in an input table.
    Note that we strongly recommand to use the 'calculatesZoneLength' function
    to calculate effective length and width instead of maximum length and width...

    References:
       Kaplan, H., et N. Dinar. « A Lagrangian Dispersion Model for Calculating
       Concentration Distribution within a Built-up Domain ». Atmospheric 
       Environment 30, nᵒ 24 (1 décembre 1996): 4197‑4207.
       https://doi.org/10.1016/1352-2310(96)00144-6.


		Parameters
		_ _ _ _ _ _ _ _ _ _ 

            cursor: conn.cursor
                A cursor object, used to perform spatial SQL queries
            dicOfInputGeometryTables: dictionary of String
                Dictionary of String with type of obstacle as key and as value
                input table name containing upwind segment geometries
                (and also the ID of each stacked obstacle)
            dicOfInputLengthTables: dictionary of String
                Dictionary of String with type of obstacle as key and as value
                input table name containing obstacle zone length
                (and also the ID of each stacked obstacle)
            
		Returns
		_ _ _ _ _ _ _ _ _ _ 

            dicOfDisplacementZoneTables: dictionary
                Map of initial table names as keys and table name of the 
                corresponding displacement zones as value"""
    print("Creates displacement zones")
    
    # Name of the output tables
    dicOfDisplacementZoneTables = {t: dicOfInputGeometryTables[t]+"_DISPLACEMENT_ZONES" 
                                   for t in dicOfInputGeometryTables.keys()}
    
    listOfQueries = ["""
        CREATE INDEX IF NOT EXISTS idx_{8} ON {8} USING BTREE({10});
        CREATE INDEX IF NOT EXISTS idx_{9} ON {9} USING BTREE({10});
        DROP TABLE IF EXISTS {0};
        CREATE TABLE {0}
            AS SELECT   {1},
                        {2},
                        {3},
                        {10},
                        CAST(CASE    WHEN ABS(DEGREES({4})) < {5} THEN 1
                                    ELSE 0 END AS INTEGER) AS {6}
            FROM ST_EXPLODE('(SELECT ST_SPLIT(ST_SNAP(ST_ROTATE(ST_MAKEELLIPSE(ST_CENTROID(a.{2}),
                                                                                ST_LENGTH(a.{2}),
                                                                                2*b.{7}*SIN(a.{4})*SIN(a.{4})),
                                                                0.5*PI()-a.{4}),
                                                     a.{2},
                                                     {12}),
                                             a.{2}) AS {2},
                                     a.{1},
                                     b.{3},
                                     a.{4},
                                     a.{10},
                                     ST_LENGTH(a.{2})/2 AS R_x,
                                     b.{7}*SIN(a.{4})*SIN(a.{4}) AS R_y
                             FROM {8} AS a LEFT JOIN {9} AS b ON a.{10} = b.{10}
                             WHERE b.{7}*SIN(a.{4})*SIN(a.{4})>{11})')
             WHERE      {4}>=0.5*PI()
                            -0.5*PI()+ACOS((1-COS(2*PI()/{13}))*R_x
                                  /SQRT(POWER((1-COS(2*PI()/{13}))*R_x,2)
                                        +POWER(SIN(2*PI()/{13})*R_y,2)))
                   AND EXPLOD_ID = 2 
                   OR   {4}<0.5*PI()
                            -0.5*PI()+ACOS((1-COS(2*PI()/{13}))*R_x
                                  /SQRT(POWER((1-COS(2*PI()/{13}))*R_x,2)
                                        +POWER(SIN(2*PI()/{13})*R_y,2)))
                   AND EXPLOD_ID = 1
           """.format(dicOfDisplacementZoneTables[t]    , UPWIND_FACADE_FIELD,
                       GEOM_FIELD                       , HEIGHT_FIELD,
                       UPWIND_FACADE_ANGLE_FIELD        , PERPENDICULAR_THRESHOLD_ANGLE,
                       PERPENDICULAR_FIELD              , DISPLACEMENT_LENGTH_FIELD,
                       dicOfInputGeometryTables[t]      , dicOfInputLengthTables[t],
                       ID_FIELD_STACKED_BLOCK           , ELLIPSOID_MIN_LENGTH,
                       SNAPPING_TOLERANCE               , NPOINTS_ELLIPSE) 
                     for t in dicOfDisplacementZoneTables.keys()]
    cursor.execute(";".join(listOfQueries))
    
    return dicOfDisplacementZoneTables

def createsCavityAndWakeZones(cursor, dicOfInputTables):
    """ Creates the cavity and wake zones for each of the stacked building
    based on Kaplan et Dinar (1996) for the equations of the ellipsoid 
    (Equation 3). When the building has a non rectangular shape or is not
    perpendicular to the wind direction, use the principles of Figure 1
    in Nelson et al. (2008): the extreme south of the geometry is used
    as center of the ellipse and the ellipse is merged with the envelope 
    of the geometry.
    
    Obstacle length and width in the equations are given in an input table.
    Note that we strongly recommand to use the 'calculatesZoneLength' function
    to calculate effective length and width instead of maximum length and width...

    References:
            Kaplan, H., et N. Dinar. « A Lagrangian Dispersion Model for Calculating
        Concentration Distribution within a Built-up Domain ». Atmospheric 
        Environment 30, nᵒ 24 (1 décembre 1996): 4197‑4207.
        https://doi.org/10.1016/1352-2310(96)00144-6.
           Nelson, Matthew, Bhagirath Addepalli, Fawn Hornsby, Akshay Gowardhan, 
        Eric Pardyjak, et Michael Brown. « 5.2 Improvements to a Fast-Response 
        Urban Wind Model », 2008.


		Parameters
		_ _ _ _ _ _ _ _ _ _ 

            cursor: conn.cursor
                A cursor object, used to perform spatial SQL queries
            dicOfInputTables: dictionary of String
                Dictionary of String with type of obstacle as key and as value
                input table name containing stacked obstacle geometries
                and zone length
            
		Returns
		_ _ _ _ _ _ _ _ _ _ 

            dicOfCavityZoneTables: dictionary
                Map of initial table names as keys and table name of the 
                corresponding cavity zones as value
            dicOfWakeZoneTables: dictionary
                Map of initial table names as keys and table name of the 
                corresponding wake zones as value"""
    print("Creates cavity and wake zones")
    
    # Name of the output tables
    dicOfCavityZoneTables = {t: dicOfInputTables[t]+"_CAVITY_ZONE" 
                                   for t in dicOfInputTables.keys()}
    dicOfWakeZoneTables = {t: dicOfInputTables[t]+"_WAKE_ZONE" 
                                   for t in dicOfInputTables.keys()}
    
    # Queries for the cavity zones
    listOfQueries = ["""
        DROP TABLE IF EXISTS {0};
        CREATE TABLE {0}
            AS SELECT   {1},
                        {2},
                        {3}
            FROM ST_EXPLODE('(SELECT ST_SPLIT(ST_SNAP(ST_UNION(ST_MAKEELLIPSE(ST_MAKEPOINT((ST_XMIN(ST_ENVELOPE({2}))+
                                                                                            ST_XMAX(ST_ENVELOPE({2})))/2,
                                                                                            ST_YMIN(ST_ENVELOPE({2}))),
                                                                                ST_XMAX(ST_ENVELOPE({2}))-ST_XMIN(ST_ENVELOPE({2})),
                                                                                2*{4}),
                                                                 ST_ENVELOPE({2})),
                                                     ST_ENVELOPE({2}),
                                                     {6}),
                                             ST_GeometryN(ST_TOMULTILINE({2}),1)) AS {2},
                                     {1},
                                     {3}
                             FROM {5})')
             WHERE EXPLOD_ID = 1
                     
           """.format(dicOfCavityZoneTables[t]          , ID_FIELD_STACKED_BLOCK,
                       GEOM_FIELD                       , HEIGHT_FIELD,
                       CAVITY_LENGTH_FIELD              , dicOfInputTables[t],
                       SNAPPING_TOLERANCE) 
                     for t in dicOfInputTables.keys()]
    cursor.execute(";".join(listOfQueries))
    
    # Queries for the wake zones
    listOfQueries = ["""
        DROP TABLE IF EXISTS {0};
        CREATE TABLE {0}
            AS SELECT   {1},
                        {2},
                        {3}
            FROM ST_EXPLODE('(SELECT ST_SPLIT(ST_SNAP(ST_UNION(ST_MAKEELLIPSE(ST_MAKEPOINT((ST_XMIN(ST_ENVELOPE({2}))+
                                                                                            ST_XMAX(ST_ENVELOPE({2})))/2,
                                                                                            ST_YMIN(ST_ENVELOPE({2}))),
                                                                                ST_XMAX(ST_ENVELOPE({2}))-ST_XMIN(ST_ENVELOPE({2})),
                                                                                6*{4}),
                                                                 ST_ENVELOPE({2})),
                                                     ST_ENVELOPE({2}),
                                                     {6}),
                                             ST_GeometryN(ST_TOMULTILINE({2}),1)) AS {2},
                                     {1},
                                     {3}
                             FROM {5})')
             WHERE EXPLOD_ID = 1
                     
           """.format(dicOfWakeZoneTables[t]            , ID_FIELD_STACKED_BLOCK,
                       GEOM_FIELD                       , HEIGHT_FIELD,
                       WAKE_LENGTH_FIELD                , dicOfInputTables[t],
                       SNAPPING_TOLERANCE) 
                     for t in dicOfInputTables.keys()]
    cursor.execute(";".join(listOfQueries))    
    
    return dicOfCavityZoneTables, dicOfWakeZoneTables

def createsStreetCanyonZones(cursor, dicOfStackedTables, dicOfUpwindTables):
    """ Creates the street canyon zones for each of the stacked building
    based on Nelson et al. (2008) Figure 8b. The method is slightly different
    since we use the cavity zone instead of the Lr buffer.

    References:
           Nelson, Matthew, Bhagirath Addepalli, Fawn Hornsby, Akshay Gowardhan, 
        Eric Pardyjak, et Michael Brown. « 5.2 Improvements to a Fast-Response 
        Urban Wind Model », 2008.


		Parameters
		_ _ _ _ _ _ _ _ _ _ 

            cursor: conn.cursor
                A cursor object, used to perform spatial SQL queries
            cavityZoneTable: String
                Name of the table containing the cavity zones and the ID of
                each stacked obstacle
            stackedObstacleTable: String
                Name of the table containing the geometry, zone length, height
                and ID of each stacked obstacle
            upwindTables: String
                Name of the table containing upwind segment geometries
                (and also the ID of each stacked obstacle)
            
		Returns
		_ _ _ _ _ _ _ _ _ _ 

            streetCanyonZoneTable: String
                Name of the table containing the street canyon zones"""
    print("Creates street canyon zones")
    
    # Name of the output tables
    streetCanyonZoneTable = PREFIX_NAME+"_STREETCANYON_ZONE"
    
    # Create temporary table names (for tables that will be removed at the end of the IProcess)
    intersectTable = DataUtil.postfix("intersect_table")
    canyonExtendTable = DataUtil.postfix("canyon_extend_table")
    
    # Identify upwind facades intersected by cavity zones
    intersectionQuery = """
        CREATE INDEX IF NOT EXISTS idx_geo_{3} ON {3} USING RTREE({2});
        CREATE INDEX IF NOT EXISTS idx_geo_{4} ON {4} USING RTREE({2});
        DROP TABLE IF EXISTS {0};
        CREATE TABLE {0}
            AS SELECT   {1},
                        {2},
            FROM    ST_EXPLODE('(SELECT    b.{1}, 
                                           ST_INTERSECTION(a.{2}, b.{2}) AS {2},
                               FROM {3} AS a, {4} AS b
                               WHERE a.{2} & b.{2} AND ST_INTERSECTS(a.{2}, b.{2}))')
                     
           """.format( intersectTable                   , ID_FIELD_STACKED_BLOCK,
                       GEOM_FIELD                       , upwindTables,
                       cavityZoneTable)
    cursor.execute(intersectionQuery)
    
    # Identify street canyon extend
    canyonExtendQuery = """
        CREATE INDEX IF NOT EXISTS idx_{0} ON {0} USING BTREE({1});
        CREATE INDEX IF NOT EXISTS idx_{2} ON {2} USING BTREE({1});
        DROP TABLE IF EXISTS {3};
        CREATE TABLE {3}
            AS SELECT   a.{1},
                        a.{6} AS {7},
                        b.{6} AS {8},
                        ST_MAKEPOLYGON(ST_MAKELINE(ST_STARTPOINT(a.{4}),
                    								ST_STARTPOINT(ST_TRANSLATE(a.{4}, 
                                                                               0, 
                                                                               ST_YMAX(b.{4})-ST_YMIN(b.{4})+b.{5})),
                    								ST_ENDPOINT(ST_TRANSLATE(a.{4},
                                                                             0, 
                                                                             ST_YMAX(b.{4})-ST_YMIN(b.{4})+b.{5})),
                    								ST_TOMULTIPOINT(ST_REVERSE(a.{4})))) AS THE_GEOM
            FROM {3} AS a LEFT JOIN {4} AS b ON a.{1} = b.{1}
                     
           """.format( intersectTable                   , ID_FIELD_STACKED_BLOCK,
                       stackedObstacleTable             , canyonExtendTable,
                       GEOM_FIELD                       , CAVITY_LENGTH_FIELD,
                       HEIGHT_FIELD                     , DOWNSTREAM_HEIGHT_FIELD,
                       UPSTREAM_HEIGHT_FIELD)
    cursor.execute(canyonExtendQuery)
    
    # Creates street canyon zones
    streetCanyonQuery = """
        CREATE INDEX IF NOT EXISTS idx_{0} ON {0} USING BTREE({1});
        DROP TABLE IF EXISTS {2};
        CREATE TABLE {2}
            AS SELECT   a.{1},
                        ST_GeometryN(ST_SPLIT(ST_SNAP(a.{3},
                                                     ST_TOMULTILINE(b.{3}),
                                                     {6}),
                                              ST_TOMULTILINE(b.{3})),1) AS {3},
                        a.{4},
                        a.{5}
            FROM        {0} AS a LEFT JOIN {6} AS b ON a.{1}=b.{1}
                     
           """.format( canyonExtendTable                , ID_FIELD_STACKED_BLOCK,
                       streetCanyonZoneTable            , GEOM_FIELD,
                       DOWNSTREAM_HEIGHT_FIELD          , UPSTREAM_HEIGHT_FIELD,
                       SNAPPING_TOLERANCE               , stackedObstacleTable)
    cursor.execute(streetCanyonQuery)
    
    # Drop intermediate tables
    cursor.execute("DROP TABLE IF EXISTS {0}".format(",".join([intersectTable,
                                                               canyonExtendTable])))
    
    return streetCanyonZoneTable