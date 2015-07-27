#!/bin/sh

db="mysql://sysop:sysop@geofon-proc/seiscomp3"
python dump-active-streams.py -d "$db" --debug
