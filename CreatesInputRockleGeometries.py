#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 22 11:05:28 2021

@author: Jérémy Bernard, University of Gothenburg
"""
import URock.DataUtil as DataUtil
import pandas as pd
from URock.GlobalVariables import * 

def rotateGeometries(cursor, dicOfInputTables, rotateAngle):
    """ Rotates of 'rotateAngle' degrees counter-clockwise the geometries 
    of all tables from the more North-East point of the enveloppe of all
    geometries contained in the first table.

		Parameters
		_ _ _ _ _ _ _ _ _ _ 

            cursor: conn.cursor
                A cursor object, used to perform spatial SQL queries
            dicOfInputTables: dictionary of String
                Dictionary of String with type of obstacle as key and input 
                table name as value (tables containing the geometries to rotate)
            rotateAngle: float
                Counter clock-wise rotation angle (in degree)
            
		Returns
		_ _ _ _ _ _ _ _ _ _ 

            dicOfRotateTables: dictionary
                Map of initial table names as keys and rotated table names as values
            rotationCenterCoordinates: tuple of float
                x and y values of the point used as center of rotation"""
    print("Rotates geometries from {0} degrees".format(rotateAngle))
    
    # Calculate the rotation angle in radian
    rotateAngleRad = DataUtil.degToRad(rotateAngle)
    
    columnNames = {}
    # For each table to rotate
    for i, t in enumerate(dicOfInputTables.values()):
        if i == 0:
            # Get the coordinates of the center of rotation
            cursor.execute("""SELECT   ST_XMAX(ST_ENVELOPE(ST_ACCUM({0}))),
                                       ST_YMAX(ST_ENVELOPE(ST_ACCUM({0})))
                              FROM     {1}""".format(GEOM_FIELD, t))
            rotationCenterCoordinates = cursor.fetchall()[0]
            
            #Get column names and remove geometry field
            columnNames[t] = DataUtil.getColumns(cursor = cursor,
                                                 tableName = t)
            columnNames[t].remove(GEOM_FIELD)
        
    # Rotate table in one query in order to limit the number of connections
    dicOfRotateTables = {t: dicOfInputTables[t]+"_ROTATED" for t in dicOfInputTables.keys()}
    sqlRotateQueries = ["""DROP TABLE IF EXISTS {0};
                        CREATE TABLE    {0}
                            AS SELECT   ST_ROTATE({1}, {2}, {3}, {4}) AS {1},
                                        {5}
                            FROM        {6}""".format(  dicOfRotateTables[t],\
                                                        GEOM_FIELD,\
                                                        rotateAngleRad,
                                                        rotationCenterCoordinates[0],
                                                        rotationCenterCoordinates[1],
                                                        ",".join(columnNames[dicOfInputTables[t]]),
                                                        dicOfInputTables[t]) for t in dicOfRotateTables.keys()]
    cursor.execute(";".join(sqlRotateQueries))
    
    return dicOfRotateTables, rotationCenterCoordinates

def createBlocks(cursor, inputBuildings, snappingTolerance = SNAPPING_TOLERANCE):
    """ Creates blocks and stacked blocks from buildings touching each other.

		Parameters
		_ _ _ _ _ _ _ _ _ _ 

            cursor: conn.cursor
                A cursor object, used to perform spatial SQL queries
            inputBuildings: String
                Name of the table containing building geometries and height
            snappingTolerance: float, default 0.1
                Distance in meter below which two buildings are 
                considered as touching each other (m)
            
		Returns
		_ _ _ _ _ _ _ _ _ _ 

            blockTable: String
                Name of the table containing the block geometries
                (only block of touching buildings independantly of their height)
            stackedBlockTable: String
                Name of the table containing blocks considering the vertical dimension
                (only buildings having the same height are merged)"""
    print("Creates blocks and stacked blocks")
    
    # Create temporary table names (for tables that will be removed at the end of the IProcess)
    correlTable = DataUtil.postfix("correl_table")
    
    # Creates final tables
    blockTable = DataUtil.prefix("block_table")
    stackedBlockTable = DataUtil.prefix("stacked_block_table")

    # Creates the block (a method based on network - such as H2network
    # would be much more efficient)
    cursor.execute("""
       DROP TABLE IF EXISTS {0}; 
       CREATE TABLE {0} 
            AS SELECT EXPLOD_ID AS {1}, ST_SIMPLIFY(ST_NORMALIZE({2}), {5}) AS {2} 
            FROM ST_EXPLODE ('(SELECT ST_UNION(ST_ACCUM(ST_BUFFER({2},{3})))
                             AS {2} FROM {4})');
            """.format(blockTable           , ID_FIELD_BLOCK,
                        GEOM_FIELD          , snappingTolerance,
                        inputBuildings      , GEOMETRY_SIMPLIFICATION_DISTANCE))
    
    # Identify building/block relations and convert building height to integer
    cursor.execute("""
       CREATE INDEX IF NOT EXISTS idx_geom_{5} ON {5} USING RTREE({2});
       CREATE INDEX IF NOT EXISTS idx_geom_{6} ON {6} USING RTREE({2});
       DROP TABLE IF EXISTS {0};
        CREATE TABLE {0} 
                AS SELECT   a.{1}, a.{2}, CAST(a.{3} AS INT) AS {3}, b.{4}
                FROM    {5} AS a, {6} AS b
                WHERE   a.{2} && b.{2} AND ST_INTERSECTS(a.{2}, b.{2});
                   """.format(correlTable, ID_FIELD_BUILD, GEOM_FIELD, 
                               HEIGHT_FIELD, ID_FIELD_BLOCK, inputBuildings, 
                               blockTable))
    
    # Identify all possible values of height for buildings being in a more than 1 building block
    cursor.execute("""
       CREATE INDEX IF NOT EXISTS idx_geom_{0} ON {0} USING BTREE({1});
       """.format(correlTable, ID_FIELD_BLOCK))
    cursor.execute("""
       SELECT DISTINCT a.{2} 
       FROM {0} AS a RIGHT JOIN (SELECT {1}, COUNT({1}) AS NB_BUILD FROM {0} GROUP BY {1}) AS b
       ON a.{1} = b.{1} AND b.NB_BUILD > 1;
                   """.format(correlTable, ID_FIELD_BLOCK, HEIGHT_FIELD))
    listOfHeight = pd.DataFrame(cursor.fetchall()).dropna()[0].astype(int).values
    
    # Create stacked blocks according to building blocks and height
    listOfSqlQueries = ["""SELECT NULL, {2}, ST_NORMALIZE({0}) AS {0} , {4}
                            FROM ST_EXPLODE('(SELECT ST_SIMPLIFY(ST_UNION(ST_ACCUM(a.{0})),
                                                                {5}) AS {0},
                                                    a.{2} AS {2}
                                            FROM {3} AS a RIGHT JOIN (SELECT {2} 
                                                                      FROM {3}
                                                                      WHERE {1}={4}) AS b
                                            ON a.{2}=b.{2} WHERE a.{1}>={4}
                                            GROUP BY a.{2})')
                            """.format(GEOM_FIELD       , HEIGHT_FIELD, 
                                        ID_FIELD_BLOCK  , correlTable, 
                                        height_i        , GEOMETRY_SIMPLIFICATION_DISTANCE) for height_i in listOfHeight]
    cursor.execute("""
        DROP TABLE IF EXISTS {0};
        CREATE TABLE {0}({1} SERIAL, {2} INT, {3} GEOMETRY, {4} INT)
            AS {5}""".format(stackedBlockTable, ID_FIELD_STACKED_BLOCK, ID_FIELD_BLOCK,
                                GEOM_FIELD, HEIGHT_FIELD, " UNION ALL ".join(listOfSqlQueries)))
    
    if not DEBUG:
        # Drop intermediate tables
        cursor.execute("DROP TABLE IF EXISTS {0}".format(",".join([correlTable])))
                        
    return blockTable, stackedBlockTable