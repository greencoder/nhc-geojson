#NHC Shapefile to GeoJSON
Converts the National Hurricane Center (NHC) shapefiles for current storms to GeoJSON files.

## Usage

The program is broken into two parts. The first will look at the NHC GIS RSS feed and create a summary json file with storm metadata and a list of shapefiles:

```
$ python get_summaries.py
````

The second part reads the summary json and fetches the shapefiles, turning them into GeoJSON files:

```
$ python get_shapefiles.py
````

## Requirements

You must have (http://www.gdal.org/ogr2ogr.html)ogr2ogr installed. It's part of the GDAL library.
