#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 13 07:28:20 2018

@author: lucadelu
"""

import sys
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
        values = {'data': instr}
        data = urllib.parse.urlencode(values)
        data = data.encode('utf-8') # data should be bytes
        req = urllib.request.Request(self.url, data)
        resp = urllib.request.urlopen(req)
        respData = resp.read()
        
        return respData.decode(encoding='utf-8',errors='ignore')
        

    def get_data_csv(self, csvheader = False):
        if csvheader:
            self.csvheader = True
        temp = """[out:csv(::id,"name","ref";{csvh};"{sep}")]
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
                                sep=self.separator)
        elif self.bbox:
            instr = temp.format(area='', bbox=self.bbox,
                                csvh=str(self.csvheader).lower(),
                                sep=self.separator)
        else:
            raise ValueError('One of area or box argument should be used')
            
        return self._get_data(instr)


    def get_data_osm(self):
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


    def write(self, to, typ=None):
        fil = open(to, 'w')
        if typ == 'csv':
            fil.write(self.get_data_csv())
        elif typ == 'osm':
            fil.write(self.get_data_osm())
        elif typ == 'wikitable':
            fil.write(self.wiki_table())
        else:
            raise ValueError('Only csv, osm, wikitable format are supported')
