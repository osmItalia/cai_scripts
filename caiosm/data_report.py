#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 11:49:25 2019

@author: lucadelu
"""
from time import sleep
from datetime import datetime
from datetime import timedelta
import matplotlib.pyplot as plt

from caiosm.data_from_overpass import CaiOsmRoute
from caiosm.data_from_overpass import CaiOsmRouteDate
from caiosm.functions import REGIONI

SINGULAR_GRAN = ["day", "month", "year"]
PLURAL_GRAN = ["days", "months", "years"]
SUPPORTED_GRAN = SINGULAR_GRAN + PLURAL_GRAN

def delta(gran):
    """Return the value """
    output, unit = gran.split(" ")
    if unit in PLURAL_GRAN:
        return (int(output), unit[:-1])
    elif unit in SINGULAR_GRAN:
        return (int(output), unit)
    else:
        print("Supported delta values are: {}".format(', '.join(SUPPORTED_GRAN)))

class CaiOsmTable:
    """Print or write to a file statistics for regions, it calculate number
    and lenght routes for each region"""

    def __init__(self, regions=REGIONI.keys()):
        """Initialize function

        :param list regions: a list of region to process, by default it
                             execute for all Italian regions
        """
        self.regions = regions

    def print_region(self, reg, unit='km'):
        """Return info for each region"""
        cod = CaiOsmRoute(area=reg)
        cod.get_cairoutehandler()
        leng = cod.get_length(unit=unit)
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

class CaiOsmHistory:
    """Return data about the history of data"""
    def __init__(self, startdate, enddate, deltatime, regions=REGIONI.keys(),
                 sleep=60):
        """Initialize function
        :param str startdate: the starting date in format YYYY-MM-DD
        :param str enddate: a ending date in format YYYY-MM-DD
        :param str deltatime: a delta time, options string like "1 day",
                              "2 months", "6 months", "1 year"
        :param list regions: a list of region to process, by default it
                             execute for all Italian regions
        """
        self.regions = regions
        self.startdate = datetime.strptime(startdate, '%Y-%m-%d')
        self.enddate = datetime.strptime(enddate, '%Y-%m-%d')
        thisdelta = delta(deltatime)
        self.times = [self.startdate]
        time = self.startdate
        while time <= self.enddate:
            if thisdelta[1] == 'day':
                time = time + timedelta(days=thisdelta[0])
            elif thisdelta[1] == 'month':
                newmonth = time.month + thisdelta[0]
                nyear = 0
                if newmonth > 12:
                    while newmonth > 12:
                        nyear += 1
                        newmonth = newmonth - 12
                newyear = time.year + nyear
                time = time.replace(year=newyear, month=newmonth)
            elif thisdelta[1] == 'year':
                newyear = time.year + thisdelta[0]
                time = time.replace(year=newyear)
            self.times.append(time)
        self.sleep = sleep

    def italy_history(self):
        output = {}
        for y in self.times:
            data = y.strftime('%Y-%m-%d')
            cord = CaiOsmRouteDate(startdate=y, area='Italia')
            cord.get_cairoutehandler()
            output[data] = [cord.cch.count, cord.length(unit='km')]
            sleep(self.sleep)
        return output

    def reg_history(self, region):
        output = {}
        for y in self.times:
            data = y.strftime('%Y-%m-%d')
            cord = CaiOsmRouteDate(startdate=y, area=region)
            cord.get_cairoutehandler()
            output[data] = [cord.cch.count, cord.get_length(unit='km')]
            sleep(self.sleep)
        return output

    def regions_history(self):
        output = {}
        for re in self.regions:
            output[re] = self.reg_history(re)
            sleep(self.sleep)
        return output
