# URock
Röckle method for fast wind speed calculation

# What is performed ?
A 3D urban wind speed calculation is performed using a 2 steps methodology proposed by Röckle (1990):
1. Initialization step: the wind field is initialized around buildings and within vegetation by modeling empirically the wind speed and direction using results from wind tunnel observations
2. Solving step: the advection equation is solved from this initial wind field to balance the wind (the turbulence is supposed roughly “solved” by the initialization).

Note that the terrain slope is not taken into account.

# How to use ?
The TestFile.py file is used to set the simulation informations of a new case and to run it.

First, you need to set the following informations:
- Geographical input data
- Meteorological input data
- Meshing properties
- Other simulation parameters
- Plotting options

## Geographical input data
The geographical inputs are vector files (shapefile and geojson are supported).

First, create a folder in the "./Ressource" directory. Let's call this folder "myCase". In the test file, you should set the variable 'caseToRun' to "myCase".

Then put your building and your (optional) vegetation files into this folder and set the variable 'buildingFileName' and 'vegetationFileName' according to your file names (with the extension). If you do not have vegetation file, set 'vegetationFileName' to None

Your building file should contain:
- a geometry field (called "THE_GEOM") containing POLYGONS,
- an ID field (you set the name in the 'idFieldBuild' variable)
- an building height field (you set the name in the 'buildingHeightField' variable).

Your vegetation file (if any) should contain:
- a geometry field (called "THE_GEOM") containing POLYGONS,
- an ID field (you set the name in the 'idVegetation' variable),
- a vegetation base height field (you set the name in the 'vegetationBaseHeight' variable),
- a vegetation top height field (you set the name in the 'vegetationTopHeight' variable),
- a vegetation attenuation factor field (you set the name in the 'vegetationAttenuationFactor' variable).

Note that all fields have default values in the GlobalVariables.py file.

## Meteorological input data
The wind field is simulated for a given wind direction and wind speed at a specified height. Then you should set the wind speed ('v_ref'), the wind direction ('windDirection') and the height ('z_ref') at which the wind speed is set.

## Meshing properties
The size of the sketch and the size of the meshes are set in this section.
In the initialization (step 1), we identify the 3D zones where the wind is strongly impacted by the obstacles (in what we called the "Röckle zones"). If we do not extend the simulation grid horizontally and vertically around these zones, we may clearly affect the resulting wind speed since the wind speed modification within these zones will induce a wind speed modification around these zones. Thus we set the size of the sketch as an extend in the along wind, cross wind and vertical directions (respectively 'alongWindZoneExtend', 'crossWindZoneExtend' and 'verticalExtend').
The cubic mesh sizes should then be set: the horizontal spacing is set using 'meshSize' and the vertical resolution is set using 'dz'.

## Other simulation parameters
The solving (step 2) may take quite a while and the user may only want to verify that the initialization (step 1) went well. To perform only step 1, the boolean variable 'onlyInitialization' should be set to True.
Intermediate results such as 2D Röckle zones and the 3D points located in the Röckle zones may be saved in the "./Ressources/Outputs" directory if you set the boolean variable 'saveRockleZones' to True.
The numerical solver can stop when one of the following condition is reached: the number of iteration reaches 'maxIterations' or the relative wind field change between two consecutive iteration is lower than 'thresholdIterations'.
A temporary directory is used for file exchange between H2Database and Python and to save the H2Database. You can set a specific path for this directory using the 'tempoDirectory' variable.

## Plotting options
Several figures are plotted if 'plotBoolean' is set to True:
1. the horizontal wind FIELD for a list of level ('levelList') defined by the user,
2. the horizontal wind SPEED for the same list of level,
3. the wind FIELD in a sectional view (YZ plan) for the median X plan

The computed wind may be the one at the end of the initialization step ('isInitialField' = True) or the one after numerical solving ('isInitialField' = False).
The wind FIELDS may be a 2D vector for each mesh ('isStream' = False) or stream lines ('isStream' = True). If streams, you can set the density of streams using the 'streamDensity' variable.
The size and shape of the arrow head may be defined using the 'headwidth', 'headlength' and 'headaxislength' variables.

# References
Röckle, R., 1990: Bestimmung der Strömungsverhältnisse im Bereich komplexer Bebauungsstruk-turen. PhD thesis Fachbereich Mechanik der Technischen Hochschule Darmstadt Darmstadt.
