#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 13 07:28:20 2018

@author: lucadelu
"""
import os
import json
import urllib.request
import osmium
import shapely.wkt as wktlib
from shapely.geometry import MultiLineString
import geojson

def invert_bbox(bbox):
    """Convert the bounding box from XMIN,YMIN,XMAX,YMAX to YMIN,XMIN,YMAX,XMAX

    :param str box: the string of the bounding box comma separated
    """
    l = bbox.split(',')
    return "{ymi},{xmi},{yma},{xma}".format(ymi=l[1], xmi=l[0], yma=l[3],
                                            xma=l[2])

def check_network(net):
    """Check if network is set

    :param str net: the network code
    """
    if net in ['lwn', 'rwn', 'nwn', 'iwn']:
        return '["network"="{}"]'.format(net)
    return ''

WKTFAB = osmium.geom.WKTFactory()

class CaiCounterHandler(osmium.SimpleHandler):
    """Class to parse CAI routes from OSM file"""
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.count = 0
        self.routes = {}
        self.ways = {}
        self.gjson = None

    def way(self, way):
        """Function to parse ways"""
        self.ways[way.id] = WKTFAB.create_linestring(way)

    def relation(self, rel):
        """Function to parse relations"""
        members = []
        tags = {}
        for mem in rel.members:
            if mem.type == 'w':
                members.append(mem.ref)
        for t in rel.tags:
            tags[t.k] = t.v
        tags['id'] = rel.id
        self.count += 1
        self.routes[rel.id] = {'tags': tags, 'elems': members}

    def create_geojson(self):
        """Function to create geometries for routes and GeoJSON object"""
        features = []
        for k, v in self.routes.items():
            lines = []
            for w in v['elems']:
                lines.append(wktlib.loads(self.ways[w]))
            geom = MultiLineString(lines)
            self.routes[k]['geom'] = geom
            feat = geojson.Feature(geometry=geom,
                                   properties=self.routes[k]['tags'])
            features.append(feat)
        self.gjson = geojson.FeatureCollection(features)

    def write_geojson(self, out):
        """Function to write GeoJSON file

        :param str out: the path to the output file
        """
        with open(out, 'w') as f:
            geojson.dump(self.gjson, f)


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
relation
  ["route"="hiking"]
  {netw}
  ["cai_scale"]
  ({bbox});
out;"""
        network = check_network(network)
        if self.area:
            instr = temp.format(area='area["name"="{}"]->.a;'.format(self.area),
                                bbox='area.a', netw=network,
                                csvh=str(self.csvheader).lower(),
                                sep=self.separator,
                                cols=tags)
        elif self.bbox:
            instr = temp.format(area='', bbox=self.bbox, netw=network,
                                csvh=str(self.csvheader).lower(),
                                sep=self.separator,
                                cols=tags)
        else:
            raise ValueError('One of area or box argument should be used')

        return self._get_data(instr)


    def get_data_osm(self, network='lwn'):
        """Function to return data in the original OSM format"""
        temp = """[out:xml]
;
{area}
relation
  ["route"="hiking"]
  {netw}
  ["cai_scale"]
  ({bbox});
out;
>;
out skel qt;
out;"""

        network = check_network(network)
        if self.area:
            instr = temp.format(area='area["name"="{}"]->.a;'.format(self.area),
                                netw=network, bbox='area.a')
        elif self.bbox:
            instr = temp.format(area='', netw=network, bbox=self.bbox)
        else:
            raise ValueError('One of area or box argument should be used')

        return self._get_data(instr)


    def get_data_json(self, network='lwn'):
        """Function to return the OSM data in JSON formats"""
        temp = """[out:json]
;
{area}
relation
  ["route"="hiking"]
  {netw}
  ["cai_scale"]
  ({bbox});
out;
>;
out skel qt;"""

        network = check_network(network)
        if self.area:
            instr = temp.format(area='area["name"="{}"]->.a;'.format(self.area),
                                netw=network, bbox='area.a')
        elif self.bbox:
            instr = temp.format(area='', netw=network, bbox=self.bbox)
        else:
            raise ValueError('One of area or box argument should be used')

        return json.loads(self._get_data(instr))


    def get_tags_json(self, debug=False, network='lwn'):
        """Function to get the tags plus id for CAI relations"""
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


    def wiki_table(self, network=False):
        """Function to convert a CSV file to a wiki table.
        Original code from https://github.com/dlink/vbin/blob/master/csv2wiki
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

    def get_geojson(self, network=False):
        """Function to create a GeoJSON object"""
        osm = self.get_data_osm(network=network)
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.osm') as fi:
            fi.write(osm)
        cch = CaiCounterHandler()
        cch.apply_file(fi.name, locations=True)
        cch.create_geojson()
        os.remove(fi.name)
        return cch.gjson

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
            data = self.get_data_json(network=network)
        elif out_format == 'tags':
            data = self.get_tags_json(network=network)
        elif out_format == 'geojson':
            data = self.get_geojson(network=network)
            with open(out, 'w') as f:
                geojson.dump(data, f)
            return True
        else:
            raise ValueError('Only csv, osm, wikitable, json, tags format are '
                             'supported')
        with open(out, 'w') as fil:
            fil.write(data)
        return True
