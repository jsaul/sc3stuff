import sys, seiscomp3.Core, seiscomp3.Client

class WaveformApp(seiscomp3.Client.StreamApplication):
    def __init__(self, argc, argv):
        seiscomp3.Client.StreamApplication.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(False, False)
        self.setLoggingToStdErr(True)
        self.setDaemonEnabled(False)
        self.setRecordStreamEnabled(True)

    def init(self):
        if not seiscomp3.Client.StreamApplication.init(self):
            return False
        now = seiscomp3.Core.Time.GMT()
        t1 = now + seiscomp3.Core.TimeSpan(-3600)
        t2 = now + seiscomp3.Core.TimeSpan(-1800)
        stream = self.recordStream()
        stream.addStream("GE","MORC","", "HHZ", t1, t2)
        stream.addStream("GE","KARP","", "HHZ", t1, t2)
        stream.addStream("GE","GHAJ","", "HHZ", t1, t2)
        return True

    def handleRecord(self, rec):
        print rec.stationCode(), rec.startTime()
        return True

app = WaveformApp(len(sys.argv), sys.argv)
app()
