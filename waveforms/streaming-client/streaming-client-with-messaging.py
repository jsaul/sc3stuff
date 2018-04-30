from __future__ import print_function
import sys, seiscomp3.Core, seiscomp3.Client, seiscomp3.DataModel

class WaveformApp(seiscomp3.Client.StreamApplication):
    def __init__(self, argc, argv):
        seiscomp3.Client.StreamApplication.__init__(self, argc, argv)
        self.setMessagingEnabled(True)
        self.addMessagingSubscription("PICK")
        self.setDatabaseEnabled(False, False)
        self.setLoggingToStdErr(True)

    def init(self):
        if not seiscomp3.Client.StreamApplication.init(self):
            return False
        stream = self.recordStream()
        # note: no time windows specified because
        # we want an "infinite" stream here!
        stream.addStream("GE", "KARP", "",   "BHZ")
        stream.addStream("GE", "GHAJ", "",   "BHZ")
        stream.addStream("IU", "ANTO", "10", "BHZ")
        return True

    def handleRecord(self, rec):
        print(rec.stationCode(), rec.startTime())
        return True

    def addObject(self, parentID, obj):
        pick = seiscomp3.DataModel.Pick.Cast(obj)
        if pick:
            print("new pick", pick.publicID())

    def updateObject(self, parentID, obj):
        pick = seiscomp3.DataModel.Pick.Cast(obj)
        if pick:
            print("updated pick", pick.publicID())

app = WaveformApp(len(sys.argv), sys.argv)
app()
