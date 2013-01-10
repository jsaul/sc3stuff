#!/bin/sh

# specify event id(s) on the command line

host="geofon-proc"
#user="mkplayback" # max 10 characters allowed by spread

for evid in "$@"
do
    python make-mseed-playback.py -H "$host" -u "$user" -E "$evid" --debug 2>&1 |
    tee $evid.log
done

