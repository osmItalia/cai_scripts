#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 13 07:28:20 2018

@author: lucadelu
"""

import sys
import json
import urllib.request

class CaiOsmData:
    
    def __init__(self, area=None, bbox=None, outtype='csv'):
        self.area = area
        self.bbox = bbox
        self.outtype = outtype
        self.url = "http://overpass-api.de/api/interpreter?"
        self.csvheader = False
        self.separator = '|'


    def _get_data(self, instr):
        """Private function to obtain the OSM data from overpass api

        :param str instr: the string with the overpass syntax
        """
        values = {'data': instr}
        data = urllib.parse.urlencode(values)
        data = data.encode('utf-8') # data should be bytes
        req = urllib.request.Request(self.url, data)
        resp = urllib.request.urlopen(req)
        respData = resp.read()
        
        return respData.decode(encoding='utf-8',errors='ignore')
        

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
        data = self.get_data_csv()
        # read it
        
        rows = data.splitlines()
        table = []
        for fields in rows:
            row = []
            for field in fields.split(self.separator):
                field = field.strip()
                row.append(field)
            row.extend(['', ''])
            table.append(row)
        # output wiki format
        out = '{| class="wikitable sortable mw-collapsible mw-collapsed" \n'
        out += '|-\n'
        out += '!Ref\n!Nome\n!Link route\n!%completamento\n!note\n'
        i = 0
        for row in sorted(table, key=lambda row: row[2]):
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
        else:
            raise ValueError('Only csv, osm, wikitable, json, tags format are '
                             'supported')
        fil = open(to, 'w')
        fil.write(data)
        fil.close()