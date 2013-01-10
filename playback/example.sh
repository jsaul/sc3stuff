#!/bin/sh

export PATH=$PATH:.

while read evt comment
do
    case "$evt" in
    "#"*) continue;;
    esac
    echo "$evt $comment"

    test -f $evt/objects.xml ||
    make-xml-playback.sh "$evt" "$comment"

    run-xml-playback.sh $evt

done <<EOF
#gfz2012atjr  split PKP event producing fake in Baltics/Belarus/...
#gfz2012befq  pick with large residual of 10.4 s (TW.TPUB) used in location
#gfz2012bdzw  clear negativ trend of residuals with distance but default depth used instead of 80 km
#gfz2012byrq  3 Kermadec events within 2 hrs, each producing a fake in N Pacific
#gfz2012brrg  split PKP event producing fake in Siberia
#gfz2012cvfr  Fiji event too shallow due to one pick @ G.SANVU with much too big residual
#gfz2012fnoj  P.N.G. automatic depth: 10km; real depth: 115km; strange residual pattern; should have been easier to locate correctly
#gfz2012tgbb  Colombia M 7.2 z=163 km but located too shallow at 10 km
#gfz2012ttnf  Fiji M=4.6 z=471; missed but 16 good-enough automatic picks
#gfz2012wcvp  Peru M 6.0 z=113 km but located too shallow at 10 km
gfz2012wxbs  Sumbawa M 5.3; scautoloc died ca. 5 min after OT on proc1 - can we reproduce that?
EOF
