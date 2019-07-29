#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 19 22:18:37 2019

@author: lucadelu
"""

from caiosm.data_from_overpass import CaiOsmRouteDiff
from caiosm.data_from_overpass import CaiOsmSourceRef

class ManageChanges():
    
    def __init__(self, type='sezioni', sendby='mail'):
        self.type = type
        self.sendby = sendby
        if self.type == 'sezioni':
            self.cosr = CaiOsmSourceRef()
            self.cosr.get_list_codes()
            
    def send_mail():
        """"""