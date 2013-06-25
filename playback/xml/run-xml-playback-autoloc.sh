#!/bin/sh

test -x ~/.seiscomp3/env.sh && . ~/.seiscomp3/env.sh      
export PATH=$PATH:.
export LC_ALL=C

evt="$1"

debug="--debug"

if test -z "$evt"
then
    echo "specify event ID"
    exit 1
fi

strip_time () {
    sed 's/[0-9][0-9]:[0-9][0-9]:[0-9][0-9] \[/[/'
}




case "$evt" in
gfz*)
    descr="playbacks/$evt/description.txt"
    test -f "Â$descr" || wget -O "$descr" "http://geofon.gfz-potsdam.de/eqinfo/event.php?id=$evt&fmt=txt" >/dev/null 2>&1
    ( cat "$descr"; echo ) >&2
    ;;
esac

xml="playbacks/$evt/objects.xml"

#valgrind --track-origins=yes -v \
scautoloc -v --console=1 $debug \
    --use-manual-origins 1 \
    --offline --playback --input "$xml" --speed 0 \
    --station-locations   playbacks/$evt/station-locations.txt \
    --station-config      config/station.conf \
    --grid                config/grid.conf \
    2>&1 |
strip_time | tee $evt-playback.log

grep OUT $evt-playback.log

