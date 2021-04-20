#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 30 14:21:04 2021

@author: Jérémy Bernard, University of Gothenburg
"""
import os
import MainCalculation
import matplotlib.colors as colors

from GlobalVariables import * 

z_ref = 10
v_ref = 2
windDirection = 50
prefix = "StreetCanyon"
meshSize = 2
dz = 2
alongWindZoneExtend = 70
crossWindZoneExtend = 10
verticalExtend = 10
inputBuildingFilename = os.path.join(prefix, "buildingSelection.shp")
# inputVegetationFilename = os.path.join(prefix, "vegetation.shp")
inputVegetationFilename = ""
tempoDirectory = "/home/decide/Téléchargements"

u, v, w, un, vn, wn, x, y, z, e, lambdaM1, buildIndex = \
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

# Convert building coordinates to a 3D multiindex object
iterables = [np.arange(0,x.size), np.arange(0,y.size), np.arange(0,z.size)]
cells = pd.Series(dtype = "float64",
                  index = pd.MultiIndex.from_product(iterables, names=('x', 'y', 'z')))
cells.loc[pd.MultiIndex.from_arrays(buildIndex, names=('x', 'y', 'z'))] = 1.

# Calculates wind speed for each cell
ws = (u**2+v**2+w**2)**0.5

# Levels to plot
levelList = [2, 8, 14, 20, 22, 23]

# Wind speed field in an (x,y) plan
nrows = 2
ncols = int(len(levelList)/nrows)
fig, ax = plt.subplots(nrows = nrows, ncols = ncols, sharex = True, sharey=True)
for k in range(0,nrows):
    for i, j in enumerate(levelList[k*ncols:ncols+k*ncols]):
        # ax[k][i].streamplot(x, y, u = u[:,:,int(j/dz)].transpose(), v = v[:,:,int(j/dz)].transpose(), density = 3)
        Q = ax[k][i].quiver(x, y, u[:,:,int(j/dz)].transpose(), v[:,:,int(j/dz)].transpose(), 
                            units = 'xy', scale = dz, headwidth = 6, headlength = 3,
                            headaxislength = 2.5)
        ax[k][i].quiverkey(Q, 0.9, 0.9, 1, r'$1 \frac{m}{s}$', labelpos='E',
                    coordinates='figure')
        # ax[k][i].set_xlim(-5,45)
        # ax[k][i].set_ylim(int(25/dz),int(75/dz))
        
        # Get buildings for the z level considered
        buildZ = cells.xs(int(j/dz), level = 2)
        
        # Set building pixels in black
        ax[k][i].pcolor(buildZ.index.unique(0)*meshSize,
                        buildZ.index.unique(1)*meshSize,
                        buildZ.unstack().transpose().values,
                        shading = "nearest",
                        alpha = 0.8)
        ax[k][i].set_title("{0} m".format(j))
        
# Wind speed field in an (y,z) plan
i_plan = int(x.size/2)
fig, ax = plt.subplots(sharex = True, sharey=True)
# ax[k][i].streamplot(x, y, u = u[:,:,j].transpose(), v = v[:,:,j].transpose(), density = 1)
Q = ax.quiver(y, z, v[i_plan,:,:].transpose(), w[i_plan,:,:].transpose(), 
                    units = 'xy', scale = dz, headwidth = 6, headlength = 3,
                    headaxislength = 2.5)
ax.quiverkey(Q, 0.9, 0.9, 1, r'$1 \frac{m}{s}$', labelpos='E',
            coordinates='figure')

buildZ = cells.xs(i_plan, level = 0)

# Set building pixels in black
ax.pcolor(  buildZ.index.unique(0)*meshSize,
            buildZ.index.unique(1)*dz,
            buildZ.unstack().transpose().values,
            shading = "nearest",
            alpha = 0.8)
# ax.set_xlim(-5,45)
# ax.set_ylim(25,75)

# Wind speed colormap
nrows = 2
ncols = int(len(levelList)/nrows)
fig, ax = plt.subplots(nrows = nrows, ncols = ncols, sharex = True, sharey=True)
for k in range(0,nrows):
    for i, j in enumerate(levelList[k*ncols:ncols+k*ncols]):
        # Set building pixels in black
        ax[k][i].pcolor(ws[:,:,int(j/dz)].transpose(), 
                        cmap = "coolwarm")
        
        # Get buildings for the z level considered
        buildZ = cells.xs(int(j/dz), level = 2)
        
        # Set building pixels in black
        ax[k][i].pcolor(buildZ.index.unique(0),
                        buildZ.index.unique(1),
                        buildZ.unstack().transpose().values,
                        shading = "nearest")
        ax[k][i].set_title("{0} m".format(j))