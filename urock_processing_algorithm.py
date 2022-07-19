# -*- coding: utf-8 -*-

"""
/***************************************************************************
 URock
                                 A QGIS plugin
 This plugin calculates wind field in an urban context
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-10-04
        copyright            : (C) 2021 by Jérémy Bernard / University of Gothenburg
        email                : jeremy.bernard@zaclys.net
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Jérémy Bernard / University of Gothenburg'
__date__ = '2021-10-04'
__copyright__ = '(C) 2021 by Jérémy Bernard / University of Gothenburg'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterMatrix,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterString,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterBoolean,
                       QgsRasterLayer,
                       QgsVectorLayer,
                       QgsProject,
                       QgsProcessingContext,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFile)
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.utils import iface
from pathlib import Path
import subprocess
import pandas as pd

from . import DataUtil
try:
    path_pybin = DataUtil.locate_py()
    subprocess.check_call([str(path_pybin), "-m", "pip", "install", "jaydebeapi"])
    import jaydebeapi
except Exception:
    QMessageBox.critical(None, 'Error', "'jaydebeapi' Python package is missing, cannot connect to H2 Driver")
    pass

from . import MainCalculation
from .GlobalVariables import *
from .H2gisConnection import getJavaDir, setJavaDir, saveJavaDir



class URockAlgorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    # Input variables
    JAVA_PATH = "JAVA_PATH"
    BUILDING_TABLE_NAME = 'BUILDINGS'
    VEGETATION_TABLE_NAME = "VEGETATION"
    INPUT_WIND_HEIGHT = "INPUT_WIND_HEIGHT"
    INPUT_WIND_SPEED = "INPUT_WIND_SPEED"
    INPUT_WIND_DIRECTION = "INPUT_WIND_DIRECTION"
    HORIZONTAL_RESOLUTION = "HORIZONTAL_RESOLUTION"
    VERTICAL_RESOLUTION = "VERTICAL_RESOLUTION"
    ID_FIELD_BUILD = "ID_FIELD_BUILD"
    HEIGHT_FIELD_BUILD = "HEIGHT_FIELD_BUILD"
    ID_FIELD_VEG = "ID_FIELD_VEG"
    VEGETATION_CROWN_BASE_HEIGHT = "VEGETATION_CROWN_BASE_HEIGHT"
    VEGETATION_CROWN_TOP_HEIGHT = "VEGETATION_CROWN_TOP_HEIGHT"
    ATTENUATION_FIELD = "ATTENUATION_FIELD"
    PREFIX = "PREFIX"
    WIND_HEIGHT = "WIND_HEIGHT"
    RASTER_OUTPUT = "RASTER_OUTPUT"
    INPUT_PROFILE_TYPE = "INPUT_PROFILE_TYPE"
    INPUT_PROFILE_FILE = "INPUT_PROFILE_FILE"
    LIST_OF_PROFILES = pd.Series(['power', 'log', 'urban', 'user'])

    # Output variables    
    OUTPUT_DIRECTORY = "UROCK_OUTPUT"
    OUTPUT_FILENAME = "OUTPUT_FILENAME"
    SAVE_RASTER = "SAVE_RASTER"
    SAVE_VECTOR = "SAVE_VECTOR"
    SAVE_NETCDF = "SAVE_NETCDF"
    LOAD_OUTPUT = "LOAD_OUTPUT"
    
    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        # Get the plugin directory to save some useful files
        plugin_directory = self.plugin_dir = os.path.dirname(__file__)
        
        # Get the default value of the Java environment path if already exists
        javaDirDefault = getJavaDir(plugin_directory)
        
        # Inform the user that the Java version should be 64 bits
        if "Program Files (x86)" in javaDirDefault:
            iface.ValueError(""""Only a 32 bits version of Java has been found \
                             on your computer. Please consider installing Java 64 bits.""")
        else:
            # Set a Java dir if not exist and save it into a file in the plugin repository
            setJavaDir(javaDirDefault)
            saveJavaDir(javaPath = javaDirDefault,
                        pluginDirectory = plugin_directory)
        
        # We add the input parameters
        # First the layers used as input and output
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.BUILDING_TABLE_NAME,
                self.tr('Building polygons'),
                [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(
            QgsProcessingParameterField(
                self.HEIGHT_FIELD_BUILD,
                self.tr('Building height field'),
                None,
                self.BUILDING_TABLE_NAME,
                QgsProcessingParameterField.Numeric))
        self.addParameter(
            QgsProcessingParameterField(
                self.ID_FIELD_BUILD,
                self.tr('Building ID field'),
                None,
                self.BUILDING_TABLE_NAME,
                QgsProcessingParameterField.Numeric,
                optional=True))
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.VEGETATION_TABLE_NAME,
                self.tr('Vegetation polygons'),
                [QgsProcessing.TypeVectorPolygon],
                optional=True))
        self.addParameter(
            QgsProcessingParameterField(
                self.VEGETATION_CROWN_TOP_HEIGHT,
                self.tr('Vegetation crown top height field'),
                None,
                self.VEGETATION_TABLE_NAME,
                QgsProcessingParameterField.Numeric,
                optional = True))
        self.addParameter(
            QgsProcessingParameterField(
                self.VEGETATION_CROWN_BASE_HEIGHT,
                self.tr('Vegetation crown base height field'),
                None,
                self.VEGETATION_TABLE_NAME,
                QgsProcessingParameterField.Numeric,
                optional = True))
        self.addParameter(
            QgsProcessingParameterField(
                self.ATTENUATION_FIELD,
                self.tr('Vegetation wind attenuation factor'),
                None,
                self.VEGETATION_TABLE_NAME,
                QgsProcessingParameterField.Numeric,
                optional = True))
        self.addParameter(
            QgsProcessingParameterField(
                self.ID_FIELD_VEG,
                self.tr('Vegetation ID field'),
                None,
                self.VEGETATION_TABLE_NAME,
                QgsProcessingParameterField.Numeric,
                optional = True))


        # Then the informations related to calculation
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_PROFILE_FILE,
                self.tr('Vertical wind profile file (.csv)'),
                defaultValue = '',
                extension='csv',
                optional = True))
        self.addParameter(
           QgsProcessingParameterEnum(
               self.INPUT_PROFILE_TYPE, 
               self.tr('Vertical wind profile type'),
               self.LIST_OF_PROFILES.values,
               defaultValue=0,
               optional = True))
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_WIND_HEIGHT,
                self.tr('Height of the reference wind speed (m)'),
                QgsProcessingParameterNumber.Double,
                10,
                True))
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_WIND_SPEED,
                self.tr('Wind speed at the reference height (m/s)'),
                QgsProcessingParameterNumber.Double,
                2,
                True))
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_WIND_DIRECTION,
                self.tr('Wind direction (° clock-wise from North)'),
                QgsProcessingParameterNumber.Double,
                45,
                False))
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.RASTER_OUTPUT,
                self.tr('Raster to use as output'), 
                None,
                optional = True))
        self.addParameter(
            QgsProcessingParameterNumber(
                self.HORIZONTAL_RESOLUTION,
                self.tr('Horizontal resolution (m)'),
                QgsProcessingParameterNumber.Integer,
                2,
                optional = True))
        self.addParameter(
            QgsProcessingParameterNumber(
                self.VERTICAL_RESOLUTION,
                self.tr('Vertical resolution (m)'),
                QgsProcessingParameterNumber.Integer,
                2,
                False))


        # We add several output parameters
        self.addParameter(
            QgsProcessingParameterString(
                self.WIND_HEIGHT,
                self.tr('Output wind height(s) (m) - if several values, separated by ","'),
                defaultValue = "1.5",
                optional = False))
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT_DIRECTORY,
                self.tr('Directory to save the outputs')))
        self.addParameter(
            QgsProcessingParameterString(
                self.OUTPUT_FILENAME,
                self.tr('String used as output file base name'),
                "urock_output",
                False))
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SAVE_RASTER,
                self.tr("Save 2D wind speed as raster file(s)"),
                defaultValue=False))
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SAVE_VECTOR,
                self.tr("Save 2D wind field as vector file(s)"),
                defaultValue=False))
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SAVE_NETCDF,
                self.tr("Save 3D wind field in a NetCDF file"),
                defaultValue=False))
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.LOAD_OUTPUT,
                self.tr("Open output file after running algorithm"),
                defaultValue=False))        
        
        # Optional parameters
        self.addParameter(
            QgsProcessingParameterString(
                self.PREFIX,
                self.tr('String to prefix the output from this calculation'),
                "",
                False,
                True))
        self.addParameter(
            QgsProcessingParameterString(
                self.JAVA_PATH,
                self.tr('Java environment path (should be set automatically'),
                javaDirDefault,
                False,
                False)) 

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        # Get the plugin directory to save some useful files
        plugin_directory = self.plugin_dir = os.path.dirname(__file__)
        
        # Defines inputs
        javaEnvVar = self.parameterAsString(parameters, self.JAVA_PATH, context)
        z_ref = self.parameterAsDouble(parameters, self.INPUT_WIND_HEIGHT, context)
        v_ref = self.parameterAsDouble(parameters, self.INPUT_WIND_SPEED, context)
        windDirection = self.parameterAsDouble(parameters, self.INPUT_WIND_DIRECTION, context)
        meshSize = self.parameterAsInt(parameters, self.HORIZONTAL_RESOLUTION, context)
        dz = self.parameterAsInt(parameters, self.VERTICAL_RESOLUTION, context)
        profileType = self.LIST_OF_PROFILES.loc[self.parameterAsInt(parameters, self.INPUT_PROFILE_TYPE, context)]
        profileFile = self.parameterAsString(parameters, self.INPUT_PROFILE_FILE, context)
        
        # Get building layer and then file directory
        inputBuildinglayer = self.parameterAsVectorLayer(parameters, self.BUILDING_TABLE_NAME, context)
        build_file = str(inputBuildinglayer.dataProvider().dataSourceUri())
        if build_file.count("|layername") == 1:
            build_file = build_file.split("|layername")[0]
        srid_build = inputBuildinglayer.crs().postgisSrid()

        # Get vegetation layer if exists, check that it has the same SRID as building layer
        # and then get the file directory of the layer
        inputVegetationlayer = self.parameterAsVectorLayer(parameters, self.VEGETATION_TABLE_NAME, context)
        if inputVegetationlayer:
            veg_file = str(inputVegetationlayer.dataProvider().dataSourceUri())
            if veg_file.count("|layername") == 1:
                veg_file = veg_file.split("|layername")[0]
            srid_veg = inputVegetationlayer.crs().postgisSrid()
            if srid_build != srid_veg:
                feedback.pushInfo('Coordinate system of input building layer and vegetation layer differ!')
        else:
            veg_file = None
            srid_veg = None
        outputRaster = self.parameterAsRasterLayer(parameters, self.RASTER_OUTPUT, context)
        idBuild = self.parameterAsString(parameters, self.ID_FIELD_BUILD, context)
        heightBuild = self.parameterAsString(parameters, self.HEIGHT_FIELD_BUILD, context)
        idVeg = self.parameterAsString(parameters, self.ID_FIELD_VEG, context)
        baseHeightVeg = self.parameterAsString(parameters, self.VEGETATION_CROWN_BASE_HEIGHT, context)
        topHeightVeg = self.parameterAsString(parameters, self.VEGETATION_CROWN_TOP_HEIGHT, context)
        attenuationVeg = self.parameterAsString(parameters, self.ATTENUATION_FIELD, context)
        prefix = self.parameterAsString(parameters, self.PREFIX, context)
        
        # Defines outputs
        z_out = self.parameterAsString(parameters, self.WIND_HEIGHT, context).split(",")
        z_out = [float(i) for i in z_out]
        outputDirectory = self.parameterAsString(parameters, self.OUTPUT_DIRECTORY, context)
        outputFilename = self.parameterAsString(parameters, self.OUTPUT_FILENAME, context)
        saveRaster = self.parameterAsBool(parameters, self.SAVE_RASTER, context)
        saveVector = self.parameterAsBool(parameters, self.SAVE_VECTOR, context)
        saveNetcdf = self.parameterAsBool(parameters, self.SAVE_NETCDF, context)
        loadOutput = self.parameterAsBool(parameters, self.LOAD_OUTPUT, context)

        # Creates the output folder if it does not exist
        if not os.path.exists(outputDirectory):
            if os.path.exists(Path(outputDirectory).parent.absolute()):
                os.mkdir(outputDirectory)
            else:
                feedback.pushInfo('The output directory does not exist, neither its parent directory')

        # If there is an output raster, need to get some of its parameters
        if outputRaster:
            if inputBuildinglayer.crs().postgisSrid() != outputRaster.crs().postgisSrid():
                feedback.pushInfo('Coordinate system of input building layer and output Raster layer differ!')
            xres = (outputRaster.extent().xMaximum() - outputRaster.extent().xMinimum()) / outputRaster.width()
            yres = (outputRaster.extent().yMaximum() - outputRaster.extent().yMinimum()) / outputRaster.height()               
            # If there is a raster and no meshSize, take the mean of x and y raster resolution
            if not meshSize:
                meshSize = float(xres + yres) / 2
        elif not meshSize:
            feedback.pushInfo('You should either specify an output raster or a horizontal mesh size')
            
        # Make the calculations
        u, v, w, u0, v0, w0, x, y, z, buildingCoordinates, cursor, gridName,\
        rotationCenterCoordinates, verticalWindProfile, dicVectorTables,\
        netcdf_path, net_cdf_path_ini = \
            MainCalculation.main(javaEnvironmentPath = javaEnvVar,
                                 pluginDirectory = plugin_directory,
                                 outputFilePath = outputDirectory,
                                 outputFilename = outputFilename,
                                 buildingFilePath = build_file,
                                 vegetationFilePath = veg_file,
                                 srid = srid_build,
                                 z_ref = z_ref,
                                 v_ref = v_ref,
                                 windDirection = windDirection,
                                 prefix = prefix,
                                 meshSize = meshSize,
                                 dz = dz,
                                 alongWindZoneExtend = ALONG_WIND_ZONE_EXTEND,
                                 crossWindZoneExtend = CROSS_WIND_ZONE_EXTEND,
                                 verticalExtend = VERTICAL_EXTEND,
                                 cadTriangles = "",
                                 cadTreesIntersection = "",
                                 tempoDirectory = TEMPO_DIRECTORY,
                                 onlyInitialization = ONLY_INITIALIZATION,
                                 maxIterations = MAX_ITERATIONS,
                                 thresholdIterations = THRESHOLD_ITERATIONS,
                                 idFieldBuild = idBuild,
                                 buildingHeightField = heightBuild,
                                 vegetationBaseHeight = baseHeightVeg,
                                 vegetationTopHeight = topHeightVeg,
                                 idVegetation = idVeg,
                                 vegetationAttenuationFactor = attenuationVeg,
                                 saveRockleZones = SAVE_ROCKLE_ZONES,
                                 outputRaster = outputRaster,
                                 feedback = feedback,
                                 saveRaster = saveRaster,
                                 saveVector = saveVector,
                                 saveNetcdf = saveNetcdf,
                                 z_out = z_out,
                                 debug = DEBUG,
                                 profileType = profileType,
                                 verticalProfileFile = profileFile)
        
        # Load files into QGIS if user set it
        if loadOutput:
            for z_i in z_out:
                if saveVector:
                    loadedVector = \
                        QgsVectorLayer(os.path.join(outputDirectory, 
                                                    "z{0}".format(str(z_i).replace(".","_")),
                                                    outputFilename\
                                                    + OUTPUT_VECTOR_EXTENSION),
                                       "Wind at {0} m".format(z_i),
                                       "ogr")
                    if not loadedVector.isValid():
                        feedback.pushInfo("Vector layer failed to load!")
                        break
                    else:
                        loadedVector.loadNamedStyle(os.path.join(plugin_directory,\
                                                                 "Resources",
                                                                 VECTOR_STYLE_FILENAME), True)
                        context.addLayerToLoadOnCompletion(loadedVector.id(),
                                                           QgsProcessingContext.LayerDetails("Wind at {0} m".format(z_i),
                                                                                             QgsProject.instance(),
                                                                                             ''))
                        context.temporaryLayerStore().addMapLayer(loadedVector)
                        
                if saveRaster:
                    loadedRaster = \
                        QgsRasterLayer(os.path.join(outputDirectory, 
                                                    "z{0}".format(str(z_i).replace(".","_")),
                                                    outputFilename\
                                                    + WIND_SPEED + OUTPUT_RASTER_EXTENSION),
                                       "Wind speed at {0} m".format(z_i),
                                       "gdal")
                    if not loadedRaster.isValid():
                        feedback.pushInfo("Raster layer failed to load!")
                        break
                    else:
                        context.addLayerToLoadOnCompletion(loadedRaster.id(),
                                                           QgsProcessingContext.LayerDetails("Wind speed at {0} m".format(z_i),
                                                                                             QgsProject.instance(),
                                                                                             ''))
                        context.temporaryLayerStore().addMapLayer(loadedRaster)
        # Return the output file names
        return {self.OUTPUT_DIRECTORY: outputDirectory,
                self.OUTPUT_FILENAME: outputFilename}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'urock'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return ''

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return URockAlgorithm()
