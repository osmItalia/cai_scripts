#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 10:41:25 2020

@author: lucadelu
"""
import os
import sys

DIRFILE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, DIRFILE)

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
