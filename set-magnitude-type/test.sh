#!/bin/sh

evid=gfz2015ncme
#evid=gfz2015iatp
python setmagtype.py -H geofon-proc -d mysql://sysop:sysop@geofon-proc/seiscomp3 -E $evid --magnitude-type Mw

