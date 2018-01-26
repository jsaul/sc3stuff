from __future__ import print_function
import sys, traceback, seiscomp3.Client, seiscomp3.DataModel, seiscomp3.IO, seiscomp3.Logging
import StringIO


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

    error = "could not serialize object: "
    if not obj:
        seiscomp3.Logging.error(error + "NULL")
        return None

    exp = seiscomp3.IO.Exporter.Create(expName)
    exp.setFormattedOutput(True)
    if not exp:
        seiscomp3.Logging.error(error + "exporter '%s' not found" % expName)
        return None

    try:
        io = StringIO.StringIO()
        sink = Sink(io)
        exp.write(sink, obj)
        return io.getvalue().strip()
    except Exception, e:
        seiscomp3.Logging.error(error + str(e))

    return None


class MessagingClient(seiscomp3.Client.Application):

    def __init__(self, argc, argv):
        seiscomp3.Client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(True)
        self.addMessagingSubscription("PICK")
        self.addMessagingSubscription("AMPLITUDE")
        self.addMessagingSubscription("MAGNITUDE")
        self.addMessagingSubscription("LOCATION")
        self.addMessagingSubscription("EVENT")

#       seiscomp3.Client.Application.setInterpretNotifierEnabled(self, True)

    def handleMessage(self, msg):
        
        now = seiscomp3.Core.Time.GMT().toString("%Y-%m-%dT%H:%M:%S.%f000000")[:26]+"Z"
        nm = seiscomp3.DataModel.NotifierMessage.Cast(msg)
        if nm:
            xml = objectToXML(nm)
            if xml:
                print("#### %d %s" % (len(xml), now))
                print(xml)
        seiscomp3.Client.Application.handleMessage(self, msg)


if __name__ == "__main__":
    app = MessagingClient(len(sys.argv), sys.argv)
    sys.exit(app())
