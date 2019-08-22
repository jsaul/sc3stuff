from __future__ import print_function
import sys, seiscomp.core, seiscomp.client

class WaveformApp(seiscomp.client.StreamApplication):
    def __init__(self, argc, argv):
        seiscomp.client.StreamApplication.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(False, False)
        self.setLoggingToStdErr(True)

    def init(self):
        if not seiscomp.client.StreamApplication.init(self):
            return False
        now = seiscomp.core.Time.GMT()
        t1 = now + seiscomp.core.TimeSpan(-600)
        t2 = now
        stream = self.recordStream()
        stream.addStream("GE", "KARP", "",   "BHZ", t1, t2)
        stream.addStream("GE", "GHAJ", "",   "BHZ", t1, t2)
        stream.addStream("IU", "ANTO", "10", "BHZ", t1, t2)
        return True

    def handleRecord(self, rec):
        print(rec.stationCode(), rec.startTime())
        return True

app = WaveformApp(len(sys.argv), sys.argv)
app()
