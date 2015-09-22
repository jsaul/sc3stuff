import sys, seiscomp3.Core, seiscomp3.Client

class WaveformApp(seiscomp3.Client.StreamApplication):
    def __init__(self, argc, argv):
        seiscomp3.Client.StreamApplication.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(False, False)
        self.setLoggingToStdErr(True)

    def init(self):
        if not seiscomp3.Client.StreamApplication.init(self):
            return False
        now = seiscomp3.Core.Time.GMT()
        t1 = now + seiscomp3.Core.TimeSpan(-1800)
        t2 = now
        stream = self.recordStream()
        stream.addStream("GE", "UGM",  "", "BHZ", t1, t2)
        stream.addStream("GE", "KARP", "", "BHZ", t1, t2)
        stream.addStream("GE", "GHAJ", "", "BHZ", t1, t2)
        return True

    def handleRecord(self, rec):
        print rec.stationCode(), rec.startTime()
        return True

app = WaveformApp(len(sys.argv), sys.argv)
app()
