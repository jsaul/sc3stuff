#!/bin/sh

SEISCOMP3_ROOT="$HOME/seiscomp3"
# set up a proper environment
SEISCOMP3_LIB=$SEISCOMP3_ROOT/lib
SEISCOMP3_BIN=$SEISCOMP3_ROOT/bin
SEISCOMP3_SBIN=$SEISCOMP3_ROOT/sbin
LC_ALL=C

export SEISCOMP3_ROOT
export LD_LIBRARY_PATH=$SEISCOMP3_LIB:$LD_LIBRARY_PATH
export PYTHONPATH=/usr/local/lib/python2.7/dist-packages:$SEISCOMP3_ROOT/lib/python:$PYTHONPATH
export PATH=$SEISCOMP3_BIN:$SEISCOMP3_SBIN:$PATH
export LC_ALL


python bin/scbulletin.py --database mysql://sysop:sysop@geofon-proc/seiscomp3 -E gfz2018tabt
