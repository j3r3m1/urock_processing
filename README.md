# URock
Röckle method for fast wind speed calculation

# What is performed ?
A 3D urban wind speed calculation is performed using a 2 steps methodology proposed by Röckle (1990):
1. **Initialization step**: the wind field is initialized around buildings and within vegetation by modeling empirically the wind speed and direction using results from wind tunnel observations
2. **Solving step**: the advection equation is solved from this initial wind field to balance the wind (the turbulence is supposed roughly “solved” by the initialization).

| View | After initialization | After numerical solving |
| -- | -- | -- |
| Horizontal | ![initializedHorizontal](https://user-images.githubusercontent.com/13120405/117828537-2fa09100-b272-11eb-8ff7-08cfd95f0baf.png) | ![solvedHorizontal](https://user-images.githubusercontent.com/13120405/117828703-5bbc1200-b272-11eb-8c76-8acc23dc06d5.png) |
| Sectional | ![initializedSectional](https://user-images.githubusercontent.com/13120405/117829471-12b88d80-b273-11eb-9fa8-38f1d8a31d9d.png) | ![solvedSectional](https://user-images.githubusercontent.com/13120405/117829042-ab024280-b272-11eb-897c-8b725ecbb883.png) |

Note that the terrain slope is not taken into account.

# Computer requirements
Most of the vector data manipulations are performed using [H2GIS](http://www.h2gis.org/) which is automatically downloaded when executing URock. However, H2GIS is based on Java, thus you need to have a version of Java (>=8) installed on your computer. If you do not have, please download it [here](https://java.com/en/download/windows_manual.jsp) for Windows users or [here](https://java.com/en/download/) for Linux users. Make sure you download the version (32 or 64 bits) consistent with your system (even though most computers are 64 bits nowaday). When you will first launch the URock library, you will be asked what is your JAVA environment path (probably looks like _"C:\Program Files\Java\jre1.8.0_271"_ on Windows and like _"/usr/lib/jvm/java-8-openjdk"_ on Linux).

To use such database engine in Python, you also need to install the [Jaydebeapi](https://pypi.org/project/JayDeBeApi/) Python library.

# How to use ?
The _TestFile.py_ file is used to set the simulation informations of a new case and to run it.

First, you need to set the following informations:
- Geographical input data
- Meteorological input data
- Meshing properties
- Other simulation parameters
- Plotting options

## Geographical input data
The geographical inputs are vector files (shapefile and geojson are supported).

First, create a folder in the _"./Ressource"_ directory. Let's call this folder _"myCase"_. In the test file, you should set the variable _'caseToRun'_ to _"myCase"_.

Then put your building and your (optional) vegetation files into this folder and set the variable _'buildingFileName'_ and _'vegetationFileName'_ according to your file names (with the extension). If you do not have vegetation file, set _'vegetationFileName'_ to _None_

Your **building file** should contain:
- a geometry field (called _"THE_GEOM"_) containing POLYGONS,
- an ID field (you set the name in the _'idFieldBuild'_ variable)
- an building height field (you set the name in the _'buildingHeightField'_ variable).

Your **vegetation file** (if any) should contain:
- a geometry field (called _"THE_GEOM"_) containing POLYGONS,
- an ID field (you set the name in the _'idVegetation'_ variable),
- a vegetation base height field (you set the name in the _'vegetationBaseHeight'_ variable),
- a vegetation top height field (you set the name in the _'vegetationTopHeight'_ variable),
- a vegetation attenuation factor field (you set the name in the _'vegetationAttenuationFactor'_ variable).

Note that all fields have default values in the _GlobalVariables.py_ file.

## Meteorological input data
The wind field is simulated for a given wind direction and wind speed at a specified height. Then you should set the wind speed (_'v_ref'_) in _m/s_, the wind direction (_'windDirection'_) in degree clockwise from North and the height from ground (_'z_ref'_) in _m_ at which the wind speed is set.

## Meshing properties
The size of the sketch and the size of the meshes are set in this section.
In the initialization (step 1), we identify the 3D zones where the wind is strongly impacted by the obstacles (in what we called the "Röckle zones"). If we do not extend the simulation grid horizontally and vertically around these zones, we may clearly affect the resulting wind speed since the wind speed modification within these zones will induce a wind speed modification around these zones. Thus we set the size of the sketch as an extend in the along wind, cross wind and vertical directions (respectively _'alongWindZoneExtend'_, _'crossWindZoneExtend'_ and _'verticalExtend'_).
The cubic mesh sizes should then be set: the horizontal spacing is set using _'meshSize'_ and the vertical resolution is set using _'dz'_.

## Other simulation parameters
The solving (step 2) may take quite a while and the user may only want to verify that the initialization (step 1) went well. To perform only step 1, the boolean variable _'onlyInitialization'_ should be set to True.
Intermediate results such as 2D Röckle zones and the 3D points located in the Röckle zones may be saved in the _"./Ressources/Outputs"_ directory if you set the boolean variable _'saveRockleZones'_ to True.
The numerical solver can stop when one of the following condition is reached: the number of iteration reaches _'maxIterations'_ or the relative wind field change between two consecutive iteration is lower than _'thresholdIterations'_.
A temporary directory is used for file exchange between H2Database and Python and to save the H2Database. You can set a specific path for this directory using the _'tempoDirectory'_ variable.

## Plotting options
Several figures are plotted if _'plotBoolean'_ is set to True:
1. the horizontal wind FIELD for a list of level (_'levelList'_) defined by the user,
2. the horizontal wind SPEED for the same list of level,
3. the wind FIELD in a sectional view (_YZ_ plan) for the median X plan

The computed wind may be the one at the end of the initialization step (_'isInitialField' = True_) or the one after numerical solving (_'isInitialField' = False_).
The wind FIELDS may be a 2D vector for each mesh (_'isStream' = False_) or stream lines (_'isStream' = True_). If streams, you can set the density of streams using the _'streamDensity'_ variable.
You may plot a limited range for axis _X_, _Y_ and _Z_. If so you have to set respectively in _'xRange'_, _'yRange'_ and _'zRange'_ a list containing min and max values  (if the list is empty, all the domain is plotted).
The size and shape of the arrow head may be defined using the _'headwidth'_, _'headlength'_ and _'headaxislength'_ variables.

| ![streamHorizontal](https://user-images.githubusercontent.com/13120405/117823598-eea67d80-b26d-11eb-9f86-61f37b7f0b9f.png) | ![streamSectional](https://user-images.githubusercontent.com/13120405/117829852-6aef8f80-b273-11eb-84c3-cb4539970aa9.png) |
|:--:|:--:|
| Horizontal stream line plot with 'streamDensity' = 3 | Sectional stream line plot with 'streamDensity' = 3 |



# References
_Röckle, R., 1990: Bestimmung der Strömungsverhältnisse im Bereich komplexer Bebauungsstruk-turen. PhD thesis Fachbereich Mechanik der Technischen Hochschule Darmstadt Darmstadt._
