#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 13 07:28:20 2018

@author: lucadelu
"""
import os
import json
import geojson
import urllib.request
from .functions import invert_bbox
from .functions import check_network
from .osmium_handler import CaiRoutesHandler

# class to get data from overpass and convert in different format
class CaiOsmData:

    def __init__(self, area=None, bbox=None, bbox_inverted=False,
                 separator='|', debug=False):
        """Class to get CAI data using Overpass API

        :param str area: the name of the area of interest
        :param str bbox: a string with the bounding box of the area, needed
                         format is YMIN,XMIN,YMAX,XMAX
        :param bool bbox_inverted: set True id the bbox format is
                                    XMIN,YMIN,XMAX,YMAX
        :param str separator: the separator to use for CSV
        :param bool debug: print debug information
        """
        self.area = area
        if bbox_inverted:
            self.bbox = invert_bbox(bbox)
        else:
            self.bbox = bbox
        self.url = "http://overpass-api.de/api/interpreter?"
        self.csvheader = False
        self.separator = separator
        self.debug = debug
        self.cch = None

    def _get_data(self, instr):
        """Private function to obtain the OSM data from overpass api

        :param str instr: the string with the overpass syntax
        """
        if self.debug:
            print(instr)
        values = {'data': instr}
        data = urllib.parse.urlencode(values)
        data = data.encode('utf-8') # data should be bytes
        req = urllib.request.Request(self.url, data)
        resp = urllib.request.urlopen(req)
        respData = resp.read()
        return respData.decode(encoding='utf-8', errors='ignore')

    def get_data_csv(self, csvheader=False, tags='::id,"name","ref"',
                     network='lwn'):
        """Function to return data in CSV format

        :param bool csvheader: show or hide the csv header, default hidden
        :param str tags: a list of tags to show in the csv
        """
        if csvheader:
            self.csvheader = True
        temp = """[out:csv({cols};{csvh};"{sep}")]
;
{area}
{query}
out;
"""
        network = check_network(network)
        if self.area:
            instr = temp.format(area='area["name"="{}"]->.a;'.format(self.area),
                                csvh=str(self.csvheader).lower(),
                                sep=self.separator,  cols=tags,
                                query=self.query.format(netw=network,
                                                        bbox='area.a'))
        elif self.bbox:
            instr = temp.format(area='', csvh=str(self.csvheader).lower(),
                                sep=self.separator, cols=tags,
                                query=self.query.format(netw=network,
                                                        bbox=self.bbox))
        else:
            instr = temp.format(area='', csvh=str(self.csvheader).lower(),
                                sep=self.separator, cols=tags,
                                query=self.query.format(netw=network,
                                                        bbox=''))

        return self._get_data(instr)


    def get_data_osm(self, network='lwn'):
        """Function to return data in the original OSM format

        :param str network: the network level to query, default 'lwn'
        """
        temp = """[out:xml]
;
{area}
{query}
out;
>;
out skel qt;
out;"""

        network = check_network(network)
        if self.area:
            instr = temp.format(area='area["name"="{}"]->.a;'.format(self.area),
                                query=self.query.format(netw=network,
                                                        bbox='area.a'))
        elif self.bbox:
            instr = temp.format(area='', query=self.query.format(netw=network,
                                                                 bbox=self.bbox))
        else:
            instr = temp.format(area='', query=self.query.format(netw=network,
                                                                 bbox=''))

        return self._get_data(instr)


    def get_data_json(self, network='lwn'):
        """Function to return the OSM data in JSON formats

        :param str network: the network level to query, default 'lwn'
        """
        temp = """[out:json]
;
{area}
{query}
out;
>;
out skel qt;"""

        network = check_network(network)
        if self.area:
            instr = temp.format(area='area["name"="{}"]->.a;'.format(self.area),
                                query=self.query.format(netw=network,
                                                        bbox='area.a'))
        elif self.bbox:
            instr = temp.format(area='',query=self.query.format(netw=network,
                                                                bbox=self.bbox))
        else:
            instr = temp.format(area='',query=self.query.format(netw=network,
                                                                bbox=''))

        return json.loads(self._get_data(instr))


    def get_tags_json(self, debug=False, network='lwn'):
        """Function to get the tags plus id for CAI relations

        :param str network: the network level to query, default 'lwn'
        """
        data = self.get_data_json(network=network)
        tags = []
        for elem in data['elements']:
            #check if the element is a relation
            if elem['type'] == 'relation':
                # cai_scale used as tag to reconize CAI paths
                if elem['tags']['type'] == 'route' and 'cai_scale' in elem['tags'].keys():
                    vals = elem['tags']
                    vals['id'] = elem['id']
                    tags.append(vals)
                    if debug:
                        print(vals)
        return tags


    def wiki_table(self, network='lwn'):
        """Function to convert a CSV file to a wiki table.
        Original code from https://github.com/dlink/vbin/blob/master/csv2wiki

        :param str network: the network level to query, default 'lwn'
        """
        data = self.get_data_csv(tags='"ref","name",::id', network=network)
        # read it

        rows = data.splitlines()
        table = []
        for fields in rows:
            row = []
            x = 0
            for field in fields.split(self.separator):
                field = field.strip()
                if x == 2:
                    row.append("{{BrowseRelation|" + field + "}}")
                else:
                    row.append(field)
                x += 1
            row.extend(['', ''])
            table.append(row)
        # output wiki format
        out = '{| class="wikitable sortable mw-collapsible mw-collapsed" \n'
        out += '|-\n'
        out += '!Ref\n!Nome\n!Link route\n!%completamento\n!note\n'
        i = 0
        for row in sorted(table, key=lambda row: row[0]):
            i += 1
            if i == 1 and self.csvheader:
                continue
            else:
                delim = '|'
                out += "|-\n"

            out += '\n'.join(["%s%s" % (delim, x) for x in row])
            out += '\n'

        out += "|-\n|}\n"
        return out

    def write(self, out, out_format, network=False):
        """Write the data obtained in different format into a file

        :param str out: the path to the output file
        :param str out_format: the required output format
        """
        if out_format == 'csv':
            data = self.get_data_csv(network=network)
        elif out_format == 'osm':
            data = self.get_data_osm(network=network)
        elif out_format == 'wikitable':
            data = self.wiki_table(network=network)
        elif out_format == 'json':
            data = json.dumps(self.get_data_json(network=network))
        elif out_format == 'tags':
            data = json.dumps(self.get_tags_json(network=network))
        elif out_format == 'geojson':
            data = self.get_geojson(network=network)
            with open(out, 'w') as fil:
                geojson.dump(data, fi)
            return True
        else:
            raise ValueError('Only csv, osm, wikitable, json, tags, geojson '
                             'format are supported')
        with open(out, 'w') as fil:
            fil.write(data)
        return True


class CaiOsmRoute(CaiOsmData):
    def __init__(self, area=None, bbox=None, bbox_inverted=False,
                 separator='|', debug=False):
        super(CaiOsmRoute, self).__init__(area=area, bbox=bbox,
                                          bbox_inverted=bbox_inverted,
                                          separator=separator, debug=debug)

        self.query = """
