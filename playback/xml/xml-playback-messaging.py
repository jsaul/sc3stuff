import sys, os, time, tempfile
import seiscomp.core, seiscomp.client, seiscomp.datamodel, seiscomp.io, seiscomp.logging

class PickPlayer(seiscomp.client.Application):

    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(True)
        self.setDatabaseEnabled(False, False)
        self.setPrimaryMessagingGroup("PICK")
        self._startTime = self._endTime = None
        self._xmlFile = None
        self._tmpDir = None
        self.speed = 1

    def createCommandLineDescription(self):
        seiscomp.client.Application.createCommandLineDescription(self)
        self.commandline().addGroup("Mode");
        self.commandline().addOption("Mode", "test", "Do not send any object");
        self.commandline().addGroup("Play")
        self.commandline().addStringOption("Play", "begin", "specify start of time window")
        self.commandline().addStringOption("Play", "end", "specify end of time window")
        self.commandline().addStringOption("Play", "speed", "specify speed factor")
        self.commandline().addGroup("Input")
        self.commandline().addStringOption("Input", "xml-file", "specify xml file")
        self.commandline().addStringOption("Input", "tmp-dir", "specify tmp directory (default is /tmp)")

    def validateParameters(self):
        if not self.commandline().hasOption("test"):
            if not self.commandline().hasOption("host"):
                sys.stderr.write("must specify host name on command line!\n")
                return False
        return True

    def init(self):
        if not seiscomp.client.Application.init(self):
            return False

        try:    start = self.commandline().optionString("begin")
        except: start = None

        try:    end = self.commandline().optionString("end")
        except: end = None

        try:    self._xmlFile = self.commandline().optionString("xml-file")
        except: pass

        try:    self._tmpDir = self.commandline().optionString("tmp-dir")
        except: pass

        try:
            self.speed = self.commandline().optionString("speed")
            if self.speed == "0":
                self.speed = None
            else:
                self.speed = float(self.speed)
        except: self.speed = 1

        if start:
            self._startTime = seiscomp.core.Time.GMT()
            if self._startTime.fromString(start, "%F %T") == False:
                sys.stderr.write("Wrong 'begin' format\n")
                return False
        if end:
            self._endTime = seiscomp.core.Time.GMT()
            if self._endTime.fromString(end, "%F %T") == False:
                sys.stderr.write("Wrong 'end' format\n")
                return False

        return True

    def _readEventParametersFromXML(self):
        ar = seiscomp.io.XMLArchive()
        if ar.open(self._xmlFile) == False:
            raise IOError, self._xmlFile + ": unable to open"
        obj = ar.readObject()
        if obj is None:
            raise TypeError, self._xmlFile + ": invalid format"
        ep  = seiscomp.datamodel.EventParameters.Cast(obj)
        if ep is None:
            raise TypeError, self._xmlFile + ": no eventparameters found"
        return ep

    def _runBatchMode(self):
        ep = self._readEventParametersFromXML()

        # collect the objects
        objs = []
        while ep.pickCount() > 0:
            # FIXME: The cast hack forces the SC3 refcounter to be increased.
            pick = seiscomp.datamodel.Pick.Cast(ep.pick(0))
            ep.removePick(0)
            objs.append(pick)
        while ep.amplitudeCount() > 0:
            # FIXME: The cast hack forces the SC3 refcounter to be increased.
            ampl = seiscomp.datamodel.Amplitude.Cast(ep.amplitude(0))
            ep.removeAmplitude(0)
            objs.append(ampl)
        while ep.originCount() > 0:
            # FIXME: The cast hack forces the SC3 refcounter to be increased.
            origin = seiscomp.datamodel.Origin.Cast(ep.origin(0))
            ep.removeOrigin(0)
            objs.append(origin)
        del ep

        # DSU sort all objects by object creation time
        sortlist = []
        for obj in objs:
            # discard objects that have no creationInfo attribute
            try:    t = obj.creationInfo().creationTime()
            except: continue

            if self._startTime is not None and t < self._startTime:
                continue
            if self._endTime is not None and t > self._endTime:
                continue
            sortlist.append( (t,obj) )
        sortlist.sort()

        time_of_1st_object, obj = sortlist[0]
        time_of_playback_start = seiscomp.core.Time.GMT()

        ep = seiscomp.datamodel.EventParameters()
        pickampl = {}

        # go through the sorted list of object and process them sequentially
        for t,obj in sortlist:
            if self.isExitRequested(): return

            if self.speed:
                t = time_of_playback_start + seiscomp.core.TimeSpan(float(t - time_of_1st_object) / self.speed)
                while t > seiscomp.core.Time.GMT():
                    time.sleep(0.1)

            if obj.ClassName() not in [ "Pick", "Amplitude", "Origin" ]:
                continue

            seiscomp.datamodel.Notifier.Enable()
            ep.add(obj)
            msg = seiscomp.datamodel.Notifier.GetMessage()
            if self.commandline().hasOption("test"):
                sys.stderr.write("Test mode - not sending %-10s %s\n" % (obj.ClassName(), obj.publicID()))
            else:
                if self.connection().send(msg):
                    sys.stderr.write("Sent %s %s\n" % (obj.ClassName(), obj.publicID()))
                else:
                    sys.stderr.write("Failed to send %-10s %s\n" % (obj.ClassName(), obj.publicID()))
            seiscomp.datamodel.Notifier.Disable()
            self.sync()

        return True


    def _runStreamMode(self, stream=sys.stdin):

        import xml.dom.pulldom
        events = xml.dom.pulldom.parse(stream, bufsize=100)
        for event in events:
            typ, node = event
            if typ == 'START_ELEMENT' and node.nodeName in ["pick","amplitude","origin"]:
                events.expandNode(node)
                xmlNode = node.toxml()
                ofile = file(self._xmlFile, "w")
                # wrap object into a SC3 XML template
                ofile.write('<?xml version="1.0" encoding="UTF-8"?><seiscomp xmlns="http://geofon.gfz-potsdam.de/ns/seiscomp3-schema/0.7" version="0.7"><EventParameters>%s</EventParameters></seiscomp>\n' % xmlNode)
                ofile.close()
                # in batch mode pick up data in temp file
                self._runBatchMode()
        return True

    def run(self):

        if self._xmlFile:
            seiscomp.logging.debug("running in batch mode")
            seiscomp.logging.debug("input file is %s" % self._xmlFile)
            return self._runBatchMode()

        self._xmlFile = tempfile.mktemp(".xml", dir=self._tmpDir)
        seiscomp.logging.debug("running in stream mode")
        seiscomp.logging.debug("temp file is %s" % self._xmlFile)
        status = self._runStreamMode()
        if os.path.exists(self._xmlFile):
            os.unlink(self._xmlFile)
        return status



app = PickPlayer(len(sys.argv), sys.argv)
sys.exit(app())
