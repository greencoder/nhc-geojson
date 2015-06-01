import datetime
import json
import pytz
import re
import requests
import sys
import xml.etree.ElementTree

def get_node_text(parent_node, tag_name, default=''):
    """Wrapper to safely extract the text from a node."""
    node = parent_node.find(tag_name)
    if node is not None:
        return node.text
    else:
        return default

if __name__ == '__main__':

    # Create a place to store the data
    summaries = {'Atlantic': [], 'Pacific': []}
    shapefiles = []

    # Grab the feed contents for the Atlantic and Pacific basins
    for basin_code, basin_name in [('ep', 'Pacific'), ('at', 'Atlantic')]:

        # First, grab the RSS url
        url = 'http://www.nhc.noaa.gov/gis-%s.xml' % basin_code
        request = requests.get(url)

        # Turn the contents into an XML document
        root = xml.etree.ElementTree.fromstring(request.text)

        # Find all the 'item' nodes
        for item_node in root.findall('channel/item'):

            # Capture the common node values
            title = get_node_text(item_node, 'title')
            guid = get_node_text(item_node, 'guid')
            pub_date_str = get_node_text(item_node, 'pubDate')
            author = get_node_text(item_node, 'author')
            link = get_node_text(item_node, 'link')
            description = get_node_text(item_node, 'description')

            # If there are no storms, we'll see that in the title
            if title.startswith('There are no'):
                continue

            # We don't want any kmz or xml links, we only care about shapefiles and summaries
            if '[kmz]' in title or '[xml]' in title:
                continue

            # Try to turn the pub date string into a properly-formatted ISO8601 date
            pub_date = datetime.datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S GMT')
            pub_date = pub_date.replace(tzinfo=pytz.timezone('UTC'))
            pub_date = pub_date.isoformat()

            # If it's a summary, capture the additional data points
            if title.startswith('Summary'):

                # All of the nodes will be namespaced
                namespace = '{http://www.nhc.noaa.gov}'

                # See if a "<nhc:Cyclone>" node exists
                cyclone_node = item_node.find(namespace + 'Cyclone')

                # If the cyclone node exists, get the values
                if cyclone_node is not None:

                    storm_position = get_node_text(cyclone_node, namespace + 'center', default=None)
                    storm_type = get_node_text(cyclone_node, namespace + 'type')
                    storm_name = get_node_text(cyclone_node, namespace + 'name')
                    storm_wallet = get_node_text(cyclone_node, namespace + 'wallet')
                    storm_atcf = get_node_text(cyclone_node, namespace + 'atcf')
                    storm_movement = get_node_text(cyclone_node, namespace + 'movement')
                    storm_pressure = get_node_text(cyclone_node, namespace + 'pressure')
                    storm_wind = get_node_text(cyclone_node, namespace + 'wind')
                    storm_headline = get_node_text(cyclone_node, namespace + 'headline')

                    # Turn the position element into lat and lng, it will arrive
                    # like this: <nhc:center>15.7, -120.3</nhc:center>
                    if storm_position:

                        # Make sure we can split this string and cast the pieces as floats
                        parts = storm_position.split(', ')
                        if len(parts) == 2:
                            try:
                                storm_lat = float(parts[0])
                                storm_lng = float(parts[1])
                            except ValueError:
                                storm_lat = None
                                storm_lng = None

                    # Store our parsed summary
                    summaries[basin_name].append({
                        'atcf-code': storm_atcf,
                        'basin': basin_name,
                        'position': {
                            'lat': storm_lat,
                            'lng': storm_lng,
                        },
                        'type': storm_type,
                        'name': storm_name,
                        'wallet': storm_wallet,
                        'movement': storm_movement,
                        'pressure': storm_pressure,
                        'wind': storm_wind,
                        'headline': storm_headline,
                    })

            # If it's a shapefile associated with a specific storm, parse it
            if '[shp]' in title:

                shapefile_type = title.split(" [shp]")[0]
                shapefile_storm = title.split('[shp] - ')[-1]

                # The shapefile might be for a specific storm or for
                # 'Multiple Basins', so figure that out and store accordingly

                # It's for multiple storms
                if shapefile_storm == 'Multiple Basins':
                    shapefiles.append({
                        'link': link,
                        'type': shapefile_type,
                        'basin': 'Multiple',
                    })

                # It's a specfic storm
                else:

                    # Try to extract the atcf code from the title, it will look like
                    # this: Advisory #018 Forecast [shp] - Hurricane ANDRES (EP1/EP012015)
                    regex = re.search(r'([\w\d]+\/(?P<code>.*))', title)
                    if regex and regex.group('code'):
                        atcf_code = regex.group('code')
                    else:
                        sys.exit('No ATCF code found in title: %s' % title)

                    shapefiles.append({
                        'link': link,
                        'type': shapefile_type,
                        'basin': basin_name,
                        'atcf-code': atcf_code,
                    })

    # Create an output dictionary we can write to a JSON file
    output = {
        'summaries': summaries,
        'shapefiles': shapefiles,
    }

    # The XML parsing is done, write out our JSON
    with open('summary.json', 'w') as f:
        f.write(json.dumps(output, indent=4))
