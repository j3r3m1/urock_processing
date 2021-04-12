#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 30 14:21:04 2021

@author: Jérémy Bernard, University of Gothenburg
"""
import os
import MainCalculation

from GlobalVariables import * 

u, v, w, un, vn, wn, x, y, z, e, lambdaM1 = \
    MainCalculation.main(   z_ref = 10,
                            v_ref = 2,
                            windDirection = 270,
                            prefix = "SimpleBuilding",
                            meshSize = 1,
                            dz = 1,
                            alongWindZoneExtend = 40,
                            crossWindZoneExtend = 10,
                            verticalExtend = 10,
                            inputBuildingFilename = os.path.join("SimpleBuilding", "buildingSelection.shp"),
                            inputVegetationFilename = "",
                            tempoDirectory = "/home/decide/Téléchargements")


z_ref = 10
v_ref = 2
windDirection = 270
prefix = "SimpleBuilding"
meshSize = 1
dz = 1
alongWindZoneExtend = 40
crossWindZoneExtend = 10
verticalExtend = 10
inputBuildingFilename = os.path.join("SimpleBuilding", "buildingSelection.shp")
inputVegetationFilename = ""
tempoDirectory = "/home/decide/Téléchargements"

levelList = [2, 4, 6, 8, 10, 11]
nrows = 2
ncols = int(len(levelList)/nrows)
fig, ax = plt.subplots(nrows = nrows, ncols = ncols, sharex = True, sharey=True)
for k in range(0,nrows):
    for i, j in enumerate(levelList[k*ncols:ncols+k*ncols]):
        Q = ax[k][i].quiver(x, y, u[:,:,j].transpose(), -v[:,:,j].transpose(), 
                            units = 'xy', scale = 1.5)
        ax[k][i].quiverkey(Q, 0.9, 0.9, 1, r'$1 \frac{m}{s}$', labelpos='E',
                   coordinates='figure')
        ax[k][i].set_title("{0} m".format(j))
        ax[k][i].set_xlim(-5,45)
        ax[k][i].set_ylim(25,75)