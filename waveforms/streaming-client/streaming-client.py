import sys, seiscomp3.Core, seiscomp3.Client

class StreamingApp(seiscomp3.Client.StreamApplication):
    def __init__(self, argc, argv):
        seiscomp3.Client.StreamApplication.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(False, False)
        self.setLoggingToStdErr(True)

    def init(self):
        if not seiscomp3.Client.StreamApplication.init(self):
            return False
        stream = self.recordStream()
        stream.addStream("GE", "UGM",  "", "BHZ")
        stream.addStream("GE", "KARP", "", "BHZ")
        stream.addStream("GE", "GHAJ", "", "BHZ")
        return True

    def handleRecord(self, rec):
        print rec.stationCode(), rec.startTime()
        return True

app = StreamingApp(len(sys.argv), sys.argv)
app()
