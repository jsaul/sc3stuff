#!/usr/bin/env python

# This is just a test script for fep files. Get an example fep file
# from the USGS:
#
# mkdir ~/.seiscomp3/fep
# fep="switz_liecht.fep"
# wget -O ~/.seiscomp3/fep/$fep ftp://hazards.cr.usgs.gov/feregion/feplus/fepfiles/$fep

from __future__ import print_function
import sys
import seiscomp.client, seiscomp.seismology

class RegionApp(seiscomp.client.Application):

    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(False, False)
        self.setDaemonEnabled(False)
        self.setLoggingToStdErr(True)
        self.setLoadRegionsEnabled(True)

    def run(self):
        lat, lon = 47.16, 9.54
        reg = seiscomp.seismology.Regions()
        reg = reg.getRegionName(lat, lon)
        print(lat, lon, reg)

app = RegionApp(len(sys.argv), sys.argv)
app()
