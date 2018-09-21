#!/bin/sh

evt="$1" comment="$2"

###### configuration #######
# Give address of database
db="mysql://sysop:sysop@geofon-proc/seiscomp3"
############################

if test -z "$evt"
then
    echo "specify event ID"
    exit 1
fi

#debug="--debug"
timewindow="--event $evt --before=7200 --after=3600"

mkdir -p config
for f in grid.conf station.conf
do
    test -f config/$f || cp -p ~/seiscomp3/share/scautoloc/$f config/
done

mkdir -p "playbacks/$evt"
$HOME/seiscomp3/bin/seiscomp exec \
    python sc3playback.dump-picks.py $timewindow $debug -d "$db" \
    > "playbacks/$evt"/objects.xml

test -z "$comment" || echo "$evt  $comment" \
    > "playbacks/$evt"/comment.txt

$HOME/seiscomp3/bin/seiscomp exec \
    python sc3playback.dump-stations.py $debug -d "$db" \
    > "playbacks/$evt"/station-locations.txt

$HOME/seiscomp3/bin/seiscomp exec \
    scbulletin $debug -3 -d "$db" -E "$evt" \
    > "playbacks/$evt"/bulletin
