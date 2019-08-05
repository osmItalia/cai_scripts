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
import tempfile
from datetime import date
from datetime import timedelta
import dateutil.parser
import xmltodict
import osmium
from .functions import invert_bbox
from .functions import check_network
from .osmium_handler import CaiRoutesHandler

DIRFILE = os.path.dirname(os.path.realpath(__file__))

class CaiOsmBase:
    """Base class to get CAI data using Overpass API"""

    def __init__(self, area=None, bbox=None, bbox_inverted=False,
                 separator='|', debug=False, timeout=2500):
        """Inizialize

        :param str area: the name of the area of interest
        :param str bbox: a string with the bounding box of the area, needed
                         format is YMIN,XMIN,YMAX,XMAX
        :param bool bbox_inverted: set True id the bbox format is
                                    XMIN,YMIN,XMAX,YMAX
        :param str separator: the separator to use for CSV
        :param bool debug: print debug information
        :param int timeout: the timeout value for overpass
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
        self.timeout = timeout

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

class CaiOsmData(CaiOsmBase):
    """Class to get CAI data using Overpass API and convert in different
       formats"""
    def __init__(self, area=None, bbox=None, bbox_inverted=False,
                 separator='|', debug=False, timeout=2500):
        """Inizialize

        :param str area: the name of the area of interest
        :param str bbox: a string with the bounding box of the area, needed
                         format is YMIN,XMIN,YMAX,XMAX
        :param bool bbox_inverted: set True id the bbox format is
                                    XMIN,YMIN,XMAX,YMAX
        :param str separator: the separator to use for CSV
        :param bool debug: print debug information
        :param int timeout: the timeout value for overpass
        """
        super(CaiOsmData, self).__init__(area=area, bbox=bbox,
                                          bbox_inverted=bbox_inverted,
                                          separator=separator, debug=debug)
    def get_data_csv(self, csvheader=False, tags='::id,"name","ref"',
                     network='lwn'):
        """Function to return data in CSV format

        :param bool csvheader: show or hide the csv header, default hidden
        :param str tags: a list of tags to show in the csv
        """
        if csvheader:
            self.csvheader = True
        temp = """[timeout:{time}][out:csv({cols};{csvh};"{sep}")]
;
{area}
{query}
out;
"""
        network = check_network(network)
        if self.area:
            instr = temp.format(area='area["name"="{}"]->.a;'.format(self.area),
                                csvh=str(self.csvheader).lower(),
                                sep=self.separator, cols=tags,
                                query=self.query.format(netw=network,
                                                        bbox='area.a'),
                                time=self.timeout)
        elif self.bbox:
            instr = temp.format(area='', csvh=str(self.csvheader).lower(),
                                sep=self.separator, cols=tags,
                                query=self.query.format(netw=network,
                                                        bbox=self.bbox),
                                time=self.timeout)
        else:
            instr = temp.format(area='', csvh=str(self.csvheader).lower(),
                                sep=self.separator, cols=tags,
                                query=self.query.format(netw=network,
                                                        bbox=''),
                                time=self.timeout)

        return self._get_data(instr)


    def get_data_osm(self, sort=True, network='lwn', remove=True):
        """Function to return data in the original OSM format

        :param str network: the network level to query, default 'lwn'
        """
        temp = """[timeout:{time}][out:xml]
;
{area}
{query}
out;
>;
out qt;
out;"""

        network = check_network(network)
        if self.area:
            instr = temp.format(area='area["name"="{}"]->.a;'.format(self.area),
                                query=self.query.format(netw=network,
                                                        bbox='area.a'),
                                time=self.timeout)
        elif self.bbox:
            instr = temp.format(area='', query=self.query.format(netw=network,
                                                                 bbox=self.bbox),
                                time=self.timeout)
        else:
            instr = temp.format(area='', query=self.query.format(netw=network,
                                                                 bbox=''),
                                time=self.timeout)

        data = self._get_data(instr)
        #import pdb; pdb.set_trace()
        #mir = osmium.MergeInputReader()
        #mir.add_buffer(data, "osm")
        #print("before with")
        #with tempfile.NamedTemporaryFile(suffix=".osm") as temp_osm:
        #    os.unlink(temp_osm.name)
        #    print("before writer")
        #    wh = osmium.WriteHandler(temp_osm.name)
        #    mir.apply(wh)
        #    wh.close()
        #    print("before read")
        #    output = temp_osm.read()
        #pdb.set_trace()
        #return output
        if sort:
            mir = osmium.MergeInputReader()
            mir.add_buffer(data.encode('utf-8'), "osm")
            # the code stop here after printing the xml osm data
            tempname = tempfile.mkstemp(suffix='.osm')[1]

            with open(tempname, 'w') as temp_osm:
                os.unlink(temp_osm.name)
                wh = osmium.WriteHandler(temp_osm.name)
                mir.apply(wh, idx="flex_mem")
                wh.close()
                temp_osm.close()
            with open(tempname, 'r') as temp_osm:
                data = temp_osm.read()
            if remove:
                os.remove(tempname)
        return data

    def get_data_json(self, network='lwn'):
        """Function to return the OSM data in JSON formats

        :param str network: the network level to query, default 'lwn'
        """
        temp = """[timeout:{time}][out:json]
