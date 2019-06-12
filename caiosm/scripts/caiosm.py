#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 11:53:50 2019

@author: lucadelu
"""
import os
import argparse
from caiosm.data_from_overpass import CaiOsmRoute
from caiosm.data_from_overpass import CaiOsmOffice
from caiosm.data_print import CaiOsmReport
from caiosm.infomont import CaiOsmInfomont

def main():
    parser = argparse.ArgumentParser(description='Work with CAI OSM data')
    subparsers = parser.add_subparsers(help='caiosm sub commands help')
    parser_get = subparsers.add_parser('route', help='Get CAI route data'
                                       ' in several formats')
    parser.add_argument('--place', type=str, help='The name of an area, '
                        'like municipalities and regions')
    parser.add_argument('--box', type=str, help='The bounding box in '
                        'latitude longitude WGS84 coordinates')
    parser.add_argument('--debug', dest='debug', action='store_true',
                        help="set debug")
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
    parser_get.set_defaults(func='route')
    parser_report = subparsers.add_parser('report', help='Get reports about '
                                                         'CAI route in OSM')
    parser_report.add_argument('-g', dest='geo', action="store_true",
                               help="print the report with a map for each "
                               "route")
    parser_report.add_argument('-o', dest='out', required=True,
                               help="the name of output file without path and"
                                    " extension")
    parser_report.set_defaults(func='report')
    parser_infomont = subparsers.add_parser('infomont', help='Get OSM CAI data'
                                            ' in infomont format')
    parser_infomont.set_defaults(func='infomont')
    parser_infomont.add_argument('-o', dest='out', required=True,
                                 help="the path to the output directory "
                                 "containing the three output files")
    parser_office = subparsers.add_parser('office', help='Get CAI office data'
                                          ' in several formats')
    parser_office.set_defaults(func='office')
    parser_office.add_argument('-w', dest='wiki', action='store_true',
                               help="print CAI offices in a mediawiki table "
                                    "format")
    parser_office.add_argument('-W', dest='wikiwrite',
                               help="name for a text file with CAI offices in "
                                    "mediawiki table format")
    parser_office.add_argument('-c', dest='csv', action='store_true',
                               help="print CAI offices in a wiki table format")
    parser_office.add_argument('-C', dest='csvwrite',
                               help="name for a CSV file with CAI offices")
    parser_office.add_argument('-O', dest='osmwrite', help="name for a file "
                               "in OSM format with CAI offices")
    parser_office.add_argument('-j', dest='json', action='store_true',
                               help="print CAI offices in a JSON format")
    parser_office.add_argument('-J', dest='jsonwrite',
                               help="name for a JSON file with CAI offices")
    parser_office.add_argument('-g', dest='geojson', action='store_true',
                               help="print CAI offices in a GeoJSON format")
    parser_office.add_argument('-G', dest='geojsonwrite',
                               help="name for a GeoJSON file with CAI offices")
    args = parser.parse_args()

    if not args.place and not args.box:
        raise ValueError("one between --place or --box options is required")
    elif args.place and args.box:
        raise ValueError("Please select only one between --place and --box")
    elif args.place:
        inarea = args.place
        inbox = None
    elif args.box:
        inarea = None
        inbox = args.box

    #initialize the right class to use
    if args.func in ['report', 'route']:
        cod = CaiOsmRoute(bbox=inbox, area=inarea, debug=args.debug)
    elif args.func == 'office':
        cod = CaiOsmOffice(bbox=inbox, area=inarea, debug=args.debug)

    if args.func == 'report':
        if args.geo:
            cod.get_cairoutehandler()
            tags = cod.get_geojson()
        else:
            tags = cod.get_tags_json()
        cor = CaiOsmReport(tags, geo=args.geo, debug=args.debug)
        cor.write_book(args.out, True)
    elif args.func in ['route', 'office']:
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
            cod.write(args.jsonwrite, 'tags')
        if args.geojson:
            if args.func == 'route':
                cod.get_cairoutehandler()
            print(cod.get_geojson())
            print("")
        if args.geojsonwrite:
            cod.write(args.geojsonwrite, 'geojson')
    elif args.func == 'infomont':
        if not args.out:
            raise ValueError("Please set -o options")
        elif not os.path.isdir(args.out):
            print("The directory {} does not exist, creating it"
                  "...".format(args.out))
            os.makedirs(args.out)
        elif not os.access(args.out, os.W_OK):
            raise ValueError("The directory {} exists, but it is not "
                             "writable".format(args.out))
        coi = CaiOsmInfomont(bbox=inbox, area=inarea, debug=args.debug)
        coi.write_all_geo(args.out)
    else:
        parser.print_help()
