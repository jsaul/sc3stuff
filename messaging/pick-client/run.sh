#!/bin/sh

. ~/.seiscomp3/env.sh

python pickclient.py -u xyzabc -H geofon-proc --debug
