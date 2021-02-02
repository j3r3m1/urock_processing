# -*- coding: utf-8 -*-
import zipfile
import os
import shutil
import errno
import numpy as np

from URock.GlobalVariables import *


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

def postfix(tableName, suffix = SUFFIX_NAME, separator = "_"):
    """ Add a suffix to an input table name
    
    Parameters
	_ _ _ _ _ _ _ _ _ _ 
		tableName : String
			Name of the input table
        suffix : String, default current datetime as string
            Suffix to add to the table name
        separator : String, default "_"
            Character to separate tableName from suffix
            
    
    Returns
	_ _ _ _ _ _ _ _ _ _ 	
		The input table name with the suffix"""
        
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