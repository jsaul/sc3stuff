#!/bin/sh

###### configuration #######
# Give name of processing host
host="geofon-proc"
# Give location of waveform archive
arch="arclink://geofon-acqui:18001"
############################

# specify event id(s) on the command line



for evid in "$@"
do
    python make-mseed-playback.py -H "$host" -I $arch --user "" -E "$evid" --debug 2>&1 |
    tee $evid.log
    scxmldump --inventory --formatted -o $evid-inventory.xml -d mysql://sysop:sysop@$host/seiscomp3 --debug
done

