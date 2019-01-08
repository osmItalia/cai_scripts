#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan  5 00:14:45 2019

@author: lucadelu
"""

import jinja2
import os
import sys
from subprocess import Popen, PIPE

class CaiOsmReport:
    
    def __init__(self, myjson, output_dir='.'):
        """Class to print relation info into
        
        :param obj myjson: json containg tags and id of a list of relations, it
                           is possible to get it from 
                           data_from_overpass - CaiOsmData - get_tags_json
        :param str output_dir: the directory where save the output file
        """
        self.json = myjson
        self.latex_jinja_env = jinja2.Environment(
            block_start_string = '\BLOCK{',
            block_end_string = '}',
            variable_start_string = '\VAR{',
            variable_end_string = '}',
            comment_start_string = '\#{',
            comment_end_string = '}',
            line_statement_prefix = '%%',
            line_comment_prefix = '%#',
            trim_blocks = True,
            autoescape = False,
            loader = jinja2.FileSystemLoader(os.path.abspath('./latex_template'))
        )
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
        cmd = 'pdflatex -interaction=nonstopmode -output-directory={di} {inf}'.format(
               di=self.output_dir, inf=infile)
        proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE )
        out, err = proc.communicate()
        retcode = proc.returncode
        if not retcode == 0:
            print(err)
            raise ValueError('Error {} executing command: {}'.format(retcode,
                                                                     cmd)) 

    def _clean_tags(self, tags):
        newtags = {}
        for k in tags.keys():
            if ':' in k:
                newtags[k.replace(':','')] = tags[k]
            else:
                newtags[k] = tags[k]
        return newtags
        
    def print_single(self, out_type=None, pdf=False):
        """Print or save the tex file for each element

        :param str out_type: parameter to choose the method and the name of the
                           output file
        :param bool pdf: convert the tex files to pdf
        """
        template = self.latex_jinja_env.get_template('single.tex')
        # for each relation create its own tex file
        for ele in self.json:
            if 'ref' not in ele.keys():
                print("Relazione con id {} non ha il campo ref".format(ele['id']))
                continue
            if not out_type:
                outfile = sys.stdout
            elif out_type == 'REF':
                outname = 'sentiero_{}.tex'. format(ele['ref'])
                outfile = open(os.path.join(self.output_dir, outname), 'w')
            elif out_type == 'NAME':
                outname = '{}.tex'. format(ele['name'].replace(' ', '_'))
                outfile = open(os.path.join(self.output_dir, outname), 'w')
            else:
                raise ValueError("output value options are: REF and NAME")
            tags = self._clean_tags(ele)
            outext = template.render(tags=tags)
            outfile.write(outext)
            if outfile.name != '<stdout>':
                outfile.close()
            # create the pdf
            if pdf:
                self._create_pdf(outfile.name)
    
    def write_book(self, output, out_type, pdf=False):
        """Write all the relations in one document
        
        :param str output:
        :param str out_type: parameter to choose the method and the name of the
                           output file
        :param bool pdf: convert the tex files to pdf
        """
        template = self.latex_jinja_env.get_template('simple.tex')
        refs = []
        # create the single document for each relation
        for ele in self.json:
            if 'ref' not in ele.keys():
                print("Relazione con id {} non ha il campo ref".format(ele['id']))
                continue
            if out_type == 'REF':
                name = ele['ref']
                outname = 'testo_{}.tex'. format(name)
                refs.append(name)
                outfile = open(os.path.join(self.output_dir, outname), 'w')
            elif out_type == 'NAME':
                name = ele['name'].replace(' ', '_')
                outname = '{}.tex'. format(name)
                refs.append(name)
                outfile = open(os.path.join(self.output_dir, outname), 'w')
            else:
                raise ValueError("output value options are: REF and NAME")
            tags = self._clean_tags(ele)
            outext = template.render(tags=tags)
            outfile.write(outext)
            outfile.close()
        # create the final document including the tex file previously created
        template = self.latex_jinja_env.get_template('document.tex')
        refs.sort()
        outext = template.render(refs=refs)
        outfile = open(os.path.join(self.output_dir, output), 'w')
        outfile.write(outext)
        outfile.close()
        # convert to PDF
        if pdf:
            self._create_pdf(outfile.name)
        
