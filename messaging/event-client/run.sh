#!/bin/sh

. ~/.seiscomp3/env.sh

date
python eventclient.py --debug  -u js.test -H geofon-proc
date
