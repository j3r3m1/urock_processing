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
 This script initializes the plugin, making it known to QGIS.
"""

__author__ = 'Jérémy Bernard / University of Gothenburg'
__date__ = '2021-10-04'
__copyright__ = '(C) 2021 by Jérémy Bernard / University of Gothenburg'

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load URock class from file URock.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .urock_processing import URockPlugin
    return URockPlugin()
