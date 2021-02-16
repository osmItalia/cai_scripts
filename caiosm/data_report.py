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
import numpy as np
from caiosm.data_from_overpass import CaiOsmRoute
from caiosm.data_from_overpass import CaiOsmRouteDate
from caiosm.functions import REGIONI

SINGULAR_GRAN = ["day", "month", "year"]
PLURAL_GRAN = ["days", "months", "years"]
SUPPORTED_GRAN = SINGULAR_GRAN + PLURAL_GRAN

BIGFONT = {"fontname": "Arial", "size": "24", "weight": "bold"}
NORMALFONT = {"fontname": "Arial", "size": "20"}
SMALLFONT = {"fontname": "Arial", "size": "16"}


def delta(gran):
    """Return the value """
    output, unit = gran.split(" ")
    if unit in PLURAL_GRAN:
        return (int(output), unit[:-1])
    elif unit in SINGULAR_GRAN:
        return (int(output), unit)
    else:
        print("Supported delta values are: {}".format(", ".join(SUPPORTED_GRAN)))


def plot_one(data, title, outname=None, dpi=300):
    xlabels = sorted(list(data.keys()))
    xs = np.arange(0, len(xlabels))
    nums = []
    counts = []
    for x in xlabels:
        nums.append(data[x][0])
        counts.append(data[x][1])
    fig, ax1 = plt.subplots()
    ax1col = "green"
    ax1.set_xticks(range(len(xlabels)))
    ax1.set_xticklabels(xlabels)
    ax1.bar(xs, nums, color=ax1col)
    ax1.tick_params(axis="y", colors=ax1col, labelsize=NORMALFONT["size"])
    ax1.tick_params(axis="x", labelsize=SMALLFONT["size"])
    ax2 = ax1.twinx()
    ax2col = "red"
    ax2.set_ylabel("Chilometri", labelpad=40, **NORMALFONT, color=ax2col)
    ax2.plot(xs, counts, color=ax2col)
    ax2.tick_params(axis="y", colors=ax2col, labelsize=NORMALFONT["size"])
    ax1.set_xlabel("Data", labelpad=40, **NORMALFONT)
    ax1.set_ylabel("Numero sentieri", labelpad=40, **NORMALFONT, color=ax1col)
    ax1.set_title(title, **BIGFONT)
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show()
    if outname:
        plt.savefig(outname, dpi=dpi)
        plt.close()
    else:
        plt.show()
    return True


class CaiOsmTable:
    """Print or write to a file statistics for regions, it calculate number
    and lenght routes for each region"""

    def __init__(self, regions=REGIONI.keys()):
        """Initialize function

        :param list regions: a list of region to process, by default it
                             execute for all Italian regions
        """
        self.regions = regions

    def print_region(self, reg, unit="km"):
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
            print(
                "{re}: {to} percorsi, lunghezza totale {le} "
                "km\n".format(re=re, le=l, to=c)
            )
            sleep(30)

    def write_regions(self, output):
        """Return number of routes and total lenght for each region

        :param str output: the path for output file
        """
        with open(output, "w") as fi:
            for re in self.regions:
                l, c = self.print_region(re)
                fi.write(
                    "{re}: {to} percorsi, lunghezza totale "
                    "{le} km\n".format(re=re, le=l, to=c)
                )
        return True


class CaiOsmHistory:
    """Return data about the history of data"""

    def __init__(
        self,
        startdate,
        enddate=None,
        deltatime=None,
        regions=REGIONI.keys(),
        sleep=300,
        debug=False,
    ):
        """Initialize function
        :param str startdate: the starting date in format YYYY-MM-DD
        :param str enddate: a ending date in format YYYY-MM-DD
        :param str deltatime: a delta time, options string like "1 day",
                              "2 months", "6 months", "1 year"
        :param list regions: a list of region to process, by default it
                             execute for all Italian regions
        :param list sleep: seconds to wait between two overpass query
        :param bool debug: print debug information
        """
        self.regions = regions
        self.debug = debug
        self.startdate = datetime.strptime(startdate, "%Y-%m-%d")
        self.times = [self.startdate]
        if enddate:
            self.enddate = datetime.strptime(enddate, "%Y-%m-%d")
            if deltatime:
                thisdelta = delta(deltatime)
            else:
                raise Exception("deltatime parameter è required with enddate")
            time = self.startdate
            while time <= self.enddate:
                if thisdelta[1] == "day":
                    time = time + timedelta(days=thisdelta[0])
                elif thisdelta[1] == "month":
                    newmonth = time.month + thisdelta[0]
                    nyear = 0
                    if newmonth > 12:
                        while newmonth > 12:
                            nyear += 1
                            newmonth = newmonth - 12
                    newyear = time.year + nyear
                    time = time.replace(year=newyear, month=newmonth)
                elif thisdelta[1] == "year":
                    newyear = time.year + thisdelta[0]
                    time = time.replace(year=newyear)
                self.times.append(time)
        if self.debug:
            print(self.times)
        self.sleep = sleep

    def reg_history(self, region):
        """Return data about the history of CAI path for a region

        :param str region: the name of the region
        """
        output = {}
        for y in self.times:
            data = y.strftime("%Y-%m-%d")
            cord = CaiOsmRouteDate(startdate=y, area=region, debug=self.debug)
            cord.get_cairoutehandler()
            output[data] = [cord.cch.count, cord.get_length(unit="km")]
            sleep(self.sleep)
        if self.debug:
            print(output)
        return output

    def italy_history(self):
        """Return data about the history of CAI path at Italian level"""
        return self.reg_history("Italia")

    def plot_italy(self, outpath=None):
        """Plot data about the history of CAI path at Italian

        :param str outpath: the path to the output Italy plot file, by default it
                            show the graph in the monitor
        """
        data = self.italy_history()
        plot_one(data, "Andamento sentieri CAI in Italia", outpath)
        return True

    def plot_region(self, region, outpath=None):
        """Plot data about the history of CAI path for a region

        :param str region: the name of the region
        :param str outpath: the path to the output region plot file, by default
                            it show the graph in the monitor
        """
        data = self.reg_history(region)
        plot_one(data, "Andamento sentieri CAI in {}".format(region), outpath)
        return True

    def regions_history(self):
        """Return data about the history of CAI path for all Italian regions"""
        output = {}
        for re in self.regions:
            output[re] = self.reg_history(re)
            sleep(self.sleep)
        return output

    def regions_csv(self, outpath=None):
        """Return region's data in csv format

        :param str region: the name of the region
        :param str outpath: the path to the output regions csv file, by default
                            it print the date
        """
        output = "region"
        for t in self.times:
            output += "|{}".format(t.strftime("%Y-%m-%d"))
        output += "\n"
        for re in self.regions:
            output += "{}".format(re)
            regdata = self.reg_history(re)
            for t in self.times:
                output += "|{}".format(regdata[t.strftime("%Y-%m-%d")][1])
            output += "\n"
        if self.debug:
            print(output)
        if outpath:
            fi = open(outpath, "w")
            fi.write(output)
            fi.close()
        else:
            print(output)
        return True
