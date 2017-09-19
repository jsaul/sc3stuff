import sys, os, logging, logging.handlers, StringIO
import seiscomp3.Client, seiscomp3.DataModel, seiscomp3.IO, seiscomp3.Logging


def objectToXML(obj, expName = "trunk"):
    # based on code contributed by Stephan Herrnkind

    class Sink(seiscomp3.IO.ExportSink):

        def __init__(self, buf):
            seiscomp3.IO.ExportSink.__init__(self)
            self.buf = buf
            self.written = 0

        def write(self, data, size):
            self.buf.write(data[:size])
            self.written += size
            return size

    if not obj:
        seiscomp3.Logging.error("could not serialize NULL object")
        return None

    exp = seiscomp3.IO.Exporter.Create(expName)
    if not exp:
        seiscomp3.Logging.error("exporter '%s' not found" % expName)
        return None
    exp.setFormattedOutput(True)

    try:
        io = StringIO.StringIO()
        sink = Sink(io)
        exp.write(sink, obj)
        return io.getvalue().strip()
    except Exception, e:
        seiscomp3.Logging.error(error + str(e))

    return None


class MyLogHandler(logging.handlers.TimedRotatingFileHandler):

    def __init__(self, filename, **kwargs):
        super(MyLogHandler, self).__init__(filename, **kwargs)
        self.suffix = "%Y-%m-%dT%H:%M:%SZ"
        self.utc = True

    def doRollover(self):
        super(MyLogHandler, self).doRollover()
        os.system("gzip '" + self.baseFilename + "'.*-*-*T*:*:*Z &")


class NotifierLogger(seiscomp3.Client.Application):

    def __init__(self, argc, argv):
        seiscomp3.Client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(True)
        self.addMessagingSubscription("PICK")
        self.addMessagingSubscription("AMPLITUDE")
        self.addMessagingSubscription("MAGNITUDE")
        self.addMessagingSubscription("LOCATION")
        self.addMessagingSubscription("FOCMECH")
        self.addMessagingSubscription("EVENT")
        # do nothing with the notifiers except logging
        self.setAutoApplyNotifierEnabled(False)
        self.setInterpretNotifierEnabled(False)
        self._logger = logging.getLogger("Rotating Log")
        self._logger.setLevel(logging.INFO)
        handler = MyLogHandler("notifier-log", when="h", interval=1, backupCount=48)
        self._logger.addHandler(handler)

    def _writeNotifier(self, xml):
        now = seiscomp3.Core.Time.GMT().toString("%Y-%m-%dT%H:%M:%S.%f000000")[:26]+"Z"
        xml = xml+"\n"
        self._logger.info("####  %s  %d bytes\n" % (now, len(xml)))
        self._logger.info(xml)

    def handleMessage(self, msg):
        nmsg = seiscomp3.DataModel.NotifierMessage.Cast(msg)
        if nmsg:
            xml = objectToXML(nmsg)
            if xml:
                self._writeNotifier(xml)
        seiscomp3.Client.Application.handleMessage(self, msg)


if __name__ == "__main__":
    app = NotifierLogger(len(sys.argv), sys.argv)
    sys.exit(app())
