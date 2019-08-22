from __future__ import print_function
import sys, os, errno, gc, hashlib, logging, logging.handlers
import seiscomp.client, seiscomp.datamodel, seiscomp.io, seiscomp.logging
from io import BytesIO

def objectToXML(obj, expName = "trunk"):
    # based on code contributed by Stephan Herrnkind

    class Sink(seiscomp.io.ExportSink):

        def __init__(self, buf):
            seiscomp.io.ExportSink.__init__(self)
            self.buf = buf
            self.written = 0

        def write(self, data, size):
            self.buf.write(data[:size])
            self.written += size
            return size

    if not obj:
        seiscomp.logging.error("could not serialize NULL object")
        return None

    exp = seiscomp.io.Exporter.Create(expName)
    if not exp:
        seiscomp.logging.error("exporter '%s' not found" % expName)
        return None
    exp.setFormattedOutput(True)

    try:
        io = BytesIO()
        sink = Sink(io)
        exp.write(sink, obj)
        return io.getvalue().strip()
    except Exception as err:
        seiscomp.logging.error(str(err))

    return None


class MyLogHandler(logging.handlers.TimedRotatingFileHandler):

    def __init__(self, filename, **kwargs):
        logging.handlers.TimedRotatingFileHandler.__init__(self, filename, **kwargs)
        self.suffix = "%Y-%m-%dT%H:%M:%SZ"
        self.utc = True

    def doRollover(self):
        logging.handlers.TimedRotatingFileHandler.doRollover(self)
        os.system("gzip '" + self.baseFilename + "'.*-*-*T*:*:*Z &")


class NotifierLogger(seiscomp.client.Application):

    def __init__(self, argc, argv):
        argv = [ bytes(a.encode()) for a in argv ]
        seiscomp.client.Application.__init__(self, argc, argv)
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
        seiscomp.datamodel.PublicObject.SetRegistrationEnabled(False) 
        self._logger = logging.getLogger("Rotating Log")
        self._logger.setLevel(logging.INFO)

    def createCommandLineDescription(self):
        self.commandline().addGroup("Output")
        self.commandline().addStringOption("Output", "prefix", "path/file prefix to generate output file names")
        return True

    def validateParameters(self):
        if not seiscomp.client.Application.validateParameters(self):
            return False
        try:
            self._prefix = self.commandline().optionString("prefix")
        except:
            self._prefix = "notifier-log"
        handler = MyLogHandler(self._prefix, when="h", interval=1, backupCount=48)
        self._logger.addHandler(handler)
        return True

    def _writeNotifier(self, xml):
        now = seiscomp.core.Time.GMT().toString("%Y-%m-%dT%H:%M:%S.%f000000")[:26]+"Z"
#       self._logger.info("####  %s  %s  %d bytes" % (now, hashlib.md5(xml).encode('utf-8').hexdigest(), len(xml)))
        self._logger.info("####  %s  %s  %d bytes" % (now, hashlib.md5(xml).hexdigest(), len(xml)))
        self._logger.info(xml)
        gc.collect()

    def handleMessage(self, msg):
        nmsg = seiscomp.datamodel.NotifierMessage.Cast(msg)
        if nmsg:
            xml = objectToXML(nmsg)
            if xml:
                self._writeNotifier(xml)
#       seiscomp.client.Application.handleMessage(self, msg)


if __name__ == "__main__":
    app = NotifierLogger(len(sys.argv), sys.argv)
    sys.exit(app())
