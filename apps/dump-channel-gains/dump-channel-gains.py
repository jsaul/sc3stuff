#!/usr/bin/env python

from __future__ import print_function
import traceback, sys, seiscomp3.Client, seiscomp3.DataModel
from sc3stuff.inventory import InventoryIterator

class InvApp(seiscomp3.Client.Application):
    def __init__(self, argc, argv):
        seiscomp3.Client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, True)
        self.setLoggingToStdErr(True)
        self.setLoadInventoryEnabled(True)

    def run(self):
        now = seiscomp3.Core.Time.GMT()
        try:
            lines = []
            inv = seiscomp3.Client.Inventory.Instance().inventory()

            for network, station, location, stream in InventoryIterator(inv, now):
                n,s,l,c = network.code(), station.code(), location.code(), stream.code()
                if l.strip() == "": l="--" # for readability
                line = "%-2s %-5s %-2s %-3s %g" % (n,s,l,c, stream.gain())
                lines.append(line)
            lines.sort()
            for line in lines:
                print(line)
            return True
        except:
            info = traceback.format_exception(*sys.exc_info())
            for i in info: sys.stderr.write(i)
            sys.exit(-1)

def main():
    app = InvApp(len(sys.argv), sys.argv)
    app()

if __name__ == "__main__":
    main()

