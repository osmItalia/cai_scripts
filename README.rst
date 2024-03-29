caiosm make download, convert, analize, print and show **Club Alpino Italiano (CAI)** data stored in **OpenStreetMap (OSM)** easy.

To get more info about the collaboration between CAI and OSM read https://wiki.openstreetmap.org/wiki/CAI

How to install
==============

From source
------------

Download the source code from Github (you need git command for this)

.. code-block:: bash

   git clone https://github.com/osmItalia/cai_scripts.git

Now you need to install all packages needed by caiosm Python requirements

  * gcc compiler (on Debian and derivates I suggest to install build-essential)
  * python3 and its development packages
  * virtualenv
  * proj (and its development packages)
  * geos (and its development packages)
  * PostgreSQL library development

On Debian and derivates you can use the following `apt` command

.. code-block:: bash

   apt install build-essential virtualenv python3-dev libgeos-dev libproj-dev proj-bin libgeos-c1v5 libpq-dev

Now it is the time to create a virtual Python environment and install caiosm dependencies

.. code-block:: bash

   # enter in cai_scrips directory
   cd cai_scripts

   # create virtual environment
   virtualenv -p python3 venv

   # activate the virtual environment
   source venv/bin/activate

   # install numpy
   pip install numpy

   # install CAIOSM dependencies
   pip install -r requirements.txt

   # if previous command run correctly now you can install caiosm
   python setup.py install

   # now you can test caiosm installation
   caiosm --help

How to use
==========

Command Line tool
-----------------

`caiosm` is a great tool to work with CAI data; it has several sub-command to run
different operation

.. code-block:: bash

    # to get more info
    caiosm --help

Get data
^^^^^^^^

.. code-block:: bash

    # save Mezzocorona routes  to a GeoJSON file
    caiosm --place Mezzocorona route -G /tmp/mezzocorona.geojson

    # save Pisa routes to a JSON format
    caiosm --place Pisa route -J /tmp/pisa.json

    # save Pisa routes in XML OSM format
    caiosm --place Pisa route -O /tmp/pisa.osm

    # print Mezzocorona routes in mediawiki table
    caiosm --place Mezzocorona route -w

    # print Ischia routes in JSON format
    caiosm --box 40.643656594949,13.76106262207,40.818226355892,14.062843322754 route -j

    # for more info about route sub-command
    caiosm route --help

    # print CAI office in Toscana to a JSON format
    caiosm --place Toscana office -j

Create a PDF report
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # get a PDF file (the name will be ischia.pdf) with all the info of Ischia's routes
    caiosm --box 40.643656594949,13.76106262207,40.818226355892,14.062843322754 report -o ischia


    # get a PDF file (the name will be ischia.pdf) with all the info of Ischia's routes
    # with maps
    caiosm --box 40.643656594949,13.76106262207,40.818226355892,14.062843322754 report -g -o ischia_geo

Convert Infomont
^^^^^^^^^^^^^^^^

.. code-block:: bash

    # convert Isola d'Elba OSM data in Infomont format
    # check the result in the /tmp/elba directory
    caiosm --place "Isola d'Elba" infomont -o /tmp/elba

Send updates
^^^^^^^^^^^^

.. code-block:: bash
    
    # send updates for all the Italian Regions
    caiosm --config ~/cai_scripts.ini updates

Library
-------

The library is composed by submodules for specific operation.

To download data Overpass API use `data_from_overpass`

.. code-block:: python

    from caiosm.data_from_overpass import CaiOsmData
    # it is possible to set a place or a bounding box as
    # area of interest
    cod = CaiOsmRoute(area='Mezzocorona')
    #codbox = CaiOsmRoute(bbox='40.643656594949,13.76106262207,40.818226355892,14.062843322754')

    # get the tags of relations as list of dictionaries
    # check the first value with tags[0]
    tags = cod.get_tags_json()

    # get the data in csv
    # by default it require id,name,ref
    csv = cod.get_data_csv()
    print(csv)

    # get more tags
    csvext = cod.get_data_csv(csvheader=True,
                              tags='::id,"name","ref","cai_scale","from","to"')

    # get OSM data in original format (XML)
    osm = cod.get_data_osm()

To print PDF file with route information use `data_print`. It uses jinja2 library to a Latex file
and convert it using `pdflatex` utility.

.. code-block:: python

    from caiosm.data_print import CaiOsmReport
    # set up using tags obtained before using
    # cod.get_tags_json()
    cor = CaiOsmReport(tags)

    # create PDF file with all the routes in a single file
    # removing the True it will create only tex files
    cor.write_book('mezzocorona',True)
    # create PDF file for each singular route
    cor.print_single(pdf=True)