;
{area}
{query}
out;
>;
out qt;"""

        network = check_network(network)
        if self.area:
            instr = temp.format(area='area["name"="{}"]->.a;'.format(self.area),
                                query=self.query.format(netw=network,
                                                        bbox='area.a'),
                                time=self.timeout)
        elif self.bbox:
            instr = temp.format(area='',query=self.query.format(netw=network,
                                                                bbox=self.bbox),
                                time=self.timeout)
        else:
            instr = temp.format(area='',query=self.query.format(netw=network,
                                                                bbox=''),
                                time=self.timeout)

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
        :param str network: the network level to query, default 'lwn'
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
            if self.cch:
                self.cch.write_geojson(out, 'route')
                return True
            else:
                data = json.dumps(data)
        else:
            raise ValueError('Only csv, osm, wikitable, json, tags, geojson '
                             'format are supported')
        with open(out, 'w') as fil:
            fil.write(data)
        return True


class CaiOsmRoute(CaiOsmData):
    """Class to get CAI routes using Overpass API and convert in different
       formats"""
    def __init__(self, area=None, bbox=None, bbox_inverted=False,
                 separator='|', debug=False, timeout=2500):
        """Inizialize

        :param str area: the name of the area of interest
        :param str bbox: a string with the bounding box of the area, needed
                         format is YMIN,XMIN,YMAX,XMAX
        :param bool bbox_inverted: set True id the bbox format is
                                    XMIN,YMIN,XMAX,YMAX
        :param str separator: the separator to use for CSV
        :param bool debug: print debug information
        :param int timeout: the timeout value for overpass
        """
        super(CaiOsmRoute, self).__init__(area=area, bbox=bbox, timeout=timeout,
                                          bbox_inverted=bbox_inverted,
                                          separator=separator, debug=debug)
        self.cch = None
        self.lenght = None
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
        if self.lenght:
            return self.lenght
        if self.cch is None:
            self.cch.get_cairoutehandler(network)
        self.lenght = self.cch.length()
        return self.lenght

    def get_cairoutehandler(self, network='lwn', infomont=False):
        """Function to download osm data and create CaiRoutesHandler instance

        :param str network: the network level to query, default 'lwn'
        """
        data = self.get_data_osm(sort=False, network=network)
        self.cch = CaiRoutesHandler(infomont=infomont)
        # trick to solve the problem that overpass data ar not sorted
        mir = osmium.MergeInputReader()
        mir.add_buffer(data.encode('utf-8'), "osm")
        mir.apply(self.cch, idx="flex_mem", simplify=True)
        return True

    def get_geojson(self, network='lwn'):
        """Function to get a GeoJSON object

        :param str network: the network level to query, default 'lwn'
        """
        if self.cch is None:
            self.get_cairoutehandler(network)
        if len(self.cch.gjson) == 0:
            self.cch.create_routes_geojson()
        return self.cch.gjson


class CaiOsmOffice(CaiOsmData):
    """Class to get CAI offices using Overpass API and convert in different
       formats"""

    def __init__(self, area='Italia', bbox=None, bbox_inverted=False,
                 separator='|', debug=False, timeout=2500):
        """Inizialize

        :param str area: the name of the area of interest
        :param str bbox: a string with the bounding box of the area, needed
                         format is YMIN,XMIN,YMAX,XMAX
        :param bool bbox_inverted: set True id the bbox format is
                                    XMIN,YMIN,XMAX,YMAX
        :param str separator: the separator to use for CSV
        :param bool debug: print debug information
        :param int timeout: the timeout value for overpass
        """
        super(CaiOsmOffice, self).__init__(area=area, bbox=bbox,
                                           timeout=timeout,
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

    def get_geojson(self, network=''):
        """Function to get a GeoJSON object"""
        data = self.get_data_json(network='')
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
    """Class to get CAI source:ref values using Overpass API and convert in
    different formats"""

    def __init__(self, area='Italia', bbox=None, separator='|', debug=False,
                 timeout=2500):
        """Inizialize

        :param str area: the name of the area of interest
        :param str bbox: a string with the bounding box of the area, needed
                         format is YMIN,XMIN,YMAX,XMAX
        :param bool bbox_inverted: set True id the bbox format is
                                    XMIN,YMIN,XMAX,YMAX
        :param str separator: the separator to use for CSV
        :param bool debug: print debug information
        :param int timeout: the timeout value for overpass
        """
        super(CaiOsmSourceRef, self).__init__(area=area, bbox=bbox,
                                              timeout=timeout,
                                              separator=separator, debug=debug)

        self.query = """
