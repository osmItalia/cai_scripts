#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 16:28:42 2019

@author: lucadelu
"""

import os
import time
import json
from datetime import datetime
import configparser
from flask import Flask
from flask import render_template
from flask import jsonify
from flask import send_file
from slugify import slugify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from caiosm.data_from_overpass import CaiOsmRoute
from caiosm.data_from_overpass import CaiOsmSourceRef
from caiosm.data_from_overpass import CaiOsmRouteSourceRef
from caiosm.data_print import CaiOsmReport
from caiosm.functions import get_regions_from_geojson

DIRFILE = os.path.dirname(os.path.realpath(__file__))
MEDIADIR = os.path.join(DIRFILE, 'media')

config = configparser.ConfigParser()
config.read(os.path.join(DIRFILE, 'cai_scripts.ini'))

def get_data():
    print("Get data {}".format(datetime.now()))
    inpath = os.path.join(DIRFILE, 'static')
    regions = get_regions_from_geojson(os.path.join(inpath, 'data',
                                                    'italy.geojson'))
    for reg in regions:
        regslug = slugify(reg)
        cod = CaiOsmRoute(area=reg)
        cod.get_cairoutehandler()
        gjsfile = os.path.join(inpath, 'regions', "{}.geojson".format(regslug))
        cod.write(gjsfile, 'geojson')
        jsobj = json.load(gjsfile)
        cor = CaiOsmReport(jsobj, geo=True, output_dir=MEDIADIR)
        cor.write_book(regslug, pdf=True)
        cod.write(os.path.join(inpath, 'regions', "{}.json".format(regslug)),
                               'tags')
        time.sleep(config['MISC']['overpasstime'])
    return True

def get_sezioni():
    print("Get sezioni {}".format(datetime.now()))
    cosr = CaiOsmSourceRef()
    cosr.write(os.path.join(DIRFILE, 'static', 'data', 'cai_osm.csv'),
               'names')
    return True

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=config['DATABASE']['SQLALCHEMY_DATABASE_URI'],
    )
    cosr = CaiOsmSourceRef()
    cosr.get_list_codes()

    if test_config is not None:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    if not os.path.exists(MEDIADIR):
        os.mkdir(MEDIADIR)

    sched = BackgroundScheduler(daemon=True)
    sched.add_job(get_sezioni, CronTrigger.from_crontab('0 0 * * *'))
    sched.add_job(get_data, CronTrigger.from_crontab('30 0 * * *'))
    sched.start()

    # a simple page that says hello
    @app.route('/')
    def home():
        """Return the home page"""
        return render_template('home.html')

    @app.route('/regione/<region>')
    def regione(region):
        """Return the info for a single region"""
        codes = cosr.get_codes_region(region)
        existing = cosr.get_list_codes()
        print(codes, existing)
        return render_template('region.html', name=region, codes=codes,
                               exists=existing)

    @app.route('/sezionejson/<group>')
    def sezionetagsjson(group):
        """Return the info for a single sezione"""
        corsr = CaiOsmRouteSourceRef(group)
        return jsonify(corsr.get_tags_json())

    @app.route('/sezionegeojson/<group>')
    def sezionegeojson(group):
        """Return the info for a single sezione"""
        corsr = CaiOsmRouteSourceRef(group)
        corsr.get_cairoutehandler()
        corsr.cch.create_routes_geojson()
        return jsonify(corsr.get_geojson())

    @app.route('/sezioneroute/<group>')
    def sezioneroute(group):
        """Return the info for a single sezione"""
        for li in cosr.cai_codes:
            if group == li[0]:
                name = li[1]
                break
        return render_template('sezione.html', name=name, sez=group)

    @app.route('/about')
    def about():
        """Return the about page"""
        return render_template('about.html')

    @app.route('/regionepdf/<region>')
    def regionepdf(region):
        """Return PDF for a region"""
        fi = open(os.path.join(MEDIADIR, '{}.pdf'.format(region)), 'rb')
        return send_file(fi, attachment_filename='{}.pdf'.format(region),
                         mimetype='application/pdf')

    @app.route('/sezionepdf/<group>')
    def sezionepdf(group):
        corsr = CaiOsmRouteSourceRef(group)
        corsr.get_cairoutehandler()
        corsr.cch.create_routes_geojson()
        jsobj = corsr.get_geojson()
        cor = CaiOsmReport(jsobj, geo=True, output_dir=MEDIADIR)
        cor.write_book(group, pdf=True)
        fi = open(os.path.join(MEDIADIR, '{}.pdf'.format(group)), 'rb')
        return send_file(fi, attachment_filename='{}.pdf'.format(group),
                         mimetype='application/pdf')

    return app
