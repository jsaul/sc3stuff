#!/bin/sh

# take your pick:

input="slink://geofon.gfz-potsdam.de:18000"
input="arclink://webdc.eu:18001"
input="fdsnws://geofon.gfz-potsdam.de/fdsnws/dataselect/1/query"
input="fdsnws://service.iris.edu/fdsnws/dataselect/1/query"

seiscomp exec python timewindow-client.py --debug -I "$input"

