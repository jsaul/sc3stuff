#!/bin/sh

evt="$1" comment="$2"

###### configuration #######
# Give address of database
db="mysql://sysop:sysop@geofon-proc1/seiscomp3"
############################

if test -z "$evt"
then
    echo "specify event ID"
    exit 1
fi

#debug="--debug"

test -x ~/.seiscomp3/env.sh && . ~/.seiscomp3/env.sh
export PATH=$PATH:.

mkdir -p config
for f in grid.conf station.conf
do
    test -f config/$f || cp -p ~/seiscomp3/share/scautoloc/$f config/
done

mkdir -p "$evt"
dump-picks-to-xml.py $debug --event "$evt" -d "$db"   > "$evt"/objects.xml
test -z "$comment" || echo "$evt  $comment"           > "$evt"/comment.txt
dump-station-locations.py $debug -d "$db"             > "$evt"/station-locations.txt
scbulletin $debug -3 -d "$db" -E "$evt"               > "$evt"/bulletin
