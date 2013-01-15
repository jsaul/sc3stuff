#!/bin/sh

# specify event id(s) on the command line
host="geofon-proc"
#user="mkplayback" # max 10 characters allowed by spread
arch="geofon-acqui:18001"


for evid in "$@"
do
    python make-mseed-playback.py -H "$host" -I arclink://$arch --user "$user" -E "$evid" --debug 2>&1 |
#   python make-mseed-playback.py -H "$host" -I arclink://$arch --user "$user" -E "$evid" --debug 2>&1 |
    tee $evid.log
done

