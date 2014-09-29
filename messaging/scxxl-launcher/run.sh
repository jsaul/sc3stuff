#!/bin/sh

. ~/.seiscomp3/env.sh
export PYTHONPATH=../event-client:$PYTHONPATH

date
python xxl-launcher.py --debug  -u js.test -H geofon-proc
date

