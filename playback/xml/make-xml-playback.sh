#!/bin/sh -e

evt="$1" comment="$2"

###### configuration #######
# Give address of database
db="mysql://sysop:sysop@geofon-proc/seiscomp3"
#db="mysql://sysop:sysop@geofon-proc2/seiscomp3_archive"
############################

if test -z "$evt"
then
    echo "specify event ID"
    exit 1
fi

#debug="--debug"
timewindow="--event $evt --before=86400 --after=86400"

mkdir -p config
for f in grid.conf station.conf
do
    test -f config/$f || cp -p ~/seiscomp3/share/scautoloc/$f config/
done

mkdir -p "playbacks/$evt"
~/seiscomp-agpl/bin/seiscomp-python \
    sc3playback.dump-picks.py $timewindow $debug -d "$db" \
    > "playbacks/$evt"/objects.xml

test -z "$comment" || echo "$evt  $comment" \
    > "playbacks/$evt"/comment.txt

~/seiscomp-agpl/bin/seiscomp-python \
    sc3playback.dump-stations.py $debug -d "$db" \
    > "playbacks/$evt"/station-locations.txt

$HOME/seiscomp-agpl/bin/seiscomp exec \
    scbulletin $debug -3 -d "$db" -E "$evt" \
    > "playbacks/$evt"/bulletin
