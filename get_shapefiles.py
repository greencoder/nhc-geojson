import os
import json
import requests
import shapefile
import shutil
import StringIO
import sys
import tempfile
import zipfile

if __name__ == '__main__':
    
    # Store a reference to the current directory
    current_dir = os.path.dirname(os.path.realpath(__file__))
    output_dir = os.path.join(current_dir, 'output')
    
    # If the output directory alrady exists, remove it. The geojson 
    # driver cannot overwrite existing files
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    # Create the output directory
    os.makedirs(output_dir)

    # Open the JSON file we already created
    with open('summary.json', 'r') as f:
        data = json.loads(f.read())
    
    # Get all the shapefile URLs
    links = []
    for item in data['shapefiles']:
        links.append(item['link'])
    
    # Iterate over the links
    for index, link in enumerate(links):
        
        print "Fetching Shapefile (%d/%d):\n%s" % (index+1, len(links), link)

        # Request the file
        request = requests.get(link)
        zf = zipfile.ZipFile(StringIO.StringIO(request.content))

        # Extract the file to a temporary directory
        temp_dir = tempfile.mkdtemp()
        zf.extractall(temp_dir)
    
        # Get all the shapefile names
        shapefile_names = [f for f in os.listdir(temp_dir) if f.endswith('.shp')]

        # Iterate over all the shapefiles
        for filename in shapefile_names:

            # Create the full filepath
            filepath = os.path.join(temp_dir, filename)

            # Get the base file name
            geojson_filename = os.path.basename(filename) + '.geojson'
            geojson_filepath = os.path.join(output_dir, geojson_filename)
            
            # Run a command line script to convert to GeoJSON
            cmd = 'ogr2ogr -f GeoJSON -t_srs crs:84 %s %s' % (geojson_filepath, filepath)
            os.system(cmd)
            
        # Clean up the temporary directory
        shutil.rmtree(temp_dir)
