#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  7 15:31:54 2020

@author: lucadelu
"""

from .osmium_handler import CaiRoutesHandler
from .functions import invert_bbox
from .functions import check_network


class CaiOsmBase:
    """Base class to get CAI data using Overpass API"""

    def __init__(
        self, area=None, bbox=None, bbox_inverted=False, separator="|", debug=False
    ):
        """Inizialize

        :param str area: the name of the area of interest
        :param str bbox: a string with the bounding box of the area, needed
                         format is YMIN,XMIN,YMAX,XMAX
        :param bool bbox_inverted: set True id the bbox format is
                                    XMIN,YMIN,XMAX,YMAX
        :param str separator: the separator to use for CSV
        :param bool debug: print debug information
        """
        self.area = area
        if bbox_inverted:
            self.bbox = invert_bbox(bbox)
        else:
            self.bbox = bbox
        self.csvheader = False
        self.separator = separator
        self.debug = debug
        self.cch = None


class CaiOsmRoute(CaiOsmData):
    """Class to get CAI routes using Overpass API and convert in different
    formats"""

    def __init__(self, **kwargs):
        """Inizialize

        :param str area: the name of the area of interest
        :param str bbox: a string with the bounding box of the area, needed
                         format is YMIN,XMIN,YMAX,XMAX
        :param bool bbox_inverted: set True id the bbox format is
                                    XMIN,YMIN,XMAX,YMAX
        :param str separator: the separator to use for CSV
        :param bool debug: print debug information
        :param int timeout: the timeout value for overpass
        """
        super(CaiOsmRoute, self).__init__(**kwargs)
        self.cch = None
        self.lenght = None
        self.query = """
"route=hiking AND {netw} AND cai_scale"
  ({bbox});
"""
