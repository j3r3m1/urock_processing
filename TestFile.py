#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 30 14:21:04 2021

@author: Jérémy Bernard, University of Gothenburg
"""
import os
import MainCalculation

from GlobalVariables import * 

z_ref = 10
v_ref = 2
windDirection = 20
prefix = "StreetCanyon"
meshSize = 2
dz = 2
alongWindZoneExtend = 40
crossWindZoneExtend = 10
verticalExtend = 10
inputBuildingFilename = os.path.join(prefix, "buildingSelection.shp")
inputVegetationFilename = ""
tempoDirectory = "/home/decide/Téléchargements"

u, v, w, un, vn, wn, x, y, z, e, lambdaM1 = \
    MainCalculation.main(   z_ref = z_ref,
                            v_ref = v_ref,
                            windDirection = windDirection,
                            prefix = prefix,
                            meshSize = meshSize,
                            dz = dz,
                            alongWindZoneExtend = alongWindZoneExtend,
                            crossWindZoneExtend = crossWindZoneExtend,
                            verticalExtend = verticalExtend,
                            inputBuildingFilename = inputBuildingFilename,
                            inputVegetationFilename = inputVegetationFilename,
                            tempoDirectory = tempoDirectory)

levelList = [1, 4, 6, 8, 10, 11]
nrows = 2
ncols = int(len(levelList)/nrows)
fig, ax = plt.subplots(nrows = nrows, ncols = ncols, sharex = True, sharey=True)
for k in range(0,nrows):
    for i, j in enumerate(levelList[k*ncols:ncols+k*ncols]):
        # ax[k][i].streamplot(x, y, u = u[:,:,j].transpose(), v = -v[:,:,j].transpose(), density = 1)
        Q = ax[k][i].quiver(x, y, u[:,:,j].transpose(), -v[:,:,j].transpose(), 
                            units = 'xy', scale = 1.5)
        ax[k][i].quiverkey(Q, 0.9, 0.9, 1, r'$1 \frac{m}{s}$', labelpos='E',
                    coordinates='figure')
        ax[k][i].set_title("{0} m".format(j))
        ax[k][i].set_xlim(-5,45)
        ax[k][i].set_ylim(25,75)