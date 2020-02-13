import sys, os
import seiscomp.core, seiscomp.client, seiscomp.datamodel, seiscomp.io, seiscomp.logging, seiscomp.utils

class NotifierPlayer(seiscomp.client.Application):

    def __init__(self, argc, argv):
        argv = [ bytes(a.encode()) for a in argv ]
        super(NotifierPlayer, self).__init__(argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(False, False)
        self._startTime = self._endTime = None
        self.xmlInputFileName = None
        self._time = None
#       self.speed = 1

    def createCommandLineDescription(self):
        super(NotifierPlayer, self).createCommandLineDescription()
        self.commandline().addGroup("Play")
        self.commandline().addStringOption("Play", "begin", "specify start of time window")
        self.commandline().addStringOption("Play", "end", "specify end of time window")
#       self.commandline().addStringOption("Play", "speed", "specify speed factor")
        self.commandline().addGroup("Input")
        self.commandline().addStringOption("Input", "xml-file", "specify xml file")

    def init(self):
        if not super(NotifierPlayer, self).init():
            return False

        try:    start = self.commandline().optionString("begin")
        except: start = None

        try:    end = self.commandline().optionString("end")
        except: end = None

        try:    self.xmlInputFileName = self.commandline().optionString("xml-file")
        except: pass

#       try:
#           self.speed = self.commandline().optionString("speed")
#           if self.speed == "0":
#               self.speed = None
#           else:
#               self.speed = float(self.speed)
#       except: self.speed = 1

        if start:
            self._startTime = seiscomp.core.Time.GMT()
            if self._startTime.fromString(start, "%FT%TZ") == False:
                seiscomp.logging.error("Wrong 'begin' format")
                return False
        if end:
            self._endTime = Core.Time.GMT()
            if self._endTime.fromString(end, "%FT%TZ") == False:
                seiscomp.logging.error("Wrong 'end' format")
                return False
        return True

    def _readNotifierMessageFromXML(self, xml):
        b = seiscomp.utils.stringToStreambuf(xml)
        ar = seiscomp.io.XMLArchive(b)
        obj = ar.readObject()
        if obj is None:
            raise TypeError("got invalid xml")
        nmsg = seiscomp.datamodel.NotifierMessage.Cast(obj)
        if nmsg is None:
            raise TypeError(self.xmlInputFile + ": no NotifierMessage object found")
        return nmsg

    def run(self):
        if not self.xmlInputFileName:
            return False

        seiscomp.logging.debug("input file is %s" % self.xmlInputFileName)
        f = open(self.xmlInputFileName)

        while True:
            while True:
                line = f.readline()
                if not line:
                    # empty input
                    return True
                line = line.strip()
                if not line:
                    # blank line
                    continue
                if line[0] == "#":
                    break

            if len(line.split()) == 3:
                sharp, timestamp, nbytes = line.split()
            elif len(line.split()) == 4:
                sharp, timestamp, nbytes, sbytes = line.split()
                assert sbytes == "bytes"
            elif len(line.split()) == 5:
                sharp, timestamp, md5hash, nbytes, sbytes = line.split()
                assert sbytes == "bytes"
            else:
                return False
            assert sharp[0] == "#"
            time = seiscomp.core.Time.GMT()
            time.fromString(timestamp, "%FT%T.%fZ")

            if self._startTime is not None and time < self._startTime:
                continue
            if self._endTime is not None and time > self._endTime:
                break

            nbytes = int(nbytes)
            assert sharp[0] == "#"
            xml = f.read(nbytes)

            nmsg = self._readNotifierMessageFromXML(xml.strip())
            self.sync(time)

            # We either extract and handle all Notifier objects individually
            for item in nmsg:
                n = seiscomp.datamodel.Notifier.Cast(item)
                assert n is not None
                n.apply()
                self.handleNotifier(n)
            # OR simply handle the NotifierMessage
#           self.handleMessage(nmsg)

        return True

    def sync(self, time):
        self._time = time
        seiscomp.logging.debug("sync time=%s" % time.toString("%FT%T.%fZ"))

    def addObject(self, parent, obj):
        # in a usable player, this must be reimplemented
        seiscomp.logging.debug("addObject class=%s parent=%s" % (obj.className(),parent))

    def updateObject(self, parent, obj):
        # in a usable player, this must be reimplemented
        seiscomp.logging.debug("updateObject class=%s parent=%s" % (obj.className(),parent))

app = NotifierPlayer(len(sys.argv), sys.argv)
sys.exit(app())
