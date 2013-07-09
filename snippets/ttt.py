#!/usr/bin/env python

# This is just a little example to illustrate the computation
# of teleseismic traveltimes for the iasp91 velocity model in SC3.

from seiscomp3.Seismology import TravelTimeTable

# uses the iasp91 tables
ttt = TravelTimeTable()

# event coordinates, depth is kilometers
lat1, lon1, dep1 = 40,20,10

# station coordinates, altitude is meters
lat2, lon2, alt2 = 52,13,0

# get a list of phases with associated traveltimes
ttlist = ttt.compute(lat1, lon1, dep1, lat2, lon2, alt2)

# iterate over traveltimes and do something with it
for tt in ttlist:
    print tt.phase, tt.time


