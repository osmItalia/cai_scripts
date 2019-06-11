#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar  3 08:51:30 2019

@author: lucadelu
"""

import osmium
import copy
import geojson
from collections import OrderedDict
import shapely.wkt as wktlib
from shapely.geometry import MultiLineString
from shapely.geometry import LineString
from shapely.geometry import mapping
from shapely.ops import transform
import fiona
import pyproj
from functools import partial

from .functions import WriteDictToCSV
from .functions import split_at_intersection

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
# route fields name {'old': 'new'}
ROUTE_FIELD = OrderedDict([('IDPerc', 'id'), ('Nume', 'ref'),
                           ('Denomi', 'name'), ('rwn_name', 'rwn:name'),
                           ('COD_REI', 'ref:REI'), ('PerDif', 'cai_scale')])
# WKT class from osmium
WKTFAB = osmium.geom.WKTFactory()

# classes to parse osm and get way and relations
class CaiRoutesHandler(osmium.SimpleHandler):
    """Class to parse CAI routes from OSM file and return them in different
    format"""

    def __init__(self, separator=",", infomont=False):
        osmium.SimpleHandler.__init__(self)
        self.infomont = infomont
        self.count = 0
        self.routes = {}
        self.ways = {}
        self.members = {}
        self.gjson = []
        self.wjson = []
        self.sep = separator
        self.route_schema = {'geometry': 'MultiLineString',}
        self.way_schema = {'geometry': 'LineString',}
        self.memb_schema = {'geometry': 'LineString',
                            'properties': OrderedDict([('IDPerc', 'int'),
                                                       ('IDtrat', 'int')])}
        if self.infomont:
            self.route_schema['properties'] = OrderedDict([('IDPerc', 'int'),
                                                           ('Nume', 'str'),
                                                           ('Denomi', 'str'),
                                                           ('rwn_name', 'str'),
                                                           ('COD_REI', 'str'),
                                                           ('PerDif', 'str'),
                                                           ('segni', 'str')])
            self.way_schema['properties'] = OrderedDict([('osm_id_way', 'int'),
                                                         ('TIPOLOGIA', 'str'),
                                                         ('CARATTER', 'str'),
                                                         ('IDTrat', 'int')])

    def way(self, way):
        """Function to parse ways"""
        self.members[way.id] = []
        self.ways[way.id] = {}
        try:
            self.ways[way.id]['geom'] = WKTFAB.create_linestring(way)
        except Exception:
            print("Error creating geometry for way {}".format(way.id))
        self.ways[way.id]['tags'] = way.tags

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
         # for each route
         total = 0
         for k, v in self.routes.items():
             lines = []
             # for each member of the route crea a linea and append to the list
             for w in v['elems']:
                 if w not in alreadid:
                     lines.append(wktlib.loads(self.ways[w]))
                     alreadid.append(w)
             # create the geometry
             geom = MultiLineString(lines)
             geomm = transform(project, geom)
             # sum to total
             total += geomm.length
         return total


    def create_routes_geojson(self):
        """Function to create GeoJSON geometries for routes"""
        for k, v in self.routes.items():
            lines = []
            outags = OrderedDict()
            for w in v['elems']:
                self.members[w].append(k)
                lines.append(wktlib.loads(self.ways[w]['geom']))
            geom = MultiLineString(lines)
            self.routes[k]['geom'] = geom
            tags = self.routes[k]['tags']
            tagskey = sorted(tags.keys())
            # run operations to be compliant with infomont format
            if self.infomont:
                for new, old in ROUTE_FIELD.items():
                    if old in tagskey:
                        outags[new] = tags[old]
                    else:
                        outags[new] = ''
                # check the symbol
                # if one of the tags exists check it/them; otherwise set 001
                if 'symbol' in tagskey or 'symbol:it' in tagskey or \
                   'osmc:symbol' in tagskey:
                    # check the tags in order
                    if 'osmc:symbol' in tagskey:
                        if 'red:red:white_stripe' in tags['osmc:symbol'] or \
                           'red:red:white_bar' in tags['osmc:symbol']:
                            if ';' in tags['osmc:symbol']:
                                outags['segni'] = '004'
                            else:
                                outags['segni'] = '002'
                        else:
                            outags['segni'] = '003'
                    elif 'symbol' in tagskey:
                        if 'unmarked' in tags['symbol']:
                            outags['segni'] = '001'
                        elif 'white red flag' in tags['symbol']:
                            if ';' in tags['symbol']:
                                outags['segni'] = '004'
                            else:
                                outags['segni'] = '002'
                        else:
                            outags['segni'] = '003'
                    elif 'symbol:it' in tagskey:
                        if 'non segnalato' in tags['symbol']:
                            outags['segni'] = '001'
                        elif 'su bandierina bianca e rossa' in tags['symbol:it'] \
                             or 'segnavia bianco e rosso' in tags['symbol:it']:
                            if ';' in tags['symbol:it']:
                                outags['segni'] = '004'
                            else:
                                outags['segni'] = '002'
                        else:
                            outags['segni'] = '003'
                else:
                    outags['segni'] = '001'
            else:
                 outags = tags
            feat = {'geometry': mapping(geom), 'properties': outags}
            self.gjson.append(feat)

    def create_way_geojson(self):
        """Function to create GeoJSON geometries for ways

        :param bool infomont: perform infomont checks
        """
        features = []
        for k, v in self.ways.items():
            geom = LineString(wktlib.loads(v['geom']))
            tags = {'id': k}
            for p in v['tags']:
                tags[p.k] = p.v
            # run operations to be compliant with infomont format
            if self.infomont:
                outags = OrderedDict([('osm_id_way', k)])
                try:
                    highway = tags['highway']
                except KeyError:
                    print("way {} without highway tag".format(k))
                    highway = None
                # check the highway tag to set the new value
                if highway is None:
                    outags['TIPOLOGIA'] = '99'
                elif highway in ASPHALT_WAYS:
                    outags['TIPOLOGIA'] = '01'
                elif highway in OTHERS_WAYS:
                    outags['TIPOLOGIA'] = '99'
                elif highway in OFFROAD_WAYS:
                    outags['TIPOLOGIA'] = '03'
                elif highway in NATURAL_WAYS:
                    outags['TIPOLOGIA'] = '02'
                else:
                    print(highway)
                # check if the highway has surface tag, if it exist use it
                # otherwise use highway tag to set the surface
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
                        outags['CARATTER'] = ''
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
                    else:
                        outags['CARATTER'] = ''
                tags = outags

            feat = {'geometry': mapping(geom), 'properties': outags}
            features.append(feat)
        if self.infomont:
            features = split_at_intersection(features)
        self.wjson = features


    def write_geojson(self, out, typ='route', driv="GeoJSON"):
        """Function to write GeoJSON file

        :param str out: the path to the output GeoJSON file
        :param str typ: the type of GeoJSON to write, route - way - members are
                        the three accepted values
        """
        if self.infomont:
            if typ == 'route':
                schema = self.route_schema
            elif typ == 'way':
                schema = self.way_schema
            elif typ == 'members':
                schema = self.memb_schema
        with fiona.open(out, 'w', driver=driv, crs=fiona.crs.from_epsg(4326),
                        schema=schema) as f:
            if typ == 'route':
                if len(self.gjson) == 0:
                    self.create_routes_geojson()
                for feat in self.gjson:
                    f.write(feat)
            elif typ == 'way':
                if len(self.wjson) == 0:
                    self.create_way_geojson()
                for feat in self.wjson:
                    f.write(feat)
            elif typ == 'members':
                membs = self.write_relation_members_infomont_geo()
                for feat in membs:
                    f.write(feat)
            else:
                raise ValueError("Accepted value for typ option are: 'route',"
                                 " 'way' and 'members'")

    def write_relation_members_infomont(self, out):
        """Function to write a csv file with all the relation and its
           members as comma separated values

        :param str out: the path to the output CSV file
        """
        outext = "IDPerc{}IDtrat\n".format(self.sep)
        for feat in self.wjson['features']:
            osmid = feat['properties']['osm_id_way']
            newid = feat['properties']['IDTrat']
            for w in self.members[osmid]:
                mystr = "{rel}{sep}{way}\n".format(rel=w, sep=self.sep,
                                                   way=newid)
                outext += mystr
        with open(out, 'w') as csvfile:
            csvfile.write(outext)
        return True

    def write_relation_members_infomont_geo(self):
        """Function to return a geojson with all the relation and its
           members as comma separated values
        """
        features = []
        for feat in self.wjson:
            osmid = feat['properties']['osm_id_way']
            newid = feat['properties']['IDTrat']
            for w in self.members[osmid]:
                tags = OrderedDict([('IDPerc', w), ('IDtrat', newid)])
                outfeat = {'geometry': feat['geometry'], 'properties': tags}
                features.append(outfeat)
        return features

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
