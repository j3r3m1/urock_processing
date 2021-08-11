#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 30 14:21:04 2021

@author: Jérémy Bernard, University of Gothenburg
"""
import os
import MainCalculation
import matplotlib.colors as colors
import matplotlib.pylab as plt

from GlobalVariables import * 


# -----------------------------------------------------------------------------------
# SET INPUT PARAMETERS --------------------------------------------------------------
# -----------------------------------------------------------------------------------
# Geographical input data
caseToRun = "BigArea"
buildingFileName = "buildingSelection.shp"
idFieldBuild = ID_FIELD_BUILD
buildingHeightField = HEIGHT_FIELD

vegetationFileName = ""
vegetationBaseHeight = VEGETATION_CROWN_BASE_HEIGHT
vegetationTopHeight = VEGETATION_CROWN_TOP_HEIGHT
idVegetation = ID_VEGETATION
vegetationAttenuationFactor = VEGETATION_ATTENUATION_FACTOR

# Meteorological input data
v_ref = 2
windDirection = 13
z_ref = 10

# Meshing properties
alongWindZoneExtend = 30
crossWindZoneExtend = 25
verticalExtend = 20
meshSize = 2
dz = 2

# Other simulation parameters
onlyInitialization = False
saveRockleZones = False
maxIterations = MAX_ITERATIONS
thresholdIterations = THRESHOLD_ITERATIONS
tempoDirectory = TEMPO_DIRECTORY

# Plotting options
plotBoolean = True
isInitialField = False
levelList = [2, 21]

isStream = False
streamDensity = 3

headwidth = 3
headlength = 1.5
headaxislength = 1.5

xRange = [10, 70]
yRange = [60, 140]
zRange = [0, 40]


# -----------------------------------------------------------------------------------
# MAIN CALCULATIONS -----------------------------------------------------------------
# -----------------------------------------------------------------------------------
inputBuildingFilename = os.path.join(caseToRun, buildingFileName)
if vegetationFileName:
    inputVegetationFilename = os.path.join(caseToRun, vegetationFileName)
else:
    inputVegetationFilename = ""


u, v, w, u0, v0, w0, x, y, z, buildingCoordinates = \
    MainCalculation.main(   z_ref = z_ref,
                            v_ref = v_ref,
                            windDirection = windDirection,
                            prefix = caseToRun,
                            meshSize = meshSize,
                            dz = dz,    
                            alongWindZoneExtend = alongWindZoneExtend,
                            crossWindZoneExtend = crossWindZoneExtend,
                            verticalExtend = verticalExtend,
                            inputBuildingFilename = inputBuildingFilename,
                            inputVegetationFilename = inputVegetationFilename,
                            tempoDirectory = tempoDirectory,
                            onlyInitialization = onlyInitialization,
                            maxIterations = maxIterations,
                            thresholdIterations = thresholdIterations,
                            idFieldBuild = idFieldBuild,
                            buildingHeightField = buildingHeightField,
                            vegetationBaseHeight = vegetationBaseHeight,
                            vegetationTopHeight = vegetationTopHeight,
                            idVegetation = idVegetation,
                            vegetationAttenuationFactor = vegetationAttenuationFactor,
                            saveRockleZones = saveRockleZones)

if plotBoolean:
    # -----------------------------------------------------------------------------------
    # POST-PROCESSING -------------------------------------------------------------------
    # -----------------------------------------------------------------------------------
    if isInitialField:
        u_plot = u0
        v_plot = v0
        w_plot = w0
    else:
        u_plot = u
        v_plot = v
        w_plot = w
    # Convert building coordinates to a 3D multiindex object
    iterables = [np.arange(0,x.size), np.arange(0,y.size), np.arange(0,z.size)]
    cells = pd.Series(dtype = "float64",
                      index = pd.MultiIndex.from_product(iterables, names=('x', 'y', 'z')))
    cells.loc[pd.MultiIndex.from_arrays(buildingCoordinates, names=('x', 'y', 'z'))] = 1.
    
    # Calculates wind speed for each cell
    ws_plot = (u_plot**2+v_plot**2+w_plot**2)**0.5
    
    # -----------------------------------------------------------------------------------
    # PLOT FIGURES ----------------------------------------------------------------------
    # -----------------------------------------------------------------------------------
    nrows = int((len(levelList))**0.5)
    ncols = int(len(levelList)/nrows)
    if nrows*ncols < len(levelList):
        ncols += 1
    # 1. Wind field in an (X,Y) plan ----------------------------------------------
    # -----------------------------------------------------------------------------------   
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
            if isStream:
                ax_ij.streamplot(x, y, u = u_plot[:,:,n_lev].transpose(), 
                                 v = v_plot[:,:,n_lev].transpose(),
                                 density = streamDensity)
            else:
                Q = ax_ij.quiver(x, y, u_plot[:,:,n_lev].transpose(), 
                                 v_plot[:,:,n_lev].transpose(), 
                                 units = 'xy', scale = dz, headwidth = 6,
                                 headlength = 3, headaxislength = 2.5)
                ax_ij.quiverkey(Q, 0.9, 0.9, 1, r'$1 \frac{m}{s}$', labelpos='E',
                                coordinates='figure')
            if len(xRange)==2:
                ax_ij.set_xlim(xRange[0],xRange[1])
            if len(yRange)==2:
                ax_ij.set_ylim(yRange[0],yRange[1])
            
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
            # Set building pixels in black
            pcol = ax_ij.pcolor(ws_plot[:,:,n_lev].transpose(), 
                            cmap = "coolwarm")
            if len(xRange)==2:
                ax_ij.set_xlim(xRange[0],xRange[1])
            if len(yRange)==2:
                ax_ij.set_ylim(yRange[0],yRange[1])
            
            
            # Get buildings for the z level considered
            buildZ = cells.xs(n_lev, level = 2)
            
            # Set building pixels in black
            ax_ij.pcolor(buildZ.index.unique(0),
                            buildZ.index.unique(1),
                            buildZ.unstack().transpose().values,
                            shading = "nearest")
            ax_ij.set_title("{0} m".format(n_lev*dz-float(dz)/2))
            plt.colorbar(pcol, ax = ax_ij)
    
    # ----------------------------------------------------------------------------- 
    # 3. Wind field in an (Y,Z) plan ----------------------------------------------
    # ----------------------------------------------------------------------------- 
    i_plan = int(x.size/2)
    fig, ax = plt.subplots(sharex = True, sharey=True)
    if isStream:
        ax.streamplot(y, z-float(dz)/2, v_plot[i_plan,:,:].transpose(),
                      w_plot[i_plan,:,:].transpose(),
                      density = streamDensity)
    else:
        Q = ax.quiver(y, z-float(dz)/2, v_plot[i_plan,:,:].transpose(),
                      w_plot[i_plan,:,:].transpose(), 
                      units = 'xy', scale = dz, headwidth = headwidth, 
                      headlength = headlength,
                      headaxislength = headaxislength)
        ax.quiverkey(Q, 0.9, 0.9, 1, r'$1 \frac{m}{s}$', labelpos='E',
                     coordinates='figure')
    
    buildZ = cells.xs(i_plan, level = 0)
    
    # Set building pixels in color
    ax.pcolor(  buildZ.index.unique(0)*meshSize,
                buildZ.index.unique(1)*dz-float(dz)/2,
                buildZ.unstack().transpose().values,
                shading = "nearest",
                alpha = 0.8)
    if len(yRange)==2:
        ax.set_xlim(yRange[0],yRange[1])
    if len(zRange)==2:
        ax.set_ylim(zRange[0],zRange[1])