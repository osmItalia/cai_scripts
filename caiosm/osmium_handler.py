#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar  3 08:51:30 2019

@author: lucadelu
"""

import osmium
import copy
from collections import OrderedDict
import shapely.wkt as wktlib
from shapely.geometry import MultiLineString
from shapely.geometry import LineString
from shapely.geometry import mapping
from shapely.geometry import shape
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
OFFROAD_SURFACE = ['compacted', 'dirt', 'grass', 'gravel', 'ground', 'unpaved',
                   'fine_gravel', 'earth', 'rock', 'mud', 'stone']
CONCRETE_SURFACE = ['cobblestone', 'cobblestone:flattened', 'paving_stones',
                    'pebblestone', 'sett', 'grass_paver', 'cement']
OTHERS_SURFACE = ['metal', 'wood', 'unknown']
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

    def __init__(self, separator=",", infomont=False, debug=False):
        """Inizialize function

        :param str separator: the separator string for CSV output
        :param bool infomont: if the output should follow Infomont format
        """

        osmium.SimpleHandler.__init__(self)
        self.debug = debug
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
                            'properties': OrderedDict([('IDPerc', 'str'),
                                                       ('IDtrat', 'str')])}
        if self.infomont:
            self.route_schema['properties'] = OrderedDict([('IDPerc', 'str'),
                                                           ('Nume', 'str'),
                                                           ('Denomi', 'str'),
                                                           ('rwn_name', 'str'),
                                                           ('COD_REI', 'str'),
                                                           ('PerDif', 'str'),
                                                           ('segni', 'str')])
            self.way_schema['properties'] = OrderedDict([('osm_id_way', 'int'),
                                                         ('TIPOLOGIA', 'str'),
                                                         ('CARATTER', 'str'),
                                                         ('IDTrat', 'str')])

    def way(self, way):
        """Function to parse ways"""
        self.members[way.id] = []
        self.ways[way.id] = {}
        try:
            self.ways[way.id]['geom'] = WKTFAB.create_linestring(way)
        except Exception:
            print("Error creating geometry for way {}".format(way.id))
        tags = {'id': way.id}
        for p in way.tags:
            tags[p.k] = p.v
        self.ways[way.id]['tags'] = tags

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

    def _create_schema(self, typ):
        """Create the schema for geojson output

        :param str typ: type of the schema to improve, parameter could be route
                        or way
        """
        outdict = {}
        if self.debug:
            print("In create schema")
        if typ == 'route':
            for v in self.routes.values():
                if set(outdict.keys()) != set(v['tags'].keys()):
                    for t in v['tags'].keys():
                        if t not in outdict.keys():
                            outdict[t] = 'str'
            self.route_schema['properties'] = outdict
        if typ == 'way':
            for v in self.ways.values():
                if set(outdict.keys()) != set(v['tags'].keys()):
                    for t in v['tags'].keys():
                        if t not in outdict.keys():
                            outdict[t] = 'str'
            self.way_schema['properties'] = outdict


    def length(self, epsg="EPSG:3035", unit='m'):
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
                     lines.append(wktlib.loads(self.ways[w]['geom']))
                     alreadid.append(w)
             # create the geometry
             geom = MultiLineString(lines)
             geomm = transform(project, geom)
             # sum to total
             total += geomm.length
         if unit == 'km':
             total = round(round(total) / 1000, 1)
         elif unit == 'm':
             total = round(total)
         else:
             print("Unit not supported, reported in meters")
         return total


    def create_routes_geojson(self):
        """Function to create GeoJSON geometries for routes"""
        for k, v in self.routes.items():
            lines = []
            for w in v['elems']:
                self.members[w].append(k)
                lines.append(wktlib.loads(self.ways[w]['geom']))
            geom = MultiLineString(lines)
            self.routes[k]['geom'] = geom
            tags = self.routes[k]['tags']
            tagskey = sorted(tags.keys())
            # run operations to be compliant with infomont format
            if self.infomont:
                outags = OrderedDict()
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
                        if 'non segnalato' in tags['symbol:it']:
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

    def create_way_geojson(self, prefix=None):
        """Function to create GeoJSON geometries for ways"""
        features = []
        for k, v in self.ways.items():
            geom = LineString(wktlib.loads(v['geom']))
            if self.debug:
                print(v)
            # run operations to be compliant with infomont format
            if self.infomont:
                outags = OrderedDict([('osm_id_way', k)])
                try:
                    highway = v['tags']['highway']
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
                    if self.debug:
                        print(highway)
                # check if the highway has surface tag, if it exist use it
                # otherwise use highway tag to set the surface
                if 'surface' in v['tags'].keys():
                    surface = v['tags']['surface']
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
                        if surface and self.debug:
                            print(surface)
                else:
                    if highway == 'via_ferrata':
                        outags['CARATTER'] = '00'
                    elif highway == 'footway':
                        if 'footway' in v['tags'].keys():
                            outags['CARATTER'] = '01'
                        elif 'sidewalk' in v['tags'].keys():
                            outags['CARATTER'] = '01'
                        else:
                            outags['CARATTER'] = '02'
                    elif highway in ['path', 'track', 'bridleway']:
                        outags['CARATTER'] = '02'
                    elif highway in ASPHALT_WAYS:
                        outags['CARATTER'] = '01'
                    elif highway in OTHERS_WAYS:
                        outags['CARATTER'] = '01'
                    else:
                        outags['CARATTER'] = ''
                outags
            else:
                outags = v['tags']

            feat = {'geometry': mapping(geom), 'properties': outags}
            features.append(feat)
        if self.infomont:
            features = split_at_intersection(features, prefix)
        self.wjson = features


    def write_geojson(self, out, typ='route', driv="GeoJSON", enc='utf-8',
                      epsg=4326):
        """Function to write GeoJSON file

        :param str out: the path to the output GeoJSON file
        :param str typ: the type of GeoJSON to write, route - way - members are
                        the three accepted values
        :param str driv: the OGR driver to use, default is GeoJSON
        :param str enc: the encoding value to use
        """
        if self.debug:
            print('Starting writing OGR output')
        if typ == 'route':
            if not self.infomont:
                self._create_schema('route')
            schema = self.route_schema
        elif typ == 'way':
            if not self.infomont:
                self._create_schema('way')
            schema = self.way_schema
        elif typ == 'members':
            schema = self.memb_schema
        else:
            raise ValueError("Accepted value for typ option are: 'route',"
                                 " 'way' and 'members'")
        if self.debug:
            print(schema)
        if epsg != 4326:
            inepsg = "EPSG:{}".format(epsg)
            project = partial(pyproj.transform, pyproj.Proj(init='EPSG:4326'),
                              pyproj.Proj(init=inepsg))
        with fiona.open(out, 'w', driver=driv, crs=fiona.crs.from_epsg(epsg),
                        schema=schema, encoding=enc) as f:
            if typ == 'route':
                if self.debug:
                    print("In route")
                if len(self.gjson) == 0:
                    self.create_routes_geojson()
                if self.debug:
                    print("Number of route {}".format(len(self.gjson)))
                for feat in self.gjson:
                    if epsg != 4326:
                        newgeom = transform(project, shape(feat['geometry']))
                        feat['geometry'] = mapping(newgeom)
                    try:
                        f.write(feat)
                    except:
                        for sc in schema['properties'].keys():
                            if sc not in feat['properties'].keys():
                                feat['properties'][sc] = ''
                        f.write(feat)
            elif typ == 'way':
                if self.debug:
                    print("In way")
                if len(self.wjson) == 0:
                    self.create_way_geojson()
                if self.debug:
                    print("Number of way {}".format(len(self.wjson)))
                for feat in self.wjson:
                    if epsg != 4326:
                        newgeom = transform(project, shape(feat['geometry']))
                        feat['geometry'] = mapping(newgeom)
                    try:
                        f.write(feat)
                    except:
                        for sc in schema['properties'].keys():
                            if sc not in feat['properties'].keys():
                                feat['properties'][sc] = ''
                        f.write(feat)
            elif typ == 'members':
                membs = self.write_relation_members_infomont_geo()
                for feat in membs:
                    if epsg != 4326:
                        newgeom = transform(project, shape(feat['geometry']))
                        feat['geometry'] = mapping(newgeom)
                    f.write(feat)
            else:
                raise ValueError("Accepted value for typ option are: 'route',"
                                 " 'way' and 'members'")
        if driv == "ESRI Shapefile":
            cpgfile = out.replace('.shp', '.cpg')
            with open(cpgfile, 'w') as cpg:
                cpg.write(enc)

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
        if self.debug:
            print("Before WriteDictToCSV")
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
