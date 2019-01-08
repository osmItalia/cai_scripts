caiosm make download, analize and print **Club Alpino Italiano (CAI)** data stored in **OpenStreetMap (OSM)** easy.

To get more info about the collaboration between CAI and OSM read https://wiki.openstreetmap.org/wiki/CAI

How to use
==========

Command Line tool
-----------------

`caiosm` is a great tool to get data or print routes info in several format

.. code-block:: bash

    # print Mezzocorona routes in mediawiki table
    caiosm --place Mezzocorona -w

    # get a PDF file (the name will be ischia.pdf) with all the info of Ischia's routes
    caiosm --box 40.643656594949,13.76106262207,40.818226355892,14.062843322754 -p ischia

    # for more info
    caiosm --help

Library
-------

The library is composed by submodules for specific operation.

To download data Overpass API use `data_from_overpass`

.. code-block:: python

    from caiosm.data_from_overpass import CaiOsmData
    # it is possible to set a place or a bounding box as
    # area of interest
    cod = CaiOsmData(area='Mezzocorona')
    #codbox = CaiOsmData(bbox='40.643656594949,13.76106262207,40.818226355892,14.062843322754')
    
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