relation
  ["route"="hiking"]
  {netw}
  ["cai_scale"]
  ({bbox});
"""

    def get_length(self, network='lwn'):
        """Function to return the total lenght of data

        :param str network: the network level to query, default 'lwn'
        """

        if not self.cch:
            self.cch.get_cairoutehandler(network)
        self.cch.length()
        return self.cch.total

    def get_cairoutehandler(self, network='lwn'):
        """Function to download osm data and create CaiRoutesHandler instance

        :param str network: the network level to query, default 'lwn'
        """
        osm = self.get_data_osm(network=network)
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.osm') as fi:
            fi.write(osm)
        self.cch = CaiRoutesHandler()
        self.cch.apply_file(fi.name, locations=True)
        os.remove(fi.name)
        return True

    def get_geojson(self, network='lwn'):
        """Function to get a GeoJSON object

        :param str network: the network level to query, default 'lwn'
        """
        if not self.cch:
            self.get_cairoutehandler(network)
        return self.cch.gjson


class CaiOsmOffice(CaiOsmData):
    def __init__(self, area='Italia', bbox=None, bbox_inverted=False,
                 separator='|', debug=False):
        super(CaiOsmOffice, self).__init__(area=area, bbox=bbox,
                                           bbox_inverted=bbox_inverted,
                                           separator=separator, debug=debug)
        self.query = """
(
  node
    ["office"="association"]
    ["operator"="Club Alpino Italiano"]
    ({bbox});
  way
    ["office"="association"]
    ["operator"="Club Alpino Italiano"]
    ({bbox});
  relation
    ["office"="association"]
    ["operator"="Club Alpino Italiano"]
    ({bbox});
  node
    ["office"="association"]
    ["operator"="Società degli Alpinisti Tridentini"]
    ({bbox});
  way
    ["office"="association"]
    ["operator"="Società degli Alpinisti Tridentini"]
    ({bbox});
  relation
    ["office"="association"]
    ["operator"="Società degli Alpinisti Tridentini"]
    ({bbox});
);
"""

    def get_geojson(self):
        """Function to get a GeoJSON object"""
        data = self.get_data_json(network=network)
        features = []
        ways = {}
        nodes = {}
        i = 1
        for elem in data['elements']:
            # node is not an office but a point to create a way
            if elem['type'] == 'node' and 'tags' not in elem.keys():
                nodes[elem['id']] = elem
            # CAI office is mapped as point
            elif elem['type'] == 'node' and 'tags' in elem.keys():
                geom = geojson.Point([elem['lon'], elem['lat']])
                feat = geojson.Feature(id=i, geometry=geom,
                                       properties=elem['tags'])
                features.append(feat)
            # CAI office is mapped as way so I need temporary variable
            elif elem['type'] == 'way' and 'tags' in elem.keys():
                ways[i] = {'tags': elem['tags'], 'nodes': elem['nodes']}
            i += 1

        for k, v in ways.items():
            coords = []
            for n in v['nodes']:
                node = nodes[n]
                coords.append((node['lon'], node['lat']))
            geom = geojson.LineString(coords)
            feat = geojson.Feature(id=k, geometry=geom, properties=v['tags'])
            features.append(feat)
        return geojson.FeatureCollection(features)

class CaiOsmSourceRef(CaiOsmData):
    def __init__(self, area='Italia', bbox=None, separator='|', debug=False):
        super(CaiOsmSourceRef, self).__init__(area=area,
                                              separator=separator, debug=debug)

        self.query = """
relation
  ["route"="hiking"]
  {netw}
  ["cai_scale"]
  ["source:ref"]
  ({bbox});
"""

    def get_list_codes(self, network='lwn'):
        """Function to return data in CSV format

        :param str network: a list of tags to show in the csv
        """
        allcodes = self.get_data_csv(csvheader=False, tags='"source:ref"',
                                     network=network)
        return list(set(allcodes.splitlines()))

class CaiOsmRouteSourceRef(CaiOsmRoute):
    def __init__(self, sourceref, separator='|', debug=False):
        super(CaiOsmRouteSourceRef, self).__init__(separator=separator,
                                                   debug=debug)
        source = '["source:ref"="{code}"]'.format(code=sourceref)
        query = """
relation
  ["route"="hiking"]
  {netw}
  ["cai_scale"]
"""
        self.query = query + source + """;"""