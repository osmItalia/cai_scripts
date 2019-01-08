#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

# Get the long description from the relevant file
with open('README.rst') as f:
    long_description = f.read()

setup(
    name='caiosm',
    version=__import__("caiosm").__version__,
    description="Tools to work with Club Alpino Italiano OpenStreetMap data",
    keywords="Club Alpino Italiano,CAI,OpenStreetMap,OSM",
    packages=find_packages(),
    include_package_data=True,
    install_requires=open('requirements.txt').read().splitlines(),
    long_description=long_description,
    author='Luca Delucchi',
    author_email='luca.delucchi@fmach.it',
    license='GPLv3+',
    entry_points="""
    [console_scripts]
    caiosm=caiosm.scripts.caiosm:main
    """
)
