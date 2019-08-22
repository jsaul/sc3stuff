#!/usr/bin/env python

import sys, seiscomp.client, seiscomp.core
from sc3stuff.inventory import InventoryIterator

class InvApp(seiscomp.client.Application):
    def __init__(self, argc, argv):
        argv = [ bytes(a.encode()) for a in argv ]
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, True)
        self.setLoggingToStdErr(True)
        self.setLoadInventoryEnabled(True)

    def run(self):
        now = seiscomp.core.Time.GMT()
        lines = []
        coord = {}
        inv = seiscomp.client.Inventory.Instance().inventory()

        for (network, station, location, stream) in InventoryIterator(inv, now):
            n,s,l,c = network.code(), station.code(), location.code(), stream.code()
            if (n,s) in coord:
                continue

            coord[n,s] = (station.latitude(), station.longitude(), station.elevation())

        for (n,s) in coord:
            lat,lon,elev = coord[n,s]
            lines.append("%-2s %-5s %8.4f %9.4f %4.0f" % (n,s,lat,lon,elev))

        lines.sort()
        for line in lines:
            print(line)
        return True

def main():
    app = InvApp(len(sys.argv), sys.argv)
    app()

if __name__ == "__main__":
    main()