relation
  ["route"="hiking"]
  {netw}
  ["cai_scale"]
  ["source:ref"]
  ({bbox});
"""
        self.codespath = os.path.join(DIRFILE, 'data', 'cai_codes.csv')
        self.osm_codes = None
        self.cai_codes = []
        self.cai_codes_dict = {}
        self.cai_codes_reg = {}
        if not os.path.exists(self.codespath):
            self.download_csv_file()
        else:
            self._read_codes()

    def _read_codes(self):
        """Read the code from the file"""
        with open(self.codespath) as fi:
            cai_lines = fi.readlines()
        for line in cai_lines :
            vals = line.split(',')
            self.cai_codes.append(vals)
            if vals[4] in ['', 'Regione']:
                continue
            self.cai_codes_dict[vals[0]] = {'name': vals[1], 'city': vals[2],
                                            'region': vals[4]}
            if vals[4] not in self.cai_codes_reg.keys():
                self.cai_codes_reg[vals[4]] = []
            self.cai_codes_reg[vals[4]].append({'name': vals[1], 'id': vals[0],
                                                'city': vals[2]})

    def download_csv_file(self, url="https://docs.google.com/spreadsheets/d/e/"
                          "2PACX-1vQWs9ydWZEMGust3TRuJX-HXLTnjAM5TBQ4XiKA_BSb4"
                          "7cfh70n-5otAOmSoqDzm8GHnFe039xnsqAz/pub?gid=1089220"
                          "791&single=true&output=csv"):
        """Function to download data into CSV file"""
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req)
        respData = resp.read()
        with open(self.codespath, 'w') as fi:
         fi.write(respData.decode(encoding='utf-8', errors='ignore'))
        self._read_codes()

    def get_list_codes(self, network='lwn'):
        """Function to return a list of the CAI codes used in OSM

        :param str network: the network level to query, default 'lwn'
        """
        if not self.osm_codes:
            osm_codes = self.get_data_csv(csvheader=False,
                                          tags='"source:ref"',
                                          network=network)
            self.osm_codes = list(set(osm_codes.splitlines()))
        return self.osm_codes

    def get_names_codes(self, network='lwn'):
        """Function to return a list of the CAI codes and name used in OSM

        :param str network: the network level to query, default 'lwn'
        """
        output = []
        for osm in self.get_list_codes(network=network):
            if osm in self.cai_codes_dict.keys():
                output.append([osm, self.cai_codes_dict[osm]['name'],
                               self.cai_codes_dict[osm]['region']])
        return output

    def get_codes_region(self, region, network='lwn'):
        """Return CAI codes for the selected region

        :param str region: The region name
        """
        region = region.upper()
        if region in self.cai_codes_reg.keys():
            return self.cai_codes_reg[region]
        else:
            if 'VALLE' in region:
                return self.cai_codes_reg["VALLE D'AOSTA"]
            elif 'TRENTINO' in region:
                return self.cai_codes_reg["TRENTINO-ALTO ADIGE"]
            elif 'FRIULI' in region:
                return self.cai_codes_reg["FRIULI-VENEZIA GIULIA"]
        return "Region '{}' not found".format(region)

    def write(self, out, out_format, network=False):
        """Write the data obtained in different format into a file

        :param str out: the path to the output file
        :param str out_format: the required output format
        :param str network: the network level to query, default 'lwn'
        """
        if out_format == 'codes':
            data = self.get_list_codes(network=network)
        elif out_format == 'names':
            data = self.get_names_codes(network=network)
        else:
            raise ValueError('Only codes, names format are supported')
        with open(out, 'w') as fil:
            for d in data:
                fil.write("{}\n".format(self.separator.join(d)))
        return True

class CaiOsmRouteSourceRef(CaiOsmRoute):
    """Class to get CAI routes for a single CAI group using Overpass API and
    convert in different formats"""

    def __init__(self, sourceref, separator='|', debug=False, timeout=2500):
        """Inizialize

        :param str area: the name of the area of interest
        :param str bbox: a string with the bounding box of the area, needed
                         format is YMIN,XMIN,YMAX,XMAX
        :param bool bbox_inverted: set True id the bbox format is
                                    XMIN,YMIN,XMAX,YMAX
        :param str separator: the separator to use for CSV
        :param bool debug: print debug information
        :param int timeout: the timeout value for overpass
        """
        super(CaiOsmRouteSourceRef, self).__init__(separator=separator,
                                                   timeout=timeout,
                                                   debug=debug)
        source = '["source:ref"="{code}"]'.format(code=sourceref)
        query = """
