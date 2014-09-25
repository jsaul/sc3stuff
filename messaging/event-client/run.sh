#!/bin/sh

. ~/.seiscomp3/env.sh

python event-client.py  -u xyzabc -H geofon-proc
