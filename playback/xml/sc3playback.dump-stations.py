#!/usr/bin/env python

from __future__ import print_function
import sys
import seiscomp.core, seiscomp.client, seiscomp.datamodel, seiscomp.logging

def str2time(s):
    t = seiscomp.core.Time.GMT()
    if t.fromString(s, "%F %T"):
        return t
    if t.fromString(s, "%FT%TZ"):
        return t
    if t.fromString(s, "%FT%T"):
        return t

class InvApp(seiscomp.client.Application):
    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, True)
        self.setLoggingToStdErr(True)
        self.referenceTime = seiscomp.core.Time.GMT()

    def createCommandLineDescription(self):
        self.commandline().addGroup("Time")
        self.commandline().addStringOption("Time", "reference-time,t", "reference time for inventory lookup")

    def run(self):
        
        try:
            referenceTime = self.commandline().optionString("reference-time")
        except:
            referenceTime = None
        if referenceTime:
            if self.referenceTime.fromString(referenceTime, "%F %T") == False:
                print("Wrong 'reference-time' format\n", file=sys.stderr)
                return False
            seiscomp.logging.debug("Reference time is %s" % self.referenceTime.toString("%FT%TZ"))

        lines = []
        dbr = seiscomp.datamodel.DatabaseReader(self.database())
        inv = seiscomp.datamodel.Inventory()
        dbr.loadNetworks(inv) 
        nnet = inv.networkCount()
        for inet in range(nnet):
            net = inv.network(inet)
            dbr.load(net);
            nsta = net.stationCount()
            for ista in range(nsta):
                sta = net.station(ista)
                line = "%-2s %-5s %9.4f %9.4f %6.1f" % ( net.code(), sta.code(), sta.latitude(), sta.longitude(), sta.elevation() )
                try:
                    start = sta.start()
                except:
                    continue
                try:
                    end = sta.end()
                except:
                    end = self.referenceTime

                if not start <= self.referenceTime <= end:
                    continue

                lines.append(line)

        lines.sort()
        for line in lines:
            print(line)

        return True

def main():
    app = InvApp(len(sys.argv), sys.argv)
    app()

if __name__ == "__main__":
    main()

