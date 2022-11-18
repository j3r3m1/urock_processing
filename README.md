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

Note that in the current version the terrain slope is not taken into account.

# Computer requirements
Most of the vector data manipulations are performed using [H2GIS](http://www.h2gis.org/) which is automatically downloaded when executing URock. However, H2GIS is based on Java, thus you need to have a version of Java (>=8) installed on your computer. If you do not have, please download it [here](https://java.com/en/download/windows_manual.jsp) for Windows users or [here](https://java.com/en/download/) for Linux users. Make sure you download the version (32 or 64 bits) consistent with your system (even though most computers are 64 bits nowaday). For information, when you will first execute URock the JAVA environment path will be collected but you can also specify it by yourself if you want URock to use a specific version of JAVA (probably looks like _"C:\Program Files\Java\jre1.8.0_271"_ on Windows and like _"/usr/lib/jvm/java-8-openjdk"_ on Linux).

Several libraries need to be downloaded beforehand (using "osgeo and pip" or only "anaconda" depending of your use - do not mix both !!)
- [Jaydebeapi](https://pypi.org/project/JayDeBeApi/) Python library: useful to use the H2GIS database engine in Python,
- [Numba](https://numba.readthedocs.io/en/stable/user/installing.html) to increase the speed of the second step of the URock methodology
the H2GIS database engine in Python,
- [importlib_metadata](https://importlib-metadata.readthedocs.io/en/latest/)

# How to use ?
(temporary patch, soon included in UMEP)
In QGIS:
1. Download the package: from the github page, click on the green button "Code" -> "download as zip" 
2. import the zip in QGIS: in QGIS, click on "toolbarPlugin" -> "Install and manage plugins" and then "Install from zip" on the left panel in the new window appearing)

Outside QGIS:
Do the installation in QGIS and then follow the tutorial to use QGIS processing in Python: https://umep-docs.readthedocs.io/projects/tutorial/en/latest/Tutorials/PythonProcessing2.html#pythonprocessing2


# References
_Röckle, R., 1990: Bestimmung der Strömungsverhältnisse im Bereich komplexer Bebauungsstruk-turen. PhD thesis Fachbereich Mechanik der Technischen Hochschule Darmstadt Darmstadt._
