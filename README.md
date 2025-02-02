# navigator-scripts

A set of Python scripts and notebooks to help deploy ArcGIS Navigator

## Notebooks

Several example Jupyter notebooks are provided to demonstrate some more advanced workflows that are possible via the ArcGIS API for Python and Navigator.
- [Automating Creation of Preplanned Routes](notebooks/Automating_Creation_of_Preplanned_Routes.ipynb)
- [Automate the Conversion of a Polyline into a Route Layer](notebooks/Automate_the_Conversion_of_a_Polyline_into_a_Route_Layer.ipynb)
- [Create a MMPK and Preplanned Route](notebooks/Create_a_MMPK_and_Preplanned_Route.ipynb)

## Scripts

Scripts for helping deploy ArcGIS Navigator.
- [create_mmpk](scripts/create_mmpk.py)


## Requirements
- Python 3.6+
- ArcGIS API for Python 1.8.4+
- ArcGIS Navigator (on iOS or Android)
- ArcPy (installed with ArcGIS Pro) - only required for select scripts that `import arcpy`

### Instructions

1. Install ArcGIS API for Python package as described [here](https://developers.arcgis.com/python/guide/install-and-set-up/).
2. Clone or download this repository
3. Open `./notebooks` directory in terminal
3. `jupyter notebook` (to start a jupyter notebook server)

## Resources

 * [ArcGIS API for Python](https://developers.arcgis.com/python)
 * [ArcGIS Navigator](https://www.esri.com/en-us/arcgis/products/arcgis-navigator/overview)

## Issues

Find a bug or want to request a new feature?  Please let us know by submitting an issue.

## Contributing

Esri welcomes contributions from anyone and everyone.
Please see our [guidelines for contributing](https://github.com/esri/contributing).

## Licensing

Copyright 2021 Esri

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

A copy of the license is available in the repository's
[LICENSE](LICENSE) file.
