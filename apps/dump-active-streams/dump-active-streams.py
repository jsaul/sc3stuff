#!/usr/bin/env python

from __future__ import print_function
import sys
import seiscomp.client, seiscomp.core, seiscomp.datamodel
from sc3stuff.inventory import InventoryIterator


class InvApp(seiscomp.client.Application):
    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, True)
        self.setLoggingToStdErr(True)
#       self.setLoadInventoryEnabled(True)
        self.setLoadConfigModuleEnabled(True)

    def run(self):
        now = seiscomp.core.Time.GMT()
        lines = []

        mod = self.configModule()
        for i in range(mod.configStationCount()):
            cfg = mod.configStation(i)
            setup = seiscomp.datamodel.findSetup(cfg, self.name(), True)
            if not setup: continue

            params = seiscomp.datamodel.ParameterSet.Find(setup.parameterSetID())
            if not params: continue

            detecStream = None
            detecLocid = ""

            for k in range(params.parameterCount()):
                param = params.parameter(k)
                if param.name() == "detecStream":
                    detecStream = param.value()
                elif param.name() == "detecLocid":
                    detecLocid = param.value()
            if detecLocid == "":
                detecLocid = "--"
            if not detecStream:
                continue

            line = "%s %s %s %s" % (cfg.networkCode(), cfg.stationCode(), detecLocid, detecStream)
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

