#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 00:41:04 2019

@author: lucadelu
"""
import os
from .data_from_overpass import CaiOsmRoute
from .functions import geojson2shp

# class to get data from overpass and convert in infomont system
class CaiOsmInfomont:
    def __init__(self, area=None, bbox=None, bbox_inverted=False):
        self.cor = CaiOsmRoute(area=area, bbox=bbox,
                               bbox_inverted=bbox_inverted)
        self.cor.get_cairoutehandler()
        self.cor.cch.create_way_geojson(infomont=True)
        self.cor.cch.create_routes_geojson(infomont=True)

    def write_ways(self, outpath):
        """Write routes' ways in GeoJSON format

        :param str outpath: the path to the output GeoJSON file
        """
        self.cor.cch.write_geojson(outpath, typ='way', infomont=True)

    def write_routes(self, outpath):
        """Write routes info in GeoJSON format

        :param str outpath: the path to the output GeoJSON file
        """
        self.cor.cch.write_relations_infomont(outpath)

    def write_routes_geo(self, outpath):
        """Write routes info in GeoJSON format

        :param str outpath: the path to the output GeoJSON file
        """
        self.cor.cch.write_geojson(outpath, typ='route', infomont=True)

    def write_routes_ways_geo(self, outpath):
        """Write routes members info in GeoJSON format

        :param str outpath: the path to the output GeoJSON file
        """
        self.cor.cch.write_geojson(outpath, typ='members', infomont=True)

    def write_routes_ways(self, outpath):
        """Write routes members info in GeoJSON format

        :param str outpath: the path to the output GeoJSON file
        """
        self.cor.cch.write_relation_members_infomont(outpath)

    def write_all(self, outdir):
        """Write all info ready to be imported in infomont
        """
        self.write_routes(os.path.join(outdir, 'sent_perc.csv'))
        self.write_ways(os.path.join(outdir, 'trt_sent.geojson'))
        self.write_routes_ways(os.path.join(outdir, 'trt_perc.csv'))

    def write_all_geo(self, outdir, shapefile=True):
        """Write all info in geo format
        """
        self.write_routes_geo(os.path.join(outdir, 'sent_perc.geojson'))
        self.write_routes_ways_geo(os.path.join(outdir, 'trt_perc.geojson'))
        self.write_ways(os.path.join(outdir, 'trt_sent.geojson'))
        if shapefile:
            geojson2shp(os.path.join(outdir, 'sent_perc.geojson'),
                        os.path.join(outdir, 'sent_perc.shp'))
            geojson2shp(os.path.join(outdir, 'trt_perc.geojson'),
                        os.path.join(outdir, 'trt_perc.shp'))
            geojson2shp(os.path.join(outdir, 'trt_sent.geojson'),
                        os.path.join(outdir, 'trt_sent.shp'))
            os.remove(os.path.join(outdir, 'sent_perc.geojson'))
            os.remove(os.path.join(outdir, 'trt_perc.geojson'))
            os.remove(os.path.join(outdir, 'trt_sent.geojson'))

