#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan  5 00:14:45 2019

@author: lucadelu
"""
import os
import shutil
import jinja2
from .functions import _run_cmd
from .functions import clean_tags
from .functions import create_map
from .functions import image_ratio
from .functions import geom_geojson

# full path of the file, used to get directory for latex templates
DIRFILE = os.path.dirname(os.path.realpath(__file__))

OSMTILES = {
    "terrain": "http://tile.stamen.com/terrain/tileZ/tileX/tileY.png",
    "osm": "https://a.tile.openstreetmap.org/tileZ/tileX/tileY.png",
    "cycle": "http://tile.thunderforest.com/cycle/tileZ/tileX/tileY.png",
    "wiki": "https://maps.wikimedia.org/osm-intl/tileZ/tileX/tileY.png",
}


class CaiOsmReport:
    """Class to print route info into a report"""

    def __init__(self, myjson, geo=False, output_dir=".", debug=None):
        """Inizialize

        :param obj myjson: json containg tags and id of a list of relations, it
                           is possible to get it from
                           data_from_overpass - CaiOsmData - get_tags_json
        :param bool geo: set if the input json is a geojson
        :param str output_dir: the directory where save the output file
        """
        self.geo = geo
        self.json = myjson
        # create jinja environment for latex
        self.latex_jinja_env = jinja2.Environment(
            block_start_string="\BLOCK{",
            block_end_string="}",
            variable_start_string="\VAR{",
            variable_end_string="}",
            comment_start_string="\#{",
            comment_end_string="}",
            line_statement_prefix="%%",
            line_comment_prefix="%#",
            trim_blocks=True,
            autoescape=False,
            loader=jinja2.FileSystemLoader(os.path.join(DIRFILE, "latex_template")),
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
                raise Exception(
                    "Folder to store output files does not " "exist or is not writeable"
                )

    def _create_pdf(self, infile, optimize=True):
        """Private function to convert tex file to pdf

        :param str infile: path to input tex file
        :param bool optimize: Optimize the PDF to decrease the size
        """
        # check if pdflatex is installed
        if shutil.which("pdflatex"):
            cmd = (
                "pdflatex -interaction=nonstopmode -output-directory={di}"
                " {inf}".format(di=self.output_dir, inf=infile)
            )
            _run_cmd(cmd)
        else:
            raise Exception("pdflatex not found. Please install it to get PDF" " files")

        if optimize:
            if shutil.which("gs"):
                ori = os.path.join(self.output_dir, "{}.pdf".format(infile))
                opti = os.path.join(self.output_dir, "opti_{}.pdf".format(infile))
                cmd = (
                    "gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.5 "
                    '-dNOPAUSE -dQUIET -dBATCH -sOutputFile="{ofile}" '
                    '"{ifile}"'.format(ifile=ori, ofile=opti)
                )
                _run_cmd(cmd)
                if os.path.exists(ori):
                    os.remove(ori)
                shutil.move(opti, ori)
            else:
                raise Exception(
                    "gs not found. Please install Ghostscript to " "get PDF files"
                )
        return True

    def print_single(self, elem, out_type="REF", pdf=False, intemp="single.tex"):
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
            ele = elem["properties"]
            geom = True
        else:
            ele = elem
            geom = False
        if "ref" not in ele.keys():
            print("Relazione con id {} non ha il campo ref".format(ele["id"]))
            return False
        if out_type == "REF":
            idd = ele["ref"]
        elif out_type == "NAME":
            idd = ele["name"].replace(" ", "_").replace("'", "_")
        elif out_type == "ID":
            idd = ele["id"]
        else:
            raise ValueError("output value options are: REF and NAME")
        tags = clean_tags(ele)
        outname = "sentiero_{}.tex".format(idd)
        outfile = open(os.path.join(self.output_dir, outname), "w")
        # if geometry exists it print also a static map
        if geom:
            pngname = os.path.join(self.output_dir, "sentiero_{}.png".format(idd))
            create_map(geom_geojson(elem["geometry"]), pngname)
            # get the ration for map and pass it to the tex template
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
            outext = template.render(tags=tags, geom=geom, image=pngname, ratio=ratio)
        else:
            outext = template.render(tags=tags, geom=geom)
        outfile.write(outext)
        outfile.close()
        # create the pdf
        if pdf:
            self._create_pdf(outfile.name)
        return True

    def print_all(self, out_type="REF", pdf=False):
        """Print or save the tex file for all elements

        :param str out_type: parameter to choose the method and the name of the
                             output file
        :param bool pdf: convert the tex files to pdf
        """
        # for each relation create its own tex file
        for elem in self.json:
            self.print_single(elem, out_type, pdf)
        return True

    def write_book(self, output, pdf=False, remove=True):
        """Write all the relations in one document

        :param str output: output file name without extension
        :param bool pdf: convert the tex files to pdf
        :param bool remove: remove unused file
        """
        refs = []
        outfiles = []
        # create the single document for each relation
        if self.geo:
            feats = self.json["features"]
        else:
            feats = self.json
        for elem in feats:
            if self.geo:
                idd = elem["properties"]["id"]
            else:
                idd = elem["id"]
            name = "sentiero_{}.tex".format(idd)
            if self.print_single(elem, out_type="ID", pdf=False, intemp="simple.tex"):
                outfiles.append(os.path.join(self.output_dir, name))
                refs.append(idd)
        # create the final document including the tex file previously created
        template = self.latex_jinja_env.get_template("document.tex")
        outext = template.render(refs=refs)
        outfile = open(os.path.join(self.output_dir, output), "w")
        outfile.write(outext)
        outfile.close()
        # convert to PDF
        if pdf:
            self._create_pdf(output)
        if pdf and remove:
            # remove tex file for each single hiking path
            for ref in outfiles:
                try:
                    os.remove(ref)
                    os.remove(ref.replace(".tex", ".aux"))
                    os.remove(ref.replace(".tex", ".log"))
                except FileNotFoundError:
                    pass
            # remove all images
            all_files = os.listdir(".")
            png_files = [file for file in all_files if file.endswith(".png")]
            for file in png_files:
                os.remove(path_to_file)

        return True
