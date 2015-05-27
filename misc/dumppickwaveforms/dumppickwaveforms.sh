#!/bin/sh

# specify event id's on the command line


# customize here:
h="geofon-proc.gfz-potsdam.de"
d="mysql://sysop:sysop@$h/seiscomp3"
i="arclink://geofon-acqui.gfz-potsdam.de:18001"
x="$HOME/seiscomp3/bin/seiscomp exec python dumppickwaveforms.py "
# no customization below

for e in "$@"
do
    echo $e
    mkdir -p $e
    $x -I "$i" -d "$d" -H $h -E "$e" --debug # || continue

    xml="$e/$e.xml"
    scxmldump -d "$d" -E $e --with-picks --with-amplitudes --with-focal-mechanisms --with-magnitudes --all-magnitudes --formatted --output "$xml"

    scbulletin -3 -d "$d" -E "$e" > "$e"/bulletin || continue
done
