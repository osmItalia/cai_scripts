#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 11:53:50 2019

@author: lucadelu
"""
import os
import time
import argparse
import shutil
import faulthandler
import configparser
from caiosm.data_from_overpass import CaiOsmRoute
from caiosm.data_from_overpass import CaiOsmOffice
from caiosm.data_from_overpass import CaiOsmSourceRef
from caiosm.data_print import CaiOsmReport
from caiosm.infomont import CaiOsmInfomont
from caiosm.functions import REGIONI
from caiosm.functions import make_safe_filename
from caiosm.data_diff import ManageChanges

def get_updates(config):

    for reg in REGIONI:
        mc = ManageChanges(area=reg)
        if len(mc.changes) > 0:
            print("**{} has changes**".format(reg))
            # TODO find a way to store mail for region
            #with db.app.app_context():
            #    mails = select_users(regslug)
            mails = None

            if mails:
                mc.mail(bccs=mails)
            mc.telegram(
                token=config["TELEGRAM"]["token"], chatid=config["TELEGRAM"]["chatid"]
            )
        else:
            print("--{} has no changes--".format(reg))
        time.sleep(int(config["MISC"]["overpasstime"]))
    return True


def create_infomont(inarea, inbox, args, prefix=None, out=None):
    if not out:
        out = args.out
    coi = CaiOsmInfomont(bbox=inbox, area=inarea, debug=args.debug, prefix=prefix)
    coi.write_all_geo(out)
    if args.zip:
        shutil.make_archive(os.path.split(out)[-1], "zip", out)


def main():
    faulthandler.enable()
    parser = argparse.ArgumentParser(description="Work with CAI OSM data")
    parser.add_argument(
        "--place",
        type=str,
        help="The name of an area, " "like municipalities and regions",
    )
    parser.add_argument(
        "--box",
        type=str,
        help="The bounding box in " "latitude longitude WGS84 coordinates",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="The config file, required by updates subcommand",
        dest="config",
    )
    parser.add_argument("--debug", dest="debug", action="store_true", help="set debug")
    subparsers = parser.add_subparsers(help="caiosm sub commands help")
    parser_get = subparsers.add_parser(
        "route", help="Get CAI route data" " in several formats"
    )
    parser_get.add_argument(
        "-w",
        dest="wiki",
        action="store_true",
        help="print CAI routes in a mediawiki table " "format",
    )
    parser_get.add_argument(
        "-W",
        dest="wikiwrite",
        help="name for a text file with CAI routes in " "mediawiki table format",
    )
    parser_get.add_argument(
        "-c",
        dest="csv",
        action="store_true",
        help="print CAI routes in a wiki table format",
    )
    parser_get.add_argument(
        "-C", dest="csvwrite", help="name for a CSV file with CAI routes"
    )
    parser_get.add_argument(
        "-O", dest="osmwrite", help="name for a file in " "OSM format with CAI routes"
    )
    parser_get.add_argument(
        "-j",
        dest="json",
        action="store_true",
        help="print CAI routes tags in a JSON format",
    )
    parser_get.add_argument(
        "-J", dest="jsonwrite", help="name for a JSON file with CAI routes tags"
    )
    parser_get.add_argument(
        "-g",
        dest="geojson",
        action="store_true",
        help="print CAI routes in a GeoJSON format",
    )
    parser_get.add_argument(
        "-G", dest="geojsonwrite", help="name for a GeoJSON file with CAI routes"
    )
    parser_get.set_defaults(func="route")
    parser_report = subparsers.add_parser(
        "report", help="Get reports about " "CAI route in OSM"
    )
    parser_report.add_argument(
        "-g",
        dest="geo",
        action="store_true",
        help="print the report with a map for each " "route",
    )
    parser_report.add_argument(
        "-o",
        dest="out",
        required=True,
        help="the name of output file without path and" " extension",
    )
    parser_report.set_defaults(func="report")
    parser_infomont = subparsers.add_parser(
        "infomont", help="Get OSM CAI data" " in infomont format"
    )
    parser_infomont.set_defaults(func="infomont")
    parser_infomont.add_argument(
        "-o",
        dest="out",
        required=True,
        help="the path to the output directory " "containing the three output files",
    )
    parser_infomont.add_argument(
        "-r", dest="regs", action="store_true", help="create all Italian regions"
    )
    parser_infomont.add_argument("-p", dest="prefix", help="added prefix to the id")
    parser_infomont.add_argument(
        "-z",
        dest="zip",
        action="store_true",
        help="create a zip file of the directory " "containing the three output files",
    )
    parser_office = subparsers.add_parser(
        "office", help="Get CAI office data" " in several formats"
    )
    parser_office.set_defaults(func="office")
    parser_office.add_argument(
        "-w",
        dest="wiki",
        action="store_true",
        help="print CAI offices in a mediawiki table " "format",
    )
    parser_office.add_argument(
        "-W",
        dest="wikiwrite",
        help="name for a text file with CAI offices in " "mediawiki table format",
    )
    parser_office.add_argument(
        "-c",
        dest="csv",
        action="store_true",
        help="print CAI offices in a wiki table format",
    )
    parser_office.add_argument(
        "-C", dest="csvwrite", help="name for a CSV file with CAI offices"
    )
    parser_office.add_argument(
        "-O", dest="osmwrite", help="name for a file " "in OSM format with CAI offices"
    )
    parser_office.add_argument(
        "-j",
        dest="json",
        action="store_true",
        help="print CAI offices in a JSON format",
    )
    parser_office.add_argument(
        "-J", dest="jsonwrite", help="name for a JSON file with CAI offices"
    )
    parser_office.add_argument(
        "-g",
        dest="geojson",
        action="store_true",
        help="print CAI offices in a GeoJSON format",
    )
    parser_office.add_argument(
        "-G", dest="geojsonwrite", help="name for a GeoJSON file with CAI offices"
    )
    parser_app = subparsers.add_parser(
        "updates", help="Get daily CAI routes updates for each italian region"
    )
    parser_app.set_defaults(func="updates")
    args = parser.parse_args()

    if not args.place and not args.box:
        if args.func == "infomont" and args.regs:
            pass
        elif args.func == "updates":
            pass
        else:
            raise ValueError("one between --place or --box options is required")
    elif args.place and args.box:
        raise ValueError("Please select only one between --place and --box")
    elif args.place:
        inarea = args.place
        inbox = None
    elif args.box:
        inarea = None
        inbox = args.box

    config = None
    if args.config:
        config = configparser.ConfigParser()
        config.read(args.config)

    # initialize the right class to use
    if args.func in ["report", "route"]:
        cod = CaiOsmRoute(bbox=inbox, area=inarea, debug=args.debug)
    elif args.func == "office":
        cod = CaiOsmOffice(bbox=inbox, area=inarea, debug=args.debug)

    if args.func == "report":
        if args.geo:
            cod.get_cairoutehandler()
            tags = cod.get_geojson()
        else:
            tags = cod.get_tags_json()
        cor = CaiOsmReport(tags, geo=args.geo, debug=args.debug)
        cor.write_book(args.out, True)
    elif args.func in ["route", "office"]:
        if args.wiki:
            print(cod.wiki_table())
            print("")
        if args.wikiwrite:
            cod.write(args.wikiwrite, "wikitable")
        if args.csv:
            print(cod.get_data_csv())
            print("")
        if args.csvwrite:
            cod.write(args.csvwrite, "csv")
        if args.osmwrite:
            cod.write(args.osmwrite, "osm")
        if args.json:
            if args.func == "route":
                print(cod.get_tags_json())
            else:
                print(cod.get_data_json())
            print("")
        if args.jsonwrite:
            if args.func == "route":
                cod.write(args.jsonwrite, "tags")
            else:
                cod.write(args.jsonwrite, "json")
        if args.geojson:
            if args.func == "route":
                cod.get_cairoutehandler()
            print(cod.get_geojson())
            print("")
        if args.geojsonwrite:
            cod.write(args.geojsonwrite, "geojson")
    elif args.func == "infomont":
        if not args.out:
            raise ValueError("Please set -o options")
        elif not os.path.isdir(args.out):
            print("The directory {} does not exist, creating it" "...".format(args.out))
            os.makedirs(args.out)
        elif not os.access(args.out, os.W_OK):
            raise ValueError(
                "The directory {} exists, but it is not " "writable".format(args.out)
            )
        if args.regs:
            for reg, regid in REGIONI.items():
                if args.debug:
                    print("-------- Processing : {} --------".format(reg))
                outpath = os.path.join(args.out, make_safe_filename(reg))
                if not os.path.isdir(outpath):
                    os.makedirs(outpath)
                try:
                    print(
                        "WARNING: process take long time, please run it in"
                        " a screen session or cronjob"
                    )
                    create_infomont(reg, None, args, regid, outpath)
                except:
                    raise ValueError(
                        "Error creating infomont data for region" " {}".format(reg)
                    )
        elif inbox or inarea:
            prefix = None
            if args.prefix:
                prefix = args.prefix
            try:
                print(
                    "WARNING: process take long time, please run it in"
                    " a screen session or cronjob"
                )
                create_infomont(inarea, inbox, args, prefix)
            except:
                raise ValueError("Error creating infomont data")
    elif args.func == "updates":
        if config is None:
            raise ValueError("--config option is required")
        print(
            "WARNING: process take long time, please run it in"
            " a screen session or cronjob"
        )
        get_updates(config)
    else:
        parser.print_help()
