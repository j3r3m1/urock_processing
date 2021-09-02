# -*- coding: utf-8 -*-
import zipfile
import os
import shutil
import errno
import numpy as np

from GlobalVariables import *


def decompressZip(dirPath, inputFileName, outputFileBaseName=None, 
                  deleteZip = False):
    """
    Decompress zip file.

    Parameters
    _ _ _ _ _ _ _ _ _ _ 
        dirPath: String
            Directory path where is located the zip file    
        inputFileName: String
            Name of the file to unzip (with .zip at the end)
        outputFileBaseName: String
            Base name of the file to unzip (without extension)
        deleteZip: boolean, default False
            Whether or not the input zip file should be removed

    Returns
    -------
        None
    """
    print("Start decompressing zip file")
    
    with open(os.path.join(dirPath,inputFileName), "rb") as zipsrc:
        zfile = zipfile.ZipFile(zipsrc)
        for member in zfile.infolist():
            print(member.filename+" is being decompressed" )
            if outputFileBaseName is None:
                target_path=os.path.join(dirPath,member.filename)
            else:
                # Initialize output file path
                target_path = os.path.join(dirPath, outputFileBaseName)
                extension = "." + member.filename.split(".")[-1]
                target_path+=extension
            
            # Create a folder if needed
            if target_path.endswith('/'):  # folder entry, create
                try:
                    os.makedirs(target_path)
                except (OSError, IOError) as err:
                    # Windows may complain if the folders already exist
                    if err.errno != errno.EEXIST:
                        raise
                continue
            with open(target_path, 'wb') as outfile, zfile.open(member) as infile:
                shutil.copyfileobj(infile, outfile)
    
    return None

def degToRad(angleDeg, origin = 0, direction = "CLOCKWISE"):
    """Convert angle arrays from degrees to radian.
    
    Parameters
	_ _ _ _ _ _ _ _ _ _ 
		angleDeg : float
			Angle in degrees
		origin : float, default 0
			Origin of the input degree coordinates (given in a reference North clockwise coordinate system)
		direction : {"CLOCKWISE", "COUNTER-CLOCKWISE"}, default "CLOCKWISE"
			Direction where go the input coordinate
    
    Returns
	_ _ _ _ _ _ _ _ _ _ 	
		angle in radian (trigonometric reference).
    """
    if direction == "CLOCKWISE":
        d = 1
    if direction == "COUNTER-CLOCKWISE":
        d = -1
    
    return (angleDeg+d*origin)*np.pi/180

def postfix(tableName, suffix = None, separator = "_"):
    """ Add a suffix to an input table name
    
    Parameters
	_ _ _ _ _ _ _ _ _ _ 
		tableName : String
			Name of the input table
        suffix : String, default None (then current datetime is used as string)
            Suffix to add to the table name
        separator : String, default "_"
            Character to separate tableName from suffix
            
    
    Returns
	_ _ _ _ _ _ _ _ _ _ 	
		The input table name with the suffix"""
    if suffix is None:
        suffix = datetime.now().strftime("%Y%m%d%H%M%S")
    
    return tableName+separator+suffix

def prefix(tableName, prefix = PREFIX_NAME, separator = "_"):
    """ Add a suffix to an input table name
    
    Parameters
	_ _ _ _ _ _ _ _ _ _ 
		tableName : String
			Name of the input table
        prefix : String
            Prefix to add to the table name
        separator : String, default "_"
            Character to separate prefix from tableName 
    
    Returns
	_ _ _ _ _ _ _ _ _ _ 	
		The input table name with the prefix"""
        
    return prefix+separator+tableName

def getColumns(cursor, tableName):
    """ Get the column name of a table into a list
    
    Parameters
	_ _ _ _ _ _ _ _ _ _ 
        cursor: conn.cursor
            A cursor object, used to perform spatial SQL queries
		tableName : String
			Name of the input table
    
    Returns
	_ _ _ _ _ _ _ _ _ _ 	
		columnNames: list
            A list of the table column names"""
    cursor.execute("""SELECT * FROM {0}""".format(tableName))
    columnNames = [info[0] for info in cursor.description]
    
    return columnNames

def saveTable(cursor, tableName, filedir, delete):
    """ Save a table in .geojson or .shp
    
    Parameters
	_ _ _ _ _ _ _ _ _ _ 
        cursor: conn.cursor
            A cursor object, used to perform spatial SQL queries
		tableName : String
			Name of the table to save
        filedir: String
            Directory (including filename and extension) of the file where to 
            store the table
        delete: Boolean, default False
            Whether or not the file is delete if exist
    
    Returns
	_ _ _ _ _ _ _ _ _ _ 	
		None"""
    # Get extension
    extension = filedir.split(".")[-1]
    
    # Define the H2GIS function depending on extension
    if extension.upper() == "GEOJSON":
        h2_function = "GEOJSONWRITE"
    elif extension.upper() == "SHP":
        h2_function = "SHPWRITE"
    else:
        print("The extension should be .geojson or .shp")
    
    # Delete files
    if delete and os.path.isfile(filedir):
        os.remove(filedir)
        if extension.upper() == "SHP":
            filedirWithoutExt = filedir.split(".")[0]
            os.remove(filedirWithoutExt+".dbf")
            os.remove(filedirWithoutExt+".shx")
            if os.path.isfile(filedir+".prj"):
                os.remove(filedirWithoutExt+".prj")
                
    # Write files
    cursor.execute("""CALL {0}('{1}','{2}')""".format(h2_function,
                                                      filedir,
                                                      tableName))
    
    return None

def readFunction(extension):
    """ Return the name of the right H2GIS function to use depending of the file extension
    
    Parameters
	_ _ _ _ _ _ _ _ _ _ 
        extension: String
            Extension of the vector file (shp or geojson)
    
    Returns
	_ _ _ _ _ _ _ _ _ _ 	
		h2gisFunctionName: String
            Return the name of the H2GIS function to use"""
    if extension.lower() == "shp":
        return "SHPREAD"
    elif extension.lower() == "geojson":
        return "GEOJSONREAD"
    
def createIndex(tableName, fieldName, isSpatial):
    """ Return the SQL query needed to create an index on a given field of a
    given table. The index should be indicated as spatial if the field is
    a geometry field.
    
    Parameters
	_ _ _ _ _ _ _ _ _ _ 
        tableName: String
            Name of the table
        fieldName: String
            Name of the field the index will be created on
        isSpatial: boolean
            Whether or not the index is a spatial index (should be True if
                                                         the field is a geometry field)
    
    Returns
	_ _ _ _ _ _ _ _ _ _ 	
		query: String
            Return the SQL query needed to create the index"""
    spatialKeyWord = ""
    if isSpatial:
        spatialKeyWord = " SPATIAL "
    query = "CREATE {0} INDEX IF NOT EXISTS id_{1}_{2} ON {2}({1});".format(spatialKeyWord,
                                                                           fieldName,
                                                                           tableName)
    return query