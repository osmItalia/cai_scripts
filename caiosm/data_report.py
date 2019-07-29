#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 11:49:25 2019

@author: lucadelu
"""
from time import sleep

from caiosm.data_from_overpass import CaiOsmRoute

REGIONI = ["Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia-Romagna",
           "Friuli Venezia Giulia", "Lazio", "Liguria", "Lombardia", "Marche",
           "Molise", "Piemonte", "Puglia", "Sardegna", "Sicilia", "Toscana",
           "Trentino-Alto Adige/Südtirol", "Umbria", "Veneto",
           "Valle d'Aosta/Vallée d'Aoste"]

class CaiOsmTable:
    """Print or write to a file statistics for regions, it calculate number
    and lenght routes for each region"""

    def __init__(self, regions=REGIONI):
        """Initialize function

        :param list regions: a list of region to process, by default it
                             execute for all Italian regions
        """
        self.regions = regions

    def print_region(self, reg, unit='km'):
        """Return info for each region"""
        cod = CaiOsmRoute(area=reg)
        cod.get_cairoutehandler()
        leng = round(cod.get_length())
        if unit == 'km':
            leng = round(leng / 1000, 1)
        count = cod.cch.count
        return leng, count

    def print_regions(self):
        """Return number of routes and total lenght for each region"""
        for re in self.regions:
            l, c = self.print_region(re)
            print("{re}: {to} percorsi, lunghezza totale {le} "
                  "km\n".format(re=re, le=l, to=c))
            sleep(30)

    def write_regions(self, output):
        """Return number of routes and total lenght for each region

        :param str output: the path for output file
        """
        with open(output, 'w') as fi:
            for re in self.regions:
                l, c = self.print_region(re)
                fi.write("{re}: {to} percorsi, lunghezza totale "
                         "{le} km\n".format(re=re, le=l, to=c))
        return True
