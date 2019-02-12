#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan  5 00:14:45 2019

@author: lucadelu
"""
import os
from subprocess import Popen, PIPE
import shutil
import json
from shapely.geometry import shape
import geojson
import geopandas
import matplotlib.pyplot as plt
from PIL import Image, ImageChops
import jinja2


# full path of the file, used to get directory for latex templates
DIRFILE = os.path.dirname(os.path.realpath(__file__))

OSMTILES = {'terrain': 'http://tile.stamen.com/terrain/tileZ/tileX/tileY.png',
            'osm': 'https://a.tile.openstreetmap.org/tileZ/tileX/tileY.png',
            'cycle': 'http://tile.thunderforest.com/cycle/tileZ/tileX/tileY.png',
            'wiki': 'https://maps.wikimedia.org/osm-intl/tileZ/tileX/tileY.png'}

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
    gs = geopandas.GeoSeries(geom)
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

class CaiOsmReport:

    def __init__(self, myjson, geo=False, output_dir='.'):
        """Class to print relation info into a report

        :param obj myjson: json containg tags and id of a list of relations, it
                           is possible to get it from
                           data_from_overpass - CaiOsmData - get_tags_json
        :param bool geo: set if the input json is a geojson
        :param str output_dir: the directory where save the output file
        """
        self.geo = geo
        if self.geo:
            self.json = myjson['features']
        else:
            self.json = myjson
        self.latex_jinja_env = jinja2.Environment(
            block_start_string='\BLOCK{',
            block_end_string='}',
            variable_start_string='\VAR{',
            variable_end_string='}',
            comment_start_string='\#{',
            comment_end_string='}',
            line_statement_prefix='%%',
            line_comment_prefix='%#',
            trim_blocks=True,
            autoescape=False,
            loader=jinja2.FileSystemLoader(os.path.join(DIRFILE,
                                                        'latex_template'))
        )
        # check if output directory exists and it is writable
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
            self.output_dir = os.path.abspath(output_dir)
        elif os.access(output_dir, os.W_OK):
            self.output_dir = os.path.abspath(output_dir)
        else:
            try:
                os.mkdir(output_dir)
                self.output_dir = os.path.abspath(output_dir)
            except:
                raise Exception("Folder to store output files does not "
                                "exist or is not writeable")

    def _create_pdf(self, infile):
        """Private function to convert tex file to pdf

        :param str infile: path to input tex file
        """
        # check if pdflatex is installed
        if shutil.which('pdflatex'):
            cmd = 'pdflatex -interaction=nonstopmode -output-directory={di}' \
                  ' {inf}'.format(di=self.output_dir, inf=infile)
        else:
            raise Exception("pdflatex not found. Please install it to get PDF"
                            " files")
        proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        retcode = proc.returncode
        if retcode != 0:
            print(err)
            raise ValueError('Error {} executing command: {}'.format(retcode,
                                                                     cmd))
        return 0

    def print_single(self, elem, out_type='REF', pdf=False,
                     intemp='single.tex'):
        """Print or save the tex file for an element

        :param obj elem: element object
        :param str out_type: parameter to choose the method and the name of the
                             output file
        :param bool pdf: convert the tex files to pdf
        :param str intemp: the name of the template to use
        """
        template = self.latex_jinja_env.get_template(intemp)
        ratio = None
        if self.geo:
            ele = elem['properties']
            geom = True
        else:
            ele = elem
            geom = False
        if 'ref' not in ele.keys():
            print("Relazione con id {} non ha il campo ref".format(ele['id']))
            return False
        if out_type == 'REF':
            idd = ele['ref']
        elif out_type == 'NAME':
            idd = ele['name'].replace(' ', '_').replace("'", "_")
        elif out_type == 'ID':
            idd = ele['id']
        else:
            raise ValueError("output value options are: REF and NAME")
        outname = 'sentiero_{}.tex'.format(idd)
        outfile = open(os.path.join(self.output_dir, outname), 'w')
        if geom:
            pngname = os.path.join(self.output_dir,
                                   'sentiero_{}.png'.format(idd))
            create_map(geom_geojson(elem['geometry']), pngname)
            imgratio = image_ratio(pngname)
            if imgratio > 0.8:
                ratio = 0.9
            elif imgratio > 0.5 and imgratio <= 0.8:
                ratio = 0.6
            elif imgratio > 0.2 and imgratio <= 0.5:
                ratio = 0.4
            elif imgratio > 0.1 and imgratio <= 0.2:
                ratio = 0.25
            else:
                ratio = 0.1
        tags = clean_tags(ele)
        outext = template.render(tags=tags, geom=geom, image=pngname,
                                 ratio=ratio)
        outfile.write(outext)
        outfile.close()
        # create the pdf
        if pdf:
            self._create_pdf(outfile.name)
        return True

    def print_all(self, out_type='REF', pdf=False):
        """Print or save the tex file for all elements

        :param str out_type: parameter to choose the method and the name of the
                             output file
        :param bool pdf: convert the tex files to pdf
        """
        # for each relation create its own tex file
        for elem in self.json:
            self.print_single(elem, out_type, pdf)
        return 0

    def write_book(self, output, pdf=False, remove=True):
        """Write all the relations in one document

        :param str output: output file name without extension
        :param bool pdf: convert the tex files to pdf
        :param bool remove: remove unused file
        """
        refs = []
        outfiles = []
        # create the single document for each relation
        for elem in self.json:
            if self.geo:
                idd = elem['properties']['id']
            else:
                idd = elem['id']
            name = 'sentiero_{}.tex'.format(idd)
            if self.print_single(elem, out_type='ID', pdf=False,
                                 intemp='simple.tex'):
                outfiles.append(os.path.join(self.output_dir, name))
                refs.append(idd)
        # create the final document including the tex file previously created
        template = self.latex_jinja_env.get_template('document.tex')
        outext = template.render(refs=refs)
        outfile = open(os.path.join(self.output_dir, output), 'w')
        outfile.write(outext)
        outfile.close()
        # convert to PDF
        if pdf:
            self._create_pdf(outfile.name)
        if remove:
            for ref in outfiles:
                os.remove(ref)
                os.remove(ref.replace('.tex', '.aux'))
                os.remove(ref.replace('.tex', '.png'))
        return 0
