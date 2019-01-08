#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 11:53:50 2019

@author: lucadelu
"""

import argparse
from caiosm.data_from_overpass import CaiOsmData
from caiosm.data_print import CaiOsmReport

def main():
    parser = argparse.ArgumentParser(description='Work with CAI OSM data')
    parser.add_argument('--place', type=str,
                        help='The name of an area, like municipalities and regions')
    parser.add_argument('--box', type=str,
                        help='The bounding box in latitude longitude WGS84 '
                        'coordinates')
    parser.add_argument('-p', dest='pdf',
                        help="name for a pdf file with all the CAI routes info")
    parser.add_argument('-w', dest='wiki', action='store_true',
                        help="print CAI routes in a wiki table format")
    parser.add_argument('-W', dest='wikiwrite',
                        help="name for a text file with CAI routes in "
                             "mediawiki table format")
    parser.add_argument('-c', dest='csv', action='store_true',
                        help="print CAI routes in a wiki table format" )
    parser.add_argument('-C', dest='csvwrite',
                        help="name for a CSV file with CAI routes" )
    parser.add_argument('-O', dest='osmwrite', help="name for a file in OSM "
                        "format with CAI routes")
    parser.add_argument('-j', dest='json', action='store_true',
                        help="print CAI routes in a JSON format" )
    parser.add_argument('-J', dest='jsonwrite',
                        help="name for a CSV file with CAI routes" )
    
    
    args = parser.parse_args()
    
    if not args['place'] and not ['box']:
        raise ValueError("one between --place or --box options is required")
    elif args['place'] and ['box']:
        raise ValueError("Please select only one between --place and --box")
    elif args['place']:
        cod = CaiOsmData(area=args['place'])
    elif args['box']:
        cod = CaiOsmData(area=args['box'])
    
    if args['pdf']:
        tags = cod.get_tags_json()
        cor = CaiOsmReport(tags)
        cor.write_book(args['p'], True)
    if args['wiki']:
        print(cod.wiki_table())
        print("")
    if args['wikiwrite']:
        cod.write(args['wikiwrite'],'wiki')
    if args['csv']:
        print(cod.get_data_csv())
        print("")
    if args['csvwrite']:
        cod.write(args['csvwrite'], 'csv')
    if args['osmwrite']:
        cod.write(args['osmwrite'], 'osm')
    if args['json']:
        print(cod.get_tags_json())
        print("")
    if args['jsonwrite']:
        cod.write(args['jsonwrite'], 'tags')