#!/bin/sh

work_d=$HOME/mt-import

#### Don't change anything below ####

script=$work_d/script/mt-import.py

x="$HOME/seiscomp3/bin/seiscomp exec python"

$x $script --event gfz2014rnvo --sdr1 66,47,-72
