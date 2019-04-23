#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar  3 08:51:30 2019

@author: lucadelu
"""

import osmium
import copy
import geojson
import shapely.wkt as wktlib
from shapely.geometry import MultiLineString
from shapely.geometry import LineString
from shapely.ops import transform
import pyproj
from functools import partial

from .functions import WriteDictToCSV

# column to create the csv with route informations
ROUTE_COLUMNS = ['id','name','ref', 'cai_scale', 'from', 'to', 'distance',
                 'source', 'source:ref', 'maintainer', 'description']
# highway classification
OTHERS_WAYS = ['cycleway', 'pedestrian', 'steps', 'via_ferrata']
ASPHALT_WAYS = ['primary', 'primary_link', 'secondary', 'secondary_link',
                'tertiary', 'tertiary_link', 'unclassified', 'residential',
                'service', 'living_street', 'road']
NATURAL_WAYS = ['track']
OFFROAD_WAYS = ['footway', 'path', 'bridleway']
# surface classification
ASPHALT_SURFACE = ['asphalt', 'concrete', 'concrete:plates', 'paved']
OFFROAD_SURFACE = ['compacted', 'dirt', 'grass', 'gravel', 'ground', 'unpaved']
CONCRETE_SURFACE = ['cobblestone', 'cobblestone:flattened', 'paving_stones',
                    'pebblestone', 'sett', 'grass_paver']
OTHERS_SURFACE = ['metal', 'wood']
# WKT class from osmium
WKTFAB = osmium.geom.WKTFactory()

# classes to parse osm and get way and relations
class CaiRoutesHandler(osmium.SimpleHandler):
    """Class to parse CAI routes from OSM file and return them in different
    format"""
    def __init__(self, separator=","):
        osmium.SimpleHandler.__init__(self)
        self.count = 0
        self.routes = {}
        self.ways = {}
        self.gjson = None
        self.wjson = None
        self.sep = separator
        self.total = 0

    def way(self, way):
        """Function to parse ways"""
        try:
            self.ways[way.id] = {}
            self.ways[way.id]['geom'] = WKTFAB.create_linestring(way)
            self.ways[way.id]['tags'] = way.tags
        except Exception:
            pass

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

    def length(self, epsg="EPSG:3035"):
         """Function to return the total lenght of routes

         :param str epsg: the EPSG code string to use
         """
         project = partial(pyproj.transform, pyproj.Proj(init='EPSG:4326'),
                           pyproj.Proj(init=epsg))
         alreadid = []
         for k, v in self.routes.items():
             lines = []
             for w in v['elems']:
                 if w not in alreadid:
                     lines.append(wktlib.loads(self.ways[w]))
                     alreadid.append(w)
             geom = MultiLineString(lines)
             geomm = transform(project, geom)
             self.total += geomm.length


    def create_routes_geojson(self):
        """Function to create GeoJSON geometries for routes"""
        features = []
        for k, v in self.routes.items():
            lines = []
            for w in v['elems']:
                lines.append(wktlib.loads(self.ways[w]['geom']))
            geom = MultiLineString(lines)
            self.routes[k]['geom'] = geom
            feat = geojson.Feature(geometry=geom,
                                   properties=self.routes[k]['tags'])
            features.append(feat)
        self.gjson = geojson.FeatureCollection(features)

    def create_way_geojson(self, infomont=False):
        """Function to create GeoJSON geometries for ways

        :param bool infomont: perform infomont checks
        """
        features = []
        for k, v in self.ways.items():
            geom = LineString(wktlib.loads(v['geom']))
            tags = {'id': k}
            for p in v['tags']:
                tags[p.k] = p.v
            if infomont:
                outags = {}
                highway = tags['highway']
                if highway in ASPHALT_WAYS:
                    outags['TIPOLOGIA'] = '01'
                elif highway in OTHERS_WAYS:
                    outags['TIPOLOGIA'] = '99'
                elif highway in OFFROAD_WAYS:
                    outags['TIPOLOGIA'] = '03'
                elif highway in NATURAL_WAYS:
                    outags['TIPOLOGIA'] = '02'
                else:
                    print(highway)

                if 'surface' in tags.keys():
                    surface = tags['surface']
                    if surface in ASPHALT_SURFACE:
                        outags['CARATTER'] = '01'
                    elif surface in OFFROAD_SURFACE:
                        outags['CARATTER'] = '02'
                    elif surface in CONCRETE_SURFACE:
                        outags['CARATTER'] = '03'
                    elif surface in OTHERS_SURFACE:
                        outags['CARATTER'] = '00'
                    else:
                        print(surface)
                else:
                    if highway == 'via_ferrata':
                        outags['CARATTER'] = '00'
                    if highway in ['path', 'track']:
                        outags['CARATTER'] = '02'
                    if highway in ASPHALT_WAYS:
                        outags['CARATTER'] = '01'
                    elif highway in OTHERS_WAYS:
                        outags['CARATTER'] = '01'
                if 'ref' in tags.keys():
                    outags['Nume'] = tags.get('ref')
                if 'name' in tags.keys():
                    outags['Denomi'] = tags.get('name')
                if 'ref:rei' in tags.keys():
                    outags['COD_REI'] = tags['ref:rei']
                if 'cai_scale' in tags.keys():
                    outags['PerDif'] = tags['cai_scale']

                tags = outags

            feat = geojson.Feature(geometry=geom, properties=tags)
            features.append(feat)
        self.wjson = geojson.FeatureCollection(features)


    def write_geojson(self, out, typ='route'):
        """Function to write GeoJSON file

        :param str out: the path to the output GeoJSON file
        :param str typ: the type of GeoJSON to write, route or way are the two
                        accepted values
        """
        with open(out, 'w') as f:
            if typ == 'route':
                if self.gjson is None:
                    self.create_routes_geojson()
                geojson.dump(self.gjson, f)
            elif typ == 'way':
                if self.wjson is None:
                    self.create_way_geojson()
                geojson.dump(self.wjson, f)
            else:
                raise ValueError("Accepted value for typ option are: 'route' "
                                 "and 'way'")

    def write_relation_members_infomont(self, out, text=True):
        """Function to return a string or a list with all the relation and its
           members as comma separated values

        :param str out: the path to the output CSV file
        :param bool text: use internally text (True, defaul) or list to write
                          info
        """
        mystr = "id_relation{}id_way\n".format(self.sep)
        if text:
            outext = mystr
        else:
            outext = [mystr]
        for k, v in self.routes.items():
            for w in v['elems']:
                mystr = "{rel}{sep}{way}\n".format(rel=k, sep=self.sep, way=w)
                if text:
                    outext += mystr
                else:
                    outext += [mystr]
        with open(out, 'w') as csvfile:
            if text:
                csvfile.write(outext)
            else:
                csvfile.writelines(outext)
        return

    def write_relations_infomont(self, out):
        """Function to return routes info in csv format

        :param str out: the path to the output CSV file
        """
        WriteDictToCSV(out, ROUTE_COLUMNS, self.routes)


class CaiStatsHandler(osmium.SimpleHandler):
    """Class to parse stats about CAI routes"""
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.comment = None
        self.user = None
        self.rels = []
        self.routes = {}
        self.ways = {}
        self.changes = []

    def changeset(self, c):
        if self.user:
            if self.user == c.user and not self.comment:
                self.changes.append(copy.deepcopy(c))
            elif self.user == c.user and self.comment:
                if self.comment in c.comment:
                    self.changes.append(copy.deepcopy(c))
        elif self.comment:
            if self.comment in c.comment:
                self.changes.append(copy.deepcopy(c))
        else:
            self.changes.append(copy.deepcopy(c))

    def set_variables(self, comment, user=None):
        """Set the useful variables for analysis

        :param str comment: the text in the comment to search
        :param str user: the name of the user
        """
        self.comment = comment
        self.user = user


    def way(self, way):
        """Function to parse ways"""
        try:
            self.ways[way.id] = WKTFAB.create_linestring(way)
        except Exception:
            pass

    def relation(self, rel):
        """Function to parse relations"""
        members = []
        tags = {}
        self.rels.append(rel)
        for t in rel.tags:
            tags[t.k] = t.v
        if 'cai_scale' in tags.keys():
            if self.user and self.user != rel.user:
                return
            for mem in rel.members:
                if mem.type == 'w':
                    members.append(mem.ref)
            tags['id'] = rel.id
            self.routes[rel.id] = {'tags': tags, 'elems': members}
        else:
            return
