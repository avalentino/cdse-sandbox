============
cdse-sandbox
============

Examples and experimental scripts showing how to query and download data
from the Copernicus Data Space Ecosystem (CDSE).

Use cases
---------

1. query for S1 RAW or SLC products based on:

   * time interval
   * imaging mode otr product type
   * relative orbit number
   * Area of Interest (AoI) in form pf BBox or Polygon

   The query shall generate a list of products and/or a Json file with the
   products metadata.
2. query for Copernicus DEM tile in a specified Area of Interest (AoI).
   The query shall generate a list of products and/or a json file with the
   products metadata.
3. download a list of products for which the product IDs are provided.
   The relevant products are (for Sentinel-1):

   * RAW
   * SLC
   * ETAD
   * orbit data
   * engineering and auxiliary products
   * Copernicus DEM tiles


SW tools
--------

* eodag v3.6.0 (01/07/2025) - https://github.com/CS-SI/eodag
* cdsetool v0.2.13 (10/10/2024) - https://github.com/CDSETool/CDSETool
* stac_client v0.9.0 (18/07/2025) - https://github.com/stac-utils/pystac-client
* cdsodatacli v2025.4.9 (09/04/2025) - https://github.com/umr-lops/cdsodatacli
* phidown v0.0.2 (29/04/2025) - https://github.com/ESA-PhiLab/phidown
* eofetch v0.3 (03/01/2025) - https://github.com/stcorp/eofetch
* cscip-client git commit 1f4dae4 (25/06/2025) -
  https://github.com/stcorp/cscip-client


API documentation
-----------------

* Catalogue APIs: https://dataspace.copernicus.eu/analyse/apis/catalogue-apis
* OData API: https://documentation.dataspace.copernicus.eu/APIs/OData.html
* STAC API: https://documentation.dataspace.copernicus.eu/APIs/STAC.html

  - query options:

    * SENTINEL-1:
      https://catalogue.dataspace.copernicus.eu/stac/collections/SENTINEL-1/queryables
    * COP-DEM:
      https://catalogue.dataspace.copernicus.eu/stac/collections/COP-DEM/queryables

* OpenSearch API:
  https://documentation.dataspace.copernicus.eu/APIs/OpenSearch.html

  - Machine readable description of the query parameters:

    * Sentinel-1:
      https://catalogue.dataspace.copernicus.eu/resto/api/collections/Sentinel1/describe.xml
    * Copernicus DEM:
      https://catalogue.dataspace.copernicus.eu/resto/api/collections/COP-DEM/describe.xml


Additional information
----------------------

* Data access via S3: https://documentation.dataspace.copernicus.eu/APIs/S3.html

  - Credentials management:
    https://eodata-s3keysmanager.dataspace.copernicus.eu

* Catalogie CSV:
  https://documentation.dataspace.copernicus.eu/Applications/Catalogue-csv.html
* Quotas and limitations:
  https://documentation.dataspace.copernicus.eu/Quotas.html
* Sentinel-1 Orbits:

  - https://documentation.dataspace.copernicus.eu/Data/SentinelMissions/Sentinel1.html#sentinel-1-precise-orbit-determination-pod-products
  - https://documentation.dataspace.copernicus.eu/Data/ComplementaryData/Additional.html#sentinel-1-orbits



License
-------

:copyright: 2025, Antonio Valentino

The `cdse-sandbox` code is distributed under the MIT License
(see the LICENSE file).
