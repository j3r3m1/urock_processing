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
windDirection = 14
prefix = "SimpleBuilding"
meshSize = 2
dz = 2
alongWindZoneExtend = 5
crossWindZoneExtend = 10
verticalExtend = 5
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

# -----------------------------------------------------------------------------------
# GRAPHIC CHARACTERISTICS -----------------------------------------------------------
# -----------------------------------------------------------------------------------
# Arrow charac
headwidth = 3
headlength = 1.5
headaxislength = 1.5

# Z level to plot
levelList = [3, 8, 14, 20, 22, 23]

# Number of row in the subplots
nrows = 2

# -----------------------------------------------------------------------------------
# POST-PROCESSING -------------------------------------------------------------------
# -----------------------------------------------------------------------------------
# Convert building coordinates to a 3D multiindex object
iterables = [np.arange(0,x.size), np.arange(0,y.size), np.arange(0,z.size)]
cells = pd.Series(dtype = "float64",
                  index = pd.MultiIndex.from_product(iterables, names=('x', 'y', 'z')))
cells.loc[pd.MultiIndex.from_arrays(buildIndex, names=('x', 'y', 'z'))] = 1.

# Calculates wind speed for each cell
ws = (u**2+v**2+w**2)**0.5

# -----------------------------------------------------------------------------------
# PLOT FIGURES ----------------------------------------------------------------------
# -----------------------------------------------------------------------------------
# 1. Wind field in an (X,Y) plan ----------------------------------------------
# -----------------------------------------------------------------------------------   
ncols = int(len(levelList)/nrows)
fig, ax = plt.subplots(nrows = nrows, ncols = ncols, sharex = True, sharey=True)
for k in range(0,nrows):
    for i, lev in enumerate(levelList[k*ncols:ncols+k*ncols]):
        n_lev = int((lev+dz/2)/dz)
        # ax[k][i].streamplot(x, y, u = u[:,:,int(j/dz)].transpose(), v = v[:,:,int(j/dz)].transpose(), density = 3)
        Q = ax[k][i].quiver(x, y, u[:,:,n_lev].transpose(), v[:,:,n_lev].transpose(), 
                            units = 'xy', scale = dz, headwidth = 6, headlength = 3,
                            headaxislength = 2.5)
        ax[k][i].quiverkey(Q, 0.9, 0.9, 1, r'$1 \frac{m}{s}$', labelpos='E',
                    coordinates='figure')
        # ax[k][i].set_xlim(-5,45)
        # ax[k][i].set_ylim(int(25/dz),int(75/dz))
        
        # Get buildings for the z level considered
        buildZ = cells.xs(n_lev, level = 2)
        
        # Set building pixels in color
        ax[k][i].pcolor(buildZ.index.unique(0)*meshSize,
                        buildZ.index.unique(1)*meshSize,
                        buildZ.unstack().transpose().values,
                        shading = "nearest",
                        alpha = 0.8)
        ax[k][i].set_title("{0} m".format(n_lev*dz-float(dz)/2))
        
# -----------------------------------------------------------------------------------    
# 2. Wind speed in an (X,Y) plan ----------------------------------------------------
# -----------------------------------------------------------------------------------
ncols = int(len(levelList)/nrows)
fig, ax = plt.subplots(nrows = nrows, ncols = ncols, sharex = True, sharey=True)
for k in range(0,nrows):
    for i, lev in enumerate(levelList[k*ncols:ncols+k*ncols]):
        n_lev = int((lev+dz/2)/dz)
        # Set building pixels in black
        pcol = ax[k][i].pcolor(ws[:,:,n_lev].transpose(), 
                        cmap = "coolwarm")
        
        # Get buildings for the z level considered
        buildZ = cells.xs(n_lev, level = 2)
        
        # Set building pixels in black
        ax[k][i].pcolor(buildZ.index.unique(0),
                        buildZ.index.unique(1),
                        buildZ.unstack().transpose().values,
                        shading = "nearest")
        ax[k][i].set_title("{0} m".format(n_lev*dz-float(dz)/2))
        plt.colorbar(pcol, ax = ax[k][i])

# -----------------------------------------------------------------------------------    
# 3. Wind field in an (Y,Z) plan ----------------------------------------------
# -----------------------------------------------------------------------------------   
i_plan = int(x.size/2)
fig, ax = plt.subplots(sharex = True, sharey=True)
# ax[k][i].streamplot(x, y, u = u[:,:,j].transpose(), v = v[:,:,j].transpose(), density = 1)
Q = ax.quiver(y, z-float(dz)/2, v[i_plan,:,:].transpose(), w[i_plan,:,:].transpose(), 
                    units = 'xy', scale = dz, headwidth = 3, headlength = 1.5,
                    headaxislength = 1.5)
ax.quiverkey(Q, 0.9, 0.9, 1, r'$1 \frac{m}{s}$', labelpos='E',
            coordinates='figure')

buildZ = cells.xs(i_plan, level = 0)

# Set building pixels in color
ax.pcolor(  buildZ.index.unique(0)*meshSize,
            buildZ.index.unique(1)*dz-float(dz)/2,
            buildZ.unstack().transpose().values,
            shading = "nearest",
            alpha = 0.8)
# ax.set_xlim(-5,45)
# ax.set_ylim(25,75)

