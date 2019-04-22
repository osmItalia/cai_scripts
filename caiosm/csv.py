#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 26 00:11:36 2019

@author: lucadelu
"""

import os
import pandas as pd

class CsvToWikiTable:
    """Class to convert CSV file to wiki tables; the CSV needs an aggregation
    column like the name of the different CAI groups (sezioni) or mountains

    Good idea is to clean your CSV file with OpenRefine
    """

    def __init__(self, inp, aggr, sep='|'):
        """
        :param str inp: the path to the CSV file
        :param str aggr: the name of the column for aggregation
        :param str sep: the CSV separator character
        """
        self.input = inp
        self.df = pd.read_csv(self.input, sep=sep)
        self.column = aggr
        self.group = None
    
    def get_group(self):
        """Populate a list with the name of the aggregation group"""
        self.group = self.df[self.column].unique()
    
    def group_table(self, dat, idcol):
        """Write a mediawiki table for singular aggregated values
        
        :param dat:
        :param str idcol: the column with routes id
        """
        if type(dat) == str:
            dat = self.df.loc[self.df[self.column] == dat]
        out = '{| class="wikitable sortable mw-collapsible mw-collapsed" \n'
        out += '|-\n'
        out += '!Ref\n!Nome\n!Link route\n!%Completamento\n!Note\n'
        for k, v in dat.iterrows():
            out += '|-\n'
            try:
                cod = str(int(float(v.get(idcol))))
            except:
                cod = str(v.get(idcol))
            if cod:
                # could be done better, but format is easting {}
                out += '| ' + cod + ' || || || {{Progress|0}} || \n'
        out += '|-\n|}\n'
        return out
        
    def groups_table(self, idcol, outdir=None, suffix=None):
        """Write a mediawiki table for all sezioni
        
        :param str idcol: the column with routes id
        :param str outdir: the path to output files, the default None value
                           print the text instead to save in a file
        :param str suffix: the name of a column to use as prefix of output file
                           the default None add no suffix
        """
        if self.sezioni == None:
            self.get_group()
        for sez in self.group:
            dat = self.df.loc[self.df[self.column] == sez]
            text = self.sezione_table(dat, idcol)
            if not outdir:
                print(text)
            else:
                outname = '{}.txt'.format(sez)
                if suffix:
                    vals = dat[suffix].value_counts().sort_values()
                    if len(vals) > 0:
                        print(vals)
                        outname = '{pr}_{pa}'.format(pr=vals.argmax(), pa=outname)
                    else:
                        continue
                outpath = os.path.join(outdir, outname)
                with open(outpath, 'w') as fil:
                    fil.write(text)
        return True
