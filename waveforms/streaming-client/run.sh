#!/bin/sh

# take your pick:

datasource="slink://geofon.gfz-potsdam.de:18000"
datasource="arclink://webdc.eu:18001"
datasource="fdsnws://geofon.gfz-potsdam.de/fdsnws/dataselect/1/query"
datasource="fdsnws://service.iris.edu/fdsnws/dataselect/1/query"

seiscomp exec python streaming-client.py --debug -I "$datasource"