relation
  ["route"="hiking"]
  {netw}
  ["cai_scale"]
"""
        self.query = query + source + """;"""

class CaiOsmRouteDiff(CaiOsmBase):
    """Class to get CAI route diff using Overpass API and convert in different
       formats"""

    def __init__(self, startdate=None, enddate=None, daydiff=1, area=None,
                 bbox=None, sourceref=None, separator='|', debug=False,
                 timeout=2500):
        """Inizialize

        :param str area: the name of the area of interest
        :param str bbox: a string with the bounding box of the area, needed
                         format is YMIN,XMIN,YMAX,XMAX
        :param bool bbox_inverted: set True id the bbox format is
                                    XMIN,YMIN,XMAX,YMAX
        :param str separator: the separator to use for CSV
        :param bool debug: print debug information
        :param int timeout: the timeout value for overpass
        """
        super(CaiOsmRouteDiff, self).__init__(area=area, bbox=bbox,
                                              timeout=timeout,
                                              separator=separator, debug=debug)
        if not startdate:
            yesterday = date.today() - timedelta(daydiff)
            startdate = "{}T00:00:00Z".format(yesterday.isoformat())
        self.startdate = dateutil.parser.parse(startdate)
        if not enddate:
            enddate = "{}T00:00:00Z".format(date.today().isoformat())
        self.enddate = dateutil.parser.parse(enddate)
        header = '[out:xml][adiff:"{start}","{end}"];'.format(start=self.startdate,
                                                              end=self.enddate)
        query = header + """{area}
relation
  ["route"="hiking"]
  {netw}
  ["cai_scale"]
"""
        if sourceref:
            source = '["source:ref"="{code}"]'.format(code=sourceref)
            self.query = query + source
        else:
            self.query = query
        if area or bbox:
            self.query += """({bbox})"""
        self.query += """; (._;>;);out meta geom;"""
        self.osmdata = None

    def get_data_osm(self, network='lwn'):
        """Function to return data in the original OSM format

        :param str network: the network level to query, default 'lwn'
        """

        network = check_network(network)
        if self.area:
            instr = self.query.format(area='area["name"="{}"]->.a;'.format(self.area),
                                      bbox='area.a', netw=network)
        elif self.bbox:
            instr = self.query.format(area='', bbox=self.bbox, netw=network)
        else:
            instr = self.query.format(area='', bbox='', netw=network)

        self.osmdata = self._get_data(instr)
        return self.osmdata

    def get_changeset(self, network='lwn'):
        """Return the changeset id

        :param str network: the network level to query, default 'lwn'
        """
        if not self.osmdata:
            self.get_data_osm(network=network)
        jsonosm = xmltodict.parse(self.osmdata)
        output = []
        for change in jsonosm['osm']['action']:
            if 'node' in change.keys():
                data = change['node']
            elif 'way' in change.keys():
                data = change['way']
            elif 'relation' in change.keys():
                data = change['relation']
            else:
                continue
            changedata = dateutil.parser.parse(data['@timestamp'])
            if self.startdate.date() <= changedata.date() <= self.enddate.date():
                changeset = data['@changeset']
                if changeset not in output:
                    output.append(changeset)
        return output

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
        if self.cch is None:
            self.get_cairoutehandler(network)
        self.cch.create_routes_geojson()
        return self.cch.gjson
