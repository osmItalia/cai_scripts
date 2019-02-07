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

    def write_geojson(self, to):
        """Function to write GeoJSON file

        :param str to: the path to the output file
        """
        with open(to, 'w') as f:
            geojson.dump(self.gjson, f)


class CaiOsmData:

    def __init__(self, area=None, bbox=None, bbox_inverted=False,
                 outtype='csv', separator='|', debug=False):
        self.area = area
        if bbox_inverted:
            self.bbox = invert_bbox(bbox)
        else:
            self.bbox = bbox
        self.outtype = outtype
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


    def get_data_csv(self, csvheader=False, tags='::id,"name","ref"'):
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
  ["network"="lwn"]
  ["cai_scale"]
  ({bbox});
out;"""

        if self.area:
            instr = temp.format(area='area["name"="{}"]->.a;'.format(self.area),
                                bbox='area.a',
                                csvh=str(self.csvheader).lower(),
                                sep=self.separator,
                                cols=tags)
        elif self.bbox:
            instr = temp.format(area='', bbox=self.bbox,
                                csvh=str(self.csvheader).lower(),
                                sep=self.separator,
                                cols=tags)
        else:
            raise ValueError('One of area or box argument should be used')

        return self._get_data(instr)


    def get_data_osm(self):
        """Function to return data in the original OSM format"""
        temp = """[out:xml]
;
{area}
relation
  ["route"="hiking"]
  ["network"="lwn"]
  ["cai_scale"]
  ({bbox});
out;
>;
out skel qt;
out;"""

        if self.area:
            instr = temp.format(area='area["name"="{}"]->.a;'.format(self.area),
                                bbox='area.a')
        elif self.bbox:
            instr = temp.format(area='', bbox=self.bbox)
        else:
            raise ValueError('One of area or box argument should be used')

        return self._get_data(instr)


    def get_data_json(self):
        """Function to return the OSM data in JSON formats"""
        temp = """[out:json]
;
{area}
relation
  ["route"="hiking"]
  ["network"="lwn"]
  ["cai_scale"]
  ({bbox});
out;
>;
out skel qt;"""

        if self.area:
            instr = temp.format(area='area["name"="{}"]->.a;'.format(self.area),
                                bbox='area.a')
        elif self.bbox:
            instr = temp.format(area='', bbox=self.bbox)
        else:
            raise ValueError('One of area or box argument should be used')

        return json.loads(self._get_data(instr))


    def get_tags_json(self, debug=False):
        """Function to get the tags plus id for CAI relations"""
        data = self.get_data_json()
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


    def wiki_table(self):
        """Function to convert a CSV file to a wiki table.
        Original code from https://github.com/dlink/vbin/blob/master/csv2wiki
        """
        data = self.get_data_csv(tags='"ref","name",::id')
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

    def geojson(self, osmfile):
        """Function to create a GeoJSON object"""
        cch = CaiCounterHandler()
        cch.apply_file(osmfile, locations=True)
        cch.create_geojson()
        return cch.gjson

    def write(self, to, out_format):
        """Write the data obtained in different format into a file

        :param str to: the path to the output file
        :param str out_format: the required output format
        """
        if out_format == 'csv':
            data = self.get_data_csv()
        elif out_format == 'osm':
            data = self.get_data_osm()
        elif out_format == 'wikitable':
            data = self.wiki_table()
        elif out_format == 'json':
            data = self.get_data_json()
        elif out_format == 'tags':
            data = self.get_tags_json()
        elif out_format == 'geojson':
            osm = self.get_data_osm()
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.osm') as fi:
                fi.write(osm)
            data = self.geojson(fi.name)
            with open(to, 'w') as f:
                geojson.dump(data, f)
            os.remove(fi.name)
            return True
        else:
            raise ValueError('Only csv, osm, wikitable, json, tags format are '
                             'supported')
        with open(to, 'w') as fil:
            fil.write(data)
