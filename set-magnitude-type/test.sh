#!/bin/sh

#python set-magnitude-type.py --xml $HOME/Work/Picker/data/2015/gfz2015iatp/gfz2015iatp.xml

evid=gfz2015ncme
#evid=gfz2015iatp
python setmagtype.py -H geofon-proc -d mysql://sysop:sysop@geofon-proc/seiscomp3 -E $evid --magnitude-type Mw

