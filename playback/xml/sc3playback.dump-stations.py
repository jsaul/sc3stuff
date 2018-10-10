#!/usr/bin/env python

from __future__ import print_function
import sys, seiscomp3.Client, seiscomp3.DataModel

def str2time(s):
    t = seiscomp3.Core.Time.GMT()
    if t.fromString(s, "%F %T"):
        return t
    if t.fromString(s, "%FT%TZ"):
        return t
    if t.fromString(s, "%FT%T"):
        return t

class InvApp(seiscomp3.Client.Application):
    def __init__(self, argc, argv):
        seiscomp3.Client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, True)
        self.setLoggingToStdErr(True)
        self.referenceTime = seiscomp3.Core.Time.GMT()

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
            seiscomp3.Logging.debug("Reference time is %s" % self.referenceTime.toString("%FT%TZ"))

        lines = []
        dbr = seiscomp3.DataModel.DatabaseReader(self.database())
        inv = seiscomp3.DataModel.Inventory()
        dbr.loadNetworks(inv) 
        nnet = inv.networkCount()
        for inet in xrange(nnet):
            net = inv.network(inet)
            dbr.load(net);
            nsta = net.stationCount()
            for ista in xrange(nsta):
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

