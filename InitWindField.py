#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  3 15:39:07 2021

@author: Jérémy Bernard, University of Gothenburg
"""

import URock.DataUtil as DataUtil
import pandas as pd
from URock.GlobalVariables import * 

def createGrid(cursor, dicOfInputTables, 
               alongWindZoneExtend = ALONG_WIND_ZONE_EXTEND, 
               crosswindZoneExtend = CROSS_WIND_ZONE_EXTEND, 
               meshSize = MESH_SIZE):
    """ Creates a grid of points which will be used to initiate the wind
    speed field.

		Parameters
		_ _ _ _ _ _ _ _ _ _ 

            cursor: conn.cursor
                A cursor object, used to perform spatial SQL queries
            dicOfInputTables: dictionary of String
                Dictionary of String with type of obstacle as key and input 
                table name as value (tables containing the rotated geometries)
            alongWindZoneExtend: float, default ALONG_WIND_ZONE_EXTEND
                Distance (in meter) of the extend of the zone around the
                rotated obstacles in the along-wind direction
            crosswindZoneExtend: float, default CROSS_WIND_ZONE_EXTEND
                Distance (in meter) of the extend of the zone around the
                rotated obstacles in the cross-wind direction
            meshSize: float, default MESH_SIZE
                Resolution (in meter) of the grid
            
		Returns
		_ _ _ _ _ _ _ _ _ _ 

            gridTable: String
                Name of the grid point table"""
    print("Creates the grid of points")
    
    # Output base name
    outputBaseName = "GRID"
    
    # Name of the output table
    gridTable = DataUtil.prefix(outputBaseName)
    
    # Gather all tables in one
    gatherQuery = ["""SELECT {0} FROM {1}""".format( GEOM_FIELD, dicOfInputTables[t])
                     for t in dicOfInputTables.keys()]
    
    # Calculate the extend of the envelope of all geometries
    finalQuery = """
        DROP TABLE IF EXISTS {0};
        CREATE TABLE {0}
            AS SELECT   {1},
                        ID AS {6},
                        ID_COL AS {7},
                        ID_ROW AS {8},
                        ST_Y({1}) AS Y_POINT,
            FROM ST_MAKEGRIDPOINTS((SELECT ST_EXPAND(ST_ACCUM({1}),
                                                      {2},
                                                      {3}) FROM ({5})), 
                                    {4}, 
                                    {4})""".format(gridTable, 
                                                   GEOM_FIELD,
                                                   crosswindZoneExtend,
                                                   alongWindZoneExtend,
                                                   meshSize,
                                                   " UNION ALL ".join(gatherQuery),
                                                   ID_POINT,
                                                   ID_POINT_X,
                                                   ID_POINT_Y)
    cursor.execute(finalQuery)
    
    return gridTable

def affectsPointToZone(cursor, gridTable, dicOfRockleZoneTable):
    """ Affects each point to a building Rockle zone and calculates relative
    point position within the zone for some of them.

		Parameters
		_ _ _ _ _ _ _ _ _ _ 

            cursor: conn.cursor
                A cursor object, used to perform spatial SQL queries
            gridTable: String
                Name of the grid point table
            dicOfRockleZoneTable: Dictionary of Rockle zone tables
                Dictionary containing as key the Rockle zone name and
                as value the corresponding table name
            
		Returns
		_ _ _ _ _ _ _ _ _ _ 

            dicOfOutputTables: dictionary of table name
                Dictionary having as key the type of Rockle zone and as value
                the name of the table containing points corresponding to the zone"""
    print("Affects each grid point to a Rockle zone and calculates relative point position")
    
    # Name of the output tables
    dicOfOutputTables = {t: DataUtil.postfix(tableName = DataUtil.prefix(tableName = t),
                                            suffix = "POINTS") for t in dicOfRockleZoneTable}
                                        
    # Temporary tables (and prefix for temporary tables)
    verticalLineTable = "VERTICAL_LINES"
    tempoPrefix = "TEMPO"
    prefixZoneLimits = "ZONE_LIMITS"
    
    # Tables that should keep y value
    listTabYvalues = [CAVITY_NAME, WAKE_NAME]
    
    query = ["""CREATE INDEX IF NOT EXISTS id_{1}_{0} ON {0} USING RTREE({1});
                 DROP TABLE IF EXISTS {2}""".format( gridTable,
                                                     GEOM_FIELD,
                                                     ",".join(dicOfOutputTables.values()))]
    # Construct a query to affect each point to a Rockle zone
    for i, t in enumerate(dicOfRockleZoneTable):
        # The query differs depending on whether y value should be kept
        queryKeepY = ""
        tempoTableName = dicOfOutputTables[t]
        if t in listTabYvalues:
            queryKeepY += "b.Y_POINT, b.{0},".format(ID_POINT_X)
            tempoTableName = DataUtil.prefix(tableName = dicOfOutputTables[t],
                                             prefix = tempoPrefix)
        # The columns to keep are different in case of street canyon zone
        columnsToKeepQuery = """b.{0}, {1} a.{2}, a.{3}
                                """.format( ID_POINT, 
                                            queryKeepY,
                                            ID_FIELD_STACKED_BLOCK,
                                            HEIGHT_FIELD)
        if t==STREET_CANYON_NAME:
            columnsToKeepQuery = """b.{0}, {1} a.{2}, a.{3}, a.{4}, a.{5}
                                    """.format( ID_POINT, 
                                                queryKeepY,
                                                ID_UPSTREAM_STACKED_BLOCK,
                                                ID_DOWNSTREAM_STACKED_BLOCK,
                                                UPSTREAM_HEIGHT_FIELD,
                                                DOWNSTREAM_HEIGHT_FIELD)
            
        query.append(""" 
            CREATE INDEX IF NOT EXISTS id_{1}_{0} ON {0} USING RTREE({1});
            CREATE TABLE {2}
                AS SELECT {4}
                FROM    {0} AS a, {3} AS b
                WHERE   a.{1} && b.{1}
                        AND ST_INTERSECTS(a.{1}, b.{1})
                        """.format( dicOfRockleZoneTable[t],
                                    GEOM_FIELD,
                                    tempoTableName,
                                    gridTable,
                                    columnsToKeepQuery))
    
    # Get the ID of the lower grid point row
    cursor.execute("""
       SELECT MAX(DISTINCT {0}) AS {0} FROM {1};
                   """.format( ID_POINT_Y,
                               gridTable))    
    idLowerGridRow = cursor.fetchall()[0][0]
    
    # For Rockle zones that needs relative point distance, extra calculation is needed
    # First creates vertical lines
    endOfQuery = """ 
        CREATE INDEX IF NOT EXISTS id_{1}_{3} ON {3} USING BTREE({1});
        CREATE INDEX IF NOT EXISTS id_{4}_{3} ON {3} USING BTREE({4});
        DROP TABLE IF EXISTS {0};
        CREATE TABLE {0} 
            AS SELECT   a.{1},
                        ST_MAKELINE(b.{2}, a.{2}) AS {2}
            FROM {3} AS a LEFT JOIN {3} AS b ON a.{1} = b.{1}
            WHERE a.{4} = 1 AND b.{4} = {5};
        CREATE INDEX IF NOT EXISTS id_{2}_{0} ON {3} USING RTREE({2});
            """.format( verticalLineTable,
                        ID_POINT_X,
                        GEOM_FIELD,
                        gridTable,
                        ID_POINT_Y,
                        idLowerGridRow)
    # Then calculates the coordinate of the upper and lower part of the zones
    # for each vertical line and last calculate the relative position of each
    # point according to the upper and lower part of the Rockle zones
    endOfQuery += ";".join(["""
        CREATE INDEX IF NOT EXISTS id_{1}_{2} ON {2} USING RTREE({1});
        DROP TABLE IF EXISTS {0}, {5};
        CREATE TABLE {0}
            AS SELECT   b.{3},
                        b.{9},
                        a.{11},
                        ST_Y(ST_GEOMETRYN(ST_INTERSECTION(a.{1}, 
                                                          ST_TOMULTILINE(b.{1}))
                                          ,2))
                            -ST_Y(ST_GEOMETRYN(ST_INTERSECTION(a.{1},
                                                               ST_TOMULTILINE(b.{1}))
                                          ,1)) AS {7},
                        ST_Y(ST_GEOMETRYN(ST_INTERSECTION(a.{1}, 
                                                          ST_TOMULTILINE(b.{1}))
                                          ,2)) AS Y_LOWER
            FROM {4} AS a, {2} AS b
            WHERE   a.{1} && b.{1} AND ST_INTERSECTS(a.{1}, b.{1});
        CREATE INDEX IF NOT EXISTS id_{3}_{0} ON {0} USING BTREE({3});
        CREATE INDEX IF NOT EXISTS id_{3}_{10} ON {10} USING BTREE({3});
        CREATE INDEX IF NOT EXISTS id_{11}_{0} ON {0} USING BTREE({11});
        CREATE INDEX IF NOT EXISTS id_{11}_{10} ON {10} USING BTREE({11});
        CREATE TABLE {5}
            AS SELECT   b.{8},
                        a.Y_LOWER-b.Y_POINT AS {6},
                        a.{7},
                        a.{9}
            FROM {0} AS a RIGHT JOIN {10} AS b
                        ON a.{3} = b.{3} AND a.{11} = b.{11}
                  """.format( DataUtil.prefix(tableName = t,
                                             prefix = prefixZoneLimits),
                              GEOM_FIELD,
                              dicOfRockleZoneTable[t],
                              ID_FIELD_STACKED_BLOCK,
                              verticalLineTable,
                              dicOfOutputTables[t],
                              DISTANCE_BUILD_TO_POINT_FIELD,
                              LENGTH_ZONE_FIELD,
                              ID_POINT,
                              HEIGHT_FIELD,
                              DataUtil.prefix(tableName = dicOfOutputTables[t],
                                              prefix = tempoPrefix),
                              ID_POINT_X)
                  for t in listTabYvalues])
    query.append(endOfQuery)
    
    # Remove intermediate tables
    query.append("""
        DROP TABLE IF EXISTS {0},{1}
                  """.format(",".join([DataUtil.prefix( tableName = dicOfOutputTables[t],
                                                        prefix = tempoPrefix)
                                             for t in listTabYvalues]),
                              ",".join([DataUtil.prefix(tableName = t,
                                                        prefix = prefixZoneLimits)
                                             for t in listTabYvalues]),
                             verticalLineTable))
    cursor.execute(";".join(query))
     
    return dicOfOutputTables