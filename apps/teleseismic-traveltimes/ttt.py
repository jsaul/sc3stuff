#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import seiscomp3.Seismology

# uses the iasp91 tables by default
ttt = seiscomp3.Seismology.TravelTimeTable()

# iasp91 and ak135 are the only supported models
ttt.setModel("ak135")

def computeTravelTimes(delta, depth):
    arrivals = ttt.compute(0, 0, depth, 0, delta, 0, 0)
    return arrivals

delta = float(sys.argv[1])
depth = float(sys.argv[2])

arrivals = computeTravelTimes(delta, depth)

for arr in arrivals:
    print("%-10s %8.3f %10.6f %10.6f %10.6f" % (arr.phase, arr.time, arr.dtdd, arr.dtdh, arr.dddp))
