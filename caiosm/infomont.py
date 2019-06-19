#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 00:41:04 2019

@author: lucadelu
"""
import os
from .data_from_overpass import CaiOsmRoute

# class to get data from overpass and convert in infomont system
class CaiOsmInfomont:
    """Class to convert OSM data into Infomont schema and create shapefile"""

    def __init__(self, area=None, bbox=None, bbox_inverted=False,
                 driver="ESRI Shapefile", debug=None):
        """Inizialize function
        :param str area: the name of the area of interest
        :param str bbox: a string with the bounding box of the area, needed
                         format is YMIN,XMIN,YMAX,XMAX
        :param bool bbox_inverted: set True id the bbox format is
                                   XMIN,YMIN,XMAX,YMAX
        :param str driver: the OGR driver to use as output
        :param bool debug: print debug information
        """

        self.cor = CaiOsmRoute(area=area, bbox=bbox, debug=debug,
                               bbox_inverted=bbox_inverted)
        self.cor.get_cairoutehandler(infomont=True)
        self.cor.cch.create_way_geojson()
        self.cor.cch.create_routes_geojson()
        self.driver = driver

    def write_ways(self, outpath):
        """Write routes' ways in a OGR format

        :param str outpath: the path to the output file
        """
        self.cor.cch.write_geojson(outpath, typ='way', driv=self.driver)

    def write_routes(self, outpath):
        """Write routes info in a OGR format

        :param str outpath: the path to the output file
        """
        self.cor.cch.write_relations_infomont(outpath)

    def write_routes_geo(self, outpath):
        """Write routes info a OGR format

        :param str outpath: the path to the output file
        """
        self.cor.cch.write_geojson(outpath, typ='route', driv=self.driver)

    def write_routes_ways_geo(self, outpath):
        """Write routes members info in a OGR format

        :param str outpath: the path to the output file
        """
        self.cor.cch.write_geojson(outpath, typ='members', driv=self.driver)

    def write_routes_ways(self, outpath):
        """Write routes members info in CSV format

        :param str outpath: the path to the output file
        """
        self.cor.cch.write_relation_members_infomont(outpath)

    def write_all(self, outdir):
        """Write all info ready to be imported in infomont

        :param str outdir: the path to the directory containing output files
        """
        self.write_routes(os.path.join(outdir, 'sent_perc.csv'))
        self.write_ways(os.path.join(outdir, 'trt_sent.shp'))
        self.write_routes_ways(os.path.join(outdir, 'trt_perc.csv'))

    def write_all_geo(self, outdir):
        """Write all info in a OGR format

        :param str outdir: the path to the directory containing output files
        """
        self.write_routes_geo(os.path.join(outdir, 'sent_perc.shp'))
        self.write_ways(os.path.join(outdir, 'trt_sent.shp'))
        self.write_routes_ways_geo(os.path.join(outdir, 'trt_perc.shp'))
