#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 21 11:49:12 2021

@author: Jérémy Bernard, University of Gothenburg
"""

#!/usr/bin/python
from __future__ import print_function
import os
import urllib
import DataUtil
import jaydebeapi
from GlobalVariables import *

try:
    import psycopg2
except ImportError:
    print("Module psycopg2 is missing, cannot connect to H2 Driver")
    exit(1)

# Global variables
# H2GIS_VERSION = "1.5.0"
# H2GIS_URL = H2GIS_VERSION.join(["https://github.com/orbisgis/h2gis/releases/download/v",
#                                 "/h2gis-dist-",
#                                 "-bin.zip"])
# H2GIS_UNZIPPED_NAME = "h2gis-standalone"+os.sep+"h2gis-dist-"+H2GIS_VERSION+".jar"

H2GIS_VERSION = "2.0.0"
H2GIS_URL = "https://jenkins.orbisgis.org/job/H2GIS/lastSuccessfulBuild/artifact/h2gis-dist/target/h2gis-standalone-bin.zip"
H2GIS_UNZIPPED_NAME = "h2gis-standalone"+os.sep+"h2gis-dist-"+H2GIS_VERSION+"-SNAPSHOT.jar"


def downloadH2gis(dbDirectory):
    """ Download the H2GIS spatial database management system (used for Röckle zone calculation)
        For more information about use with Python: https://github.com/orbisgis/h2gis/wiki/4.4-Use-H2GIS-with-Python

		Parameters
		_ _ _ _ _ _ _ _ _ _ 

			dbDirectory: String
				Directory where shoud be stored the H2GIS jar            
            
		Returns
		_ _ _ _ _ _ _ _ _ _ 

            None"""
    # Get the zip file name and create the local file directory
    zipFileName = H2GIS_URL.split("/")[-1]
    localH2ZipDir = (dbDirectory+os.sep+zipFileName).encode('utf-8')
    localH2JarDir = (dbDirectory+os.sep+H2GIS_UNZIPPED_NAME).encode('utf-8')
    
    # Test whether the .jar already downloaded
    if(os.path.exists(localH2ZipDir)):
        print("H2GIS version %s already downloaded" % (H2GIS_VERSION))
    else:
        print("Downloading H2GIS version %s at %s..." % (H2GIS_URL, H2GIS_VERSION))
        # Download the archive file and save it into the 'dbDirectory'
        pathAndFileArch, headNotUse = urllib.request.urlretrieve(H2GIS_URL, localH2ZipDir)
        print("H2GIS version %s downloaded !!" % (H2GIS_VERSION))
    
    # Test whether the .jar already exists
    if(os.path.exists(localH2JarDir)):
        print("H2GIS version %s already unzipped" % (H2GIS_VERSION))
    else:
        print("Unzipping H2GIS version %s..." % (H2GIS_VERSION))
        # Unzip the H2GIS archive
        DataUtil.decompressZip(dbDirectory, zipFileName)
        print("H2GIS version %s unzipped !!" % (H2GIS_VERSION))

           
def startH2gisInstance(dbDirectory, dbInstanceDir, instanceName = INSTANCE_NAME,
                       instanceId=INSTANCE_ID, instancePass = INSTANCE_PASS,
                       newDB = NEW_DB):
    """ Start an H2GIS spatial database instance (used for Röckle zone calculation)
    For more information about use with Python: https://github.com/orbisgis/h2gis/wiki/4.4-Use-H2GIS-with-Python

		Parameters
		_ _ _ _ _ _ _ _ _ _ 

			dbDirectory: String
				Directory where is stored the H2GIS jar         
            dbInstanceDir: String
                Directory where should be started the H2GIS instance
            instanceName: String, default INSTANCE_NAME
                File name used for the database
            instanceId: String, default INSTANCE_ID
                ID used to connect to the database
            instancePass: String, default INSTANCE_PASS
                password used to connect to the database
            newDB: Boolean, default NEW_DB
                Whether or not all existing 'public' tables should be deleted
                (if the DB already exists)
        
		Returns
		_ _ _ _ _ _ _ _ _ _ 

            cur: conn.cursor
                A cursor object, used to perform queries"""
    # DB extension
    dbExtension = ".mv.db"
    
    # Define where are the jar of the DB and the H2GIS instance (in absolute paths)
    localH2JarDir = dbDirectory+os.sep+H2GIS_UNZIPPED_NAME
    localH2InstanceDir = dbInstanceDir+os.sep+instanceName

    isDbExist = os.path.exists(localH2InstanceDir+dbExtension)
    
    # print the connection string we will use to connect
    print("Connecting to database\n	->%s" % (localH2InstanceDir))
    print (localH2JarDir)
    
    # get a connection, if a connect cannot be made an exception will be raised here
    conn = jaydebeapi.connect(  "org.h2.Driver",
                                "jdbc:h2:"+localH2InstanceDir+";AUTO_SERVER=TRUE",
                                [instanceId, instancePass],
                                localH2JarDir,)

    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cur = conn.cursor()
    print("Connected!\n")
    
    # If the DB already exists and if 'newDB' is set to True, delete all 'public' tables 
    if isDbExist & newDB:
        cur.execute("""SELECT TABLE_NAME 
                        FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_SCHEMA = 'PUBLIC'""")
        tableNames = [i[0] for i in cur.fetchall()]
        cur.execute("""
            DROP TABLE IF EXISTS {0}""".format(",".join(tableNames)))
            
    # Init spatial features
    cur.execute("CREATE ALIAS IF NOT EXISTS H2GIS_SPATIAL FOR \"org.h2gis.functions.factory.H2GISFunctions.load\";")
    cur.execute("CALL H2GIS_SPATIAL();")
    print("Spatial functions added!\n")
    
    return cur