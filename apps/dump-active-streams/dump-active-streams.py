#!/usr/bin/env python

from __future__ import print_function
import traceback, sys
import seiscomp3.Client, seiscomp3.DataModel
from sc3stuff.inventory import InventoryIterator


class InvApp(seiscomp3.Client.Application):
    def __init__(self, argc, argv):
        seiscomp3.Client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, True)
        self.setLoggingToStdErr(True)
#       self.setLoadInventoryEnabled(True)
        self.setLoadConfigModuleEnabled(True)

    def run(self):
        now = seiscomp3.Core.Time.GMT()
        lines = []
        try:
            mod = self.configModule()
            for i in xrange(mod.configStationCount()):
                cfg = mod.configStation(i)
                setup = seiscomp3.DataModel.findSetup(cfg, self.name(), True)
                if not setup: continue

                params = seiscomp3.DataModel.ParameterSet.Find(setup.parameterSetID())
                if not params: continue

                detecStream = None
                detecLocid = ""

                for k in xrange(params.parameterCount()):
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

