import sys, os, gc, hashlib, logging, logging.handlers
import seiscomp3.Client, seiscomp3.DataModel, seiscomp3.IO, seiscomp3.Logging

try:
    # Python >= 2.6
    from io import BytesIO as StringIO
except:
    # Python < 2.6
    from StringIO import StringIO


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
        io = StringIO()
        sink = Sink(io)
        exp.write(sink, obj)
        return io.getvalue().strip()
    except Exception as err:
        seiscomp3.Logging.error(str(err))

    return None


class MyLogHandler(logging.handlers.TimedRotatingFileHandler):

    def __init__(self, filename, **kwargs):
        logging.handlers.TimedRotatingFileHandler.__init__(self, filename, **kwargs)
        self.suffix = "%Y-%m-%dT%H:%M:%SZ"
        self.utc = True

    def doRollover(self):
        logging.handlers.TimedRotatingFileHandler.doRollover(self)
        os.system("gzip '" + self.baseFilename + "'.*-*-*T*:*:*Z &")


class NotifierLogger(seiscomp3.Client.Application):

    def __init__(self, argc, argv):
        argv = [ bytes(a.encode()) for a in argv ]
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
        seiscomp3.DataModel.PublicObject.SetRegistrationEnabled(False) 
        self._logger = logging.getLogger("Rotating Log")
        self._logger.setLevel(logging.INFO)
        # FIXME: clean up:
        self._directory = "/home/saul/log/notifiers"
        handler = MyLogHandler(self._directory+"/"+"notifier-log", when="h", interval=1, backupCount=48)
        self._logger.addHandler(handler)

    def _writeNotifier(self, xml):
        now = seiscomp3.Core.Time.GMT().toString("%Y-%m-%dT%H:%M:%S.%f000000")[:26]+"Z"
#       self._logger.info("####  %s  %s  %d bytes" % (now, hashlib.md5(xml).encode('utf-8').hexdigest(), len(xml)))
        self._logger.info("####  %s  %s  %d bytes" % (now, hashlib.md5(xml).hexdigest(), len(xml)))
        self._logger.info(xml)
        gc.collect()

    def handleMessage(self, msg):
        nmsg = seiscomp3.DataModel.NotifierMessage.Cast(msg)
        if nmsg:
            xml = objectToXML(nmsg)
            if xml:
                self._writeNotifier(xml)
#       seiscomp3.Client.Application.handleMessage(self, msg)


if __name__ == "__main__":
    app = NotifierLogger(len(sys.argv), sys.argv)
    sys.exit(app())
