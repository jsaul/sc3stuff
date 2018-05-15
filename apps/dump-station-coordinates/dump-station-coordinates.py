#!/usr/bin/env python

from __future__ import print_function
import traceback, sys, seiscomp3.Client, seiscomp3.DataModel
from sc3stuff.inventory import InventoryIterator

class InvApp(seiscomp3.Client.Application):
    def __init__(self, argc, argv):
        argv = [ bytes(a.encode()) for a in argv ]
        seiscomp3.Client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, True)
        self.setLoggingToStdErr(True)
        self.setLoadInventoryEnabled(True)

    def run(self):
        now = seiscomp3.Core.Time.GMT()
        lines = []
        try:
            coord = {}
            inv = seiscomp3.Client.Inventory.Instance().inventory()

            for (network, station, location, stream) in InventoryIterator(inv, now):
                n,s,l,c = network.code(), station.code(), location.code(), stream.code()
                if (n,s) in coord:
                    continue

                coord[n,s] = (station.latitude(), station.longitude(), station.elevation())

            for (n,s) in coord:
                lat,lon,elev = coord[n,s]
                lines.append("%-2s %-5s %8.4f %9.4f %4.0f" % (n,s,lat,lon,elev))
        except:
            info = traceback.format_exception(*sys.exc_info())
            for i in info: sys.stderr.write(i)
            sys.exit(-1)

        lines.sort()
        for line in lines:
            print(line)
        return True

def main():
    app = InvApp(len(sys.argv), sys.argv)
    app()

if __name__ == "__main__":
    main()

