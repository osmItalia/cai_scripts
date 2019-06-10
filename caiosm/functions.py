#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 23:45:52 2019

@author: lucadelu
"""
import os
import csv
import json
from subprocess import Popen, PIPE
import configparser
import itertools
import smtplib
from copy import deepcopy
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from shapely.geometry import mapping, shape, MultiPoint, Point
from shapely.ops import split
import geojson
import fiona
import geopandas as gpd
import matplotlib.pyplot as plt
from PIL import Image, ImageChops

# functions
def invert_bbox(bbox):
    """Convert the bounding box from XMIN,YMIN,XMAX,YMAX to YMIN,XMIN,YMAX,XMAX

    :param str box: the string of the bounding box comma separated
    """
    l = bbox.split(',')
    return "{ymi},{xmi},{yma},{xma}".format(ymi=l[1], xmi=l[0], yma=l[3],
                                            xma=l[2])

def check_network(net):
    """Check if network is set

    :param str net: the network code
    """
    if net in ['lwn', 'rwn', 'nwn', 'iwn']:
        return '["network"="{}"]'.format(net)
    return ''

def WriteDictToCSV(csv_file, csv_columns, dict_data):
    """Function to write a CSV file from a dictionary

    :param str csv_file: the path to the output CSV file
    :param list csv_columns: the name of the column and dictionary keys
    :param dict dict_data: the dictionary with the data
    """
    try:
        with open(csv_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns,
                                    extrasaction='ignore')
            writer.writeheader()
            for k, data in dict_data.items():
                writer.writerow(data['tags'])
    except IOError as err:
        errno, strerror = err.args
        print("I/O error({0}): {1}".format(errno, strerror))
    return

def _run_cmd(cmd):
    """Run a command and check if the output it is fine

    :param str cmd:
    """
    proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    retcode = proc.returncode
    if retcode > 1:
        raise ValueError('Error {} executing command: {}'.format(retcode,
                                                                 cmd))
    return True

def clean_tags(tags):
    """Clean tags removed strange "strange" characters like :

    :param dict tags: the tags dictionary
    """
    newtags = {}
    for k in tags.keys():
        if ':' in k:
            newtags[k.replace(':', '')] = tags[k]
        else:
            newtags[k] = tags[k]
    return newtags

def geom_geojson(geo):
    """Return a shapely geometry from a geojson geometry

    :param dict geo:
    """
    geoj = json.dumps(geo)
    gjson = geojson.loads(geoj)
    return shape(gjson)

def image_ratio(path):
    """Return the image ratio to scale it correctly

    :param str path: the path of an image
    """
    image = Image.open(path)
    x, y = image.size
    return x / y

def add_basemap(axi, zoom,
                url='http://tile.stamen.com/terrain/tileZ/tileX/tileY.png'):
    """Added a basemap to a subplot

    :param obj axi: subplot axes
    :param int zoom: the number of zoom to use
    :param str url: the url
    """
    import contextily as ctx
    try:
        xmin, xmax, ymin, ymax = axi.axis()
        basemap, extent = ctx.bounds2img(xmin, ymin, xmax, ymax, zoom=zoom,
                                         url=url)
        axi.imshow(basemap, extent=extent, interpolation='bilinear')
        # restore original x/y limits
        axi.axis((xmin, xmax, ymin, ymax))
        return True
    except Exception:
        return False

def autocrop(img, bgcolor):
    """Function to crop the images

    :param obj img: the image object
    :parak bgcolor: the color to crop
    """
    if img.mode != "RGB":
        img = img.convert("RGB")
    bg = Image.new("RGB", img.size, bgcolor)
    diff = ImageChops.difference(img, bg)
    bbox = diff.getbbox()
    if bbox:
        return img.crop(bbox)
    return None # no contents

def create_map(geom, out):
    """Create a map using geopandas

    :param obj geom: shapely geometry object
    :param str out: path out the output img file
    """
    gs = gpd.GeoSeries(geom)
    gs.crs = {'init': 'epsg:4326'}
    gs = gs.to_crs(epsg=3857)
    ax = gs.plot(figsize=(10, 10), alpha=0.5, color='r')
    ax.axes.get_yaxis().set_visible(False)
    ax.axes.get_xaxis().set_visible(False)
    zoom = 15
    while not add_basemap(ax, zoom=zoom):
        zoom -= 1
    fig = ax.get_figure()
    tmpto = out.replace('.png', '_tmp.png')
    fig.savefig(tmpto)
    plt.close()
    image = Image.open(tmpto)
    newimg = autocrop(image, 'white')
    if newimg:
        newimg.save(out)
        os.remove(tmpto)
        return True

def get_regions_from_geojson(inpath, col='Name'):
    infile = gpd.read_file(inpath)
    return list(infile[col])

def send_mail(sub, mess, to, attach=None):
    """"""
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.expanduser('~'), '.cai_scripts.conf'))
    email = config['EMAIL']['email']
    password = config['EMAIL']['password']

    msg = MIMEMultipart()
    msg['From'] = email
    msg['To'] = to
    msg['Subject'] = sub

    msg.attach(MIMEText(mess, 'plain'))

    if attach:
        # Setup the attachment
        filename = os.path.basename(file_location)
        attachment = open(file_location, "rb")
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % filename)

        # Attach the attachment to the MIMEMultipart object
        msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email, password)
    text = msg.as_string()
    try:
        server.sendmail(email, to, text)
        server.quit()
    except Exception as e:
        print(e)
        print(to)

def get_points(lines):
    inters = []
    for l1,l2 in itertools.combinations(lines, 2):
        line1 = shape(l1['geometry'])
        line2 = shape(l2['geometry'])
        if  line1.intersects(line2):
            inter = line1.intersection(line2)
            if "Point" == inter.type:
                inters.append(inter)
            elif "MultiPoint" == inter.type:
                inters.extend([pt for pt in inter])
            elif "MultiLineString" == inter.type:
                multiLine = [line for line in inter]
                first_coords = multiLine[0].coords[0]
                last_coords = multiLine[len(multiLine)-1].coords[1]
                inters.append(Point(first_coords[0], first_coords[1]))
                inters.append(Point(last_coords[0], last_coords[1]))
            elif "GeometryCollection" == inter.type:
                for geom in inter:
                    if "Point" == geom.type:
                        inters.append(geom)
                    elif "MultiPoint" == geom.type:
                        inters.extend([pt for pt in geom])
                    elif "MultiLineString" == geom.type:
                        multiLine = [line for line in geom]
                        first_coords = multiLine[0].coords[0]
                        last_coords = multiLine[len(multiLine)-1].coords[1]
                        inters.append(Point(first_coords[0], first_coords[1]))
                        inters.append(Point(last_coords[0], last_coords[1]))
    return MultiPoint(inters)

def split_at_intersection(lines):
    mp = get_points(lines)
    x = 0
    output = []
    for line in lines:
        splitlines = split(shape(line['geometry']), mp)
        for sl in splitlines:
            feats = deepcopy(line['properties'])
            feats['IDTrat'] = x
            output.append(geojson.Feature(geometry=mapping(sl), id=x,
                                          properties=feats))
            x += 1
    return output

def geojson2shp(f_in, f_out):
    """Function to convert geojson to ESRI shapfile"""
    with fiona.open(f_in) as source:
        with fiona.open(f_out, 'w', driver='ESRI shapefile',
                        crs = source.crs, schema=source.schema) as out:
            for feat in source:
                out.write(feat)