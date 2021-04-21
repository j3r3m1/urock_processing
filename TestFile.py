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
windDirection = 350
prefix = "StreetCanyon"
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
levelList = [1]

# Number of row in the subplots
nrows = 1

# Initial or solved wind field
initialField = False

# -----------------------------------------------------------------------------------
# POST-PROCESSING -------------------------------------------------------------------
# -----------------------------------------------------------------------------------
#
if initialField:
    u_plot = un
    v_plot = vn
    w_plot = wn
else:
    u_plot = u
    v_plot = v
    w_plot = w
# Convert building coordinates to a 3D multiindex object
iterables = [np.arange(0,x.size), np.arange(0,y.size), np.arange(0,z.size)]
cells = pd.Series(dtype = "float64",
                  index = pd.MultiIndex.from_product(iterables, names=('x', 'y', 'z')))
cells.loc[pd.MultiIndex.from_arrays(buildIndex, names=('x', 'y', 'z'))] = 1.

# Calculates wind speed for each cell
ws_plot = (u_plot**2+v_plot**2+w_plot**2)**0.5

# -----------------------------------------------------------------------------------
# PLOT FIGURES ----------------------------------------------------------------------
# -----------------------------------------------------------------------------------
# 1. Wind field in an (X,Y) plan ----------------------------------------------
# -----------------------------------------------------------------------------------   
ncols = int(len(levelList)/nrows)
fig, ax = plt.subplots(nrows = nrows, ncols = ncols, sharex = True, sharey=True)
for i in range(0,nrows):
    for j, lev in enumerate(levelList[i*ncols:ncols+i*ncols]):
        if nrows>1:
            ax_ij = ax[i]
            if ncols>1:
                ax_ij = ax[i][j]
        elif ncols>1:
            ax_ij = ax[j]
        else:
            ax_ij = ax
        n_lev = int((lev+dz/2)/dz)
        # ax_ij.streamplot(x, y, u = u[:,:,int(j/dz)].transpose(), v = v[:,:,int(j/dz)].transpose(), density = 3)
        Q = ax_ij.quiver(x, y, u_plot[:,:,n_lev].transpose(), v_plot[:,:,n_lev].transpose(), 
                            units = 'xy', scale = dz, headwidth = 6, headlength = 3,
                            headaxislength = 2.5)
        ax_ij.quiverkey(Q, 0.9, 0.9, 1, r'$1 \frac{m}{s}$', labelpos='E',
                    coordinates='figure')
        ax_ij.set_xlim(-14,78)
        ax_ij.set_ylim(132,188)
        
        # Get buildings for the z level considered
        buildZ = cells.xs(n_lev, level = 2)
        
        # Set building pixels in color
        ax_ij.pcolor(buildZ.index.unique(0)*meshSize,
                        buildZ.index.unique(1)*meshSize,
                        buildZ.unstack().transpose().values,
                        shading = "nearest",
                        alpha = 0.8)
        ax_ij.set_title("{0} m".format(n_lev*dz-float(dz)/2))
        
# -----------------------------------------------------------------------------------    
# 2. Wind speed in an (X,Y) plan ----------------------------------------------------
# -----------------------------------------------------------------------------------
ncols = int(len(levelList)/nrows)
fig, ax = plt.subplots(nrows = nrows, ncols = ncols, sharex = True, sharey=True)
for i in range(0,nrows):
    for j, lev in enumerate(levelList[i*ncols:ncols+k*ncols]):
        if nrows>1:
            ax_ij = ax[i]
            if ncols>1:
                ax_ij = ax[i][j]
        elif ncols>1:
            ax_ij = ax[j]
        else:
            ax_ij = ax
        n_lev = int((lev+dz/2)/dz)
        # Set building pixels in black
        pcol = ax_ij.pcolor(ws_plot[:,:,n_lev].transpose(), 
                        cmap = "coolwarm")
        
        # Get buildings for the z level considered
        buildZ = cells.xs(n_lev, level = 2)
        
        # Set building pixels in black
        ax_ij.pcolor(buildZ.index.unique(0),
                        buildZ.index.unique(1),
                        buildZ.unstack().transpose().values,
                        shading = "nearest")
        ax_ij.set_title("{0} m".format(n_lev*dz-float(dz)/2))
        plt.colorbar(pcol, ax = ax_ij)

# -----------------------------------------------------------------------------------    
# 3. Wind field in an (Y,Z) plan ----------------------------------------------
# -----------------------------------------------------------------------------------   
i_plan = int(x.size/2)
fig, ax = plt.subplots(sharex = True, sharey=True)
# ax.streamplot(x, z-float(dz)/2, v[i_plan,:,:].transpose(), w[i_plan,:,:].transpose(), density = 1)
Q = ax.quiver(y, z-float(dz)/2, v_plot[i_plan,:,:].transpose(), w_plot[i_plan,:,:].transpose(), 
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
ax.set_xlim(100,190)
ax.set_ylim(0,30)

