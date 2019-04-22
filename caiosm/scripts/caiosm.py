#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 11:53:50 2019

@author: lucadelu
"""
import os
import argparse
from caiosm.data_from_overpass import CaiOsmData
from caiosm.data_print import CaiOsmReport
from caiosm.infomont import CaiOsmInfomont

def main():
    parser = argparse.ArgumentParser(description='Work with CAI OSM data')
    subparsers = parser.add_subparsers(help='caiosm sub commands help')
    parser_get = subparsers.add_parser('data', help='getdata help')
    parser.add_argument('--place', type=str, help='The name of an area, '
                            'like municipalities and regions')
    parser.add_argument('--box', type=str, help='The bounding box in '
                            'latitude longitude WGS84 coordinates')
    parser_get.add_argument('-w', dest='wiki', action='store_true',
                            help="print CAI routes in a mediawiki table "
                            "format")
    parser_get.add_argument('-W', dest='wikiwrite',
                            help="name for a text file with CAI routes in "
                             "mediawiki table format")
    parser_get.add_argument('-c', dest='csv', action='store_true',
                            help="print CAI routes in a wiki table format" )
    parser_get.add_argument('-C', dest='csvwrite',
                            help="name for a CSV file with CAI routes" )
    parser_get.add_argument('-O', dest='osmwrite', help="name for a file in "
                            "OSM format with CAI routes")
    parser_get.add_argument('-j', dest='json', action='store_true',
                            help="print CAI routes in a JSON format" )
    parser_get.add_argument('-J', dest='jsonwrite',
                            help="name for a JSON file with CAI routes" )
    parser_get.add_argument('-g', dest='geojson', action='store_true',
                            help="print CAI routes in a GeoJSON format" )
    parser_get.add_argument('-G', dest='geojsonwrite',
                            help="name for a GeoJSON file with CAI routes" )
    parser_get.set_defaults(func='data')
    parser_report = subparsers.add_parser('report', help='report help')
    parser_report.add_argument('-g', dest='geo', action="store_true",
                               help="print the report with a map for each "
                               "route")
    parser_report.add_argument('-o', dest='out', required=True,
                               help="the name of output file without path and"
                                    "extension")
    parser_report.set_defaults(func='report')
    parser_infomont = subparsers.add_parser('infomont', help='infomont help')
    parser_infomont.set_defaults(func='infomont')
    parser_infomont.add_argument('-o', dest='out', required=True,
                                 help="the path to the output directory "
                                 "containing the three output file")

    args = parser.parse_args()

    if not args.place and not args.box:
        raise ValueError("one between --place or --box options is required")
    elif args.place and args.box:
        raise ValueError("Please select only one between --place and --box")
    elif args.place:
        cod = CaiOsmData(area=args.place)
    elif args.box:
        cod = CaiOsmData(bbox=args.box)
    
    if args.func == 'report':
        tags = cod.get_tags_json()
        cor = CaiOsmReport(tags, geo=args.geo)
        cor.write_book(args.out, True)
    elif args.func == 'data':
        if args.wiki:
            print(cod.wiki_table())
            print("")
        if args.wikiwrite:
            cod.write(args.wikiwrite,'wikitable')
        if args.csv:
            print(cod.get_data_csv())
            print("")
        if args.csvwrite:
            cod.write(args.csvwrite, 'csv')
        if args.osmwrite:
            cod.write(args.osmwrite, 'osm')
        if args.json:
            print(cod.get_tags_json())
            print("")
        if args.jsonwrite:
            cod.write(args.jsonwrite, 'json')
        if args.geojson:
            handler = cod.get_cairoutehandler()
            handler.create_routes_geojson()
            print(handler.gjons)
            print("")
        if args.geojsonwrite:
            cod.write_geojson(args.geojsonwrite)
    elif args.func == 'infomont':
        osm = cod.get_data_osm()
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.osm') as fi:
            fi.write(osm)
        #TODO fix segmentation fault
        coi = CaiOsmInfomont(fi.name)
        coi.write_all(args.out)
        os.remove(fi.name)
    else:
        parser.print_help()
