#!/usr/bin/env python

from __future__ import print_function
import traceback, sys, seiscomp.core, seiscomp.client
from sc3stuff.inventory import InventoryIterator

class InvApp(seiscomp.client.Application):
    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, True)
        self.setLoggingToStdErr(True)
        self.setLoadInventoryEnabled(True)

    def run(self):
        now = seiscomp.core.Time.GMT()
        lines = []
        inv = seiscomp.client.Inventory.Instance().inventory()

        for network, station, location, stream in InventoryIterator(inv, now):
            n,s,l,c = network.code(), station.code(), location.code(), stream.code()
            if l.strip() == "": l="--" # for readability
            line = "%-2s %-5s %-2s %-3s %g" % (n,s,l,c, stream.gain())
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

