#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 00:41:04 2019

@author: lucadelu
"""
import os
from .osmium_handler import CaiRoutesHandler

# class to get data from overpass and convert in infomont system
class CaiOsmInfomont:
    def __init__(self, inpath):
        self.cch = CaiRoutesHandler()
        if os.path.exists(inpath):
            self.cch.apply_file(inpath, locations=True)
        else: 
            raise IOError("{} does not exist".format(inpath))
        self.cch.create_way_geojson(infomont=True)

    def write_ways(self, outpath):
        """Write routes' ways in GeoJSON format 
        
        :param str outpath: the path to the output GeoJSON file
        """
        self.cch.write_geojson(outpath, typ='way')
        
    def write_routes(self, outpath):
        """Write routes info in CSV format
        
        :param str outpath: the path to the output CSV file
        """
        self.cch.write_relations_infomont(outpath)
        
    def write_routes_ways(self, outpath):
        """Write routes info in CSV format
        
        :param str outpath: the path to the output CSV file
        """
        self.cch.write_relation_members_infomont(outpath)
    
    def write_all(self, outdir):
        """Write all info ready to be imported in infomont
        """
        self.write_routes(os.path.join(outdir, 'route.csv'))
        self.write_routes_ways(os.path.join(outdir, 'members.csv'))
        self.write_ways(os.path.join(outdir, 'ways.geojson'))
