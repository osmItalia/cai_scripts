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
from flask import request
from slugify import slugify
from flask_apscheduler import APScheduler
from caiosm.data_from_overpass import CaiOsmRoute
from caiosm.data_from_overpass import CaiOsmSourceRef
from caiosm.data_from_overpass import CaiOsmRouteSourceRef
from caiosm.data_diff import ManageChanges
from caiosm.data_print import CaiOsmReport
from caiosm.functions import get_regions_from_geojson
from app.model import db
from app.model import select_users
from app.model import insert_user
from app.model import delete_user
from app.model import delete_region_user

DIRFILE = os.path.dirname(os.path.realpath(__file__))
MEDIADIR = os.path.join(DIRFILE, 'media')

config = configparser.ConfigParser()
config.read(os.path.join(DIRFILE, 'cai_scripts.ini'))

sched = APScheduler()

class Config(object):
    JOBS = [
        {
            'id': 'get_data',
            'func': 'app:get_data',
            'trigger': 'cron',
            'minute': 10,
            'hour': 00
        },
        {
            'id': 'get_sezioni',
            'func': 'app:get_sezioni',
            'trigger': 'cron',
            'minute': 01,
            'hour': 00
        }
    ]

    SCHEDULER_API_ENABLED = True
    SQLALCHEMY_DATABASE_URI=config['DATABASE']['SQLALCHEMY_DATABASE_URI'],
    SQLALCHEMY_TRACK_MODIFICATIONS=config['DATABASE']['SQLALCHEMY_TRACK_MODIFICATIONS'],
    SCHEDULER_API_ENABLED = True

class GeneralError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

def update(reg, inpath):
    regslug = slugify(reg)
    gjsfile = os.path.join(inpath, 'regions', "{}.geojson".format(regslug))
    cod = CaiOsmRoute(area=reg)
    cod.get_cairoutehandler()
    cod.write(gjsfile, 'geojson')
    jsobj = json.load(open(gjsfile))
    starttime = int(time.time())
    cor = CaiOsmReport(jsobj, geo=True, output_dir=MEDIADIR)
    cor.write_book(regslug, pdf=True)
    cod.write(os.path.join(inpath, 'regions',
                           "{}.json".format(regslug)),
              'tags')
    endtime = int(time.time())
    difftime = endtime-starttime
    if difftime > 420:
        return True
    else:
        return False

def get_data():
    print("Get data {}".format(datetime.now()))
    inpath = os.path.join(DIRFILE, 'static')
    regions = get_regions_from_geojson(os.path.join(inpath, 'data',
                                                    'italy.geojson'))


    for reg in regions:
        regslug = slugify(reg)
        gjsfile = os.path.join(inpath, 'regions', "{}.geojson".format(regslug))
        mc = ManageChanges(area=reg, path=DIRFILE)
        if len(mc.changes) > 0:
            print("{} has changes".format(reg))
            with db.app.app_context():
                mails = select_users(regslug)
            if mails:
                mc.mail(bccs=mails)
            mc.telegram(token=config['TELEGRAM']['token'],
                        chatid=config['TELEGRAM']['chatid'])
            time.sleep(int(config['MISC']['overpasstime'])/2)
            skiptime = update(reg, inpath)
        elif not os.path.exists(gjsfile):
            skiptime = update(reg, inpath)
        else:
            print("{} has NO changes".format(reg))
            if not os.path.exists(os.path.join(MEDIADIR,
                                               '{}.pdf'.format(regslug))):
                jsobj = json.load(open(gjsfile))
                cor = CaiOsmReport(jsobj, geo=True, output_dir=MEDIADIR)
                cor.write_book(regslug, pdf=True)
            skiptime = False
        if not skiptime:
            time.sleep(int(config['MISC']['overpasstime']))
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
    app.config.from_object(Config())

    db.app = app
    db.init_app(app)

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

    sched.init_app(app)
    sched.start()

    @app.errorhandler(GeneralError)
    def handle_invalid_usage(error):
        response = error
        response.status_code = error.status_code
        return response


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

    @app.route('/insertmail', methods=['POST'])
    def insertmail():
        data = request.json
        if not data:
            data = request.form
            if not data:
                raise GeneralError('Nessun dato')
        err = ''
        if 'email' not in data.keys():
            err += "Manca l'indirizzo email. "
        if 'reg' not in data.keys():
            err += "Manca la regione d'interesse."
        if err:
            raise GeneralError(err)
        out = insert_user(data['email'], data['reg'])
        return jsonify({'response': out})

    @app.route('/deleteregionmail', methods=['POST'])
    def deleteregionmail():
        data = request.json
        if not data:
            data = request.form
            if not data:
                raise GeneralError('Nessun dato')
        err = ''
        if 'email' not in data.keys():
            err += "Manca l'indirizzo email. "
        if 'reg' not in data.keys():
            err += "Manca la regione d'interesse."
        if 'deleteuser' not in data.keys():
            delete = False
        else:
            if data['deleteuser'] == 'true':
                delete = True
            else:
                delete = False
        if err:
            raise GeneralError(err)
        out = delete_region_user(data['email'], data['reg'], delete)
        return jsonify({'response': out})

    @app.route('/deletemail', methods=['POST'])
    def deletemail():
        data = request.json
        if not data:
            data = request.form
            if not data:
                raise GeneralError('Nessun dato')
        if 'email' not in data.keys():
            raise GeneralError("Manca l'indirizzo email")
        out = delete_user(data['email'])
        return jsonify({'response': out})

    return app
