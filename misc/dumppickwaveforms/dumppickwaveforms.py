############################################################################
#                                                                          #
#    Copyright (C) 2009 by GFZ Potsdam                                     #
#                                                                          #
#    author: Joachim Saul                                                  #
#    email:  saul@gfz-potsdam.de                                           #
#                                                                          #
############################################################################

import sys, os, glob, traceback
import seiscomp3.Core, seiscomp3.Client, seiscomp3.IO

beforeP = afterP = 360

def usage(exitcode=0):
    sys.exit(exitcode)


class EventLoaderApp(seiscomp3.Client.Application):

    def __init__(self, argc, argv):
        seiscomp3.Client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, True)
        self.setLoggingToStdErr(True)
        self.setDaemonEnabled(False)
        self.setRecordStreamEnabled(False)

    def createCommandLineDescription(self):
        try:
            try:
                self.commandline().addGroup("Dump")
                self.commandline().addStringOption("Dump", "event,E", "ID of event to dump")
            except:
                seiscomp3.Logging.warning("caught unexpected error %s" % sys.exc_info())
            return True
        except:
            info = traceback.format_exception(*sys.exc_info())
            for i in info: sys.stderr.write(i)
            sys.exit(-1)

    def validateParameters(self):
        try:
            if seiscomp3.Client.Application.validateParameters(self) == False:
                return False
            if not self.commandline().hasOption("event"):
                sys.stderr.write("event ID must be specified")
                return False
            return True
        except:
            info = traceback.format_exception(*sys.exc_info())
            for i in info: sys.stderr.write(i)
            sys.exit(-1)

    def loadEvent(self, eventID):
        # load event and preferred origin
        evt = self.query().loadObject(seiscomp3.DataModel.Event.TypeInfo(), eventID)
        evt = seiscomp3.DataModel.Event.Cast(evt)
        if evt is None:
            seiscomp3.Logging.error("unknown event '%s'" % eventID)
            return
        self.evt = evt
        return evt

    def loadPreferredOrigin(self, eventID):
        originID = self.evt.preferredOriginID()
        org = self.query().loadObject(seiscomp3.DataModel.Origin.TypeInfo(), originID)
        org = seiscomp3.DataModel.Origin.Cast(org)
        if not org:
            seiscomp3.Logging.error("origin '%s' not loaded" % originID)
            return
        return org

    def loadPicks(self, org):
        # load picks for origin
        orid = org.publicID()
        pick = {}
        for obj in self.query().getPicks(orid):
            p = seiscomp3.DataModel.Pick.Cast(obj)
            key = p.publicID()
            pick[key] = p
        return pick

    def loadAmplitudes(self, org):
        # load amplitudes for origin
        orid = org.publicID()
        ampl = {}
        for obj in self.query().getAmplitudesForOrigin(orid):
            amp = seiscomp3.DataModel.Amplitude.Cast(obj)
            key = amp.publicID()
            ampl[key] = amp
        return ampl

    def loadAll(self, eventID):
        evt = self.loadEvent(eventID)
        if not evt:
            return
        self.evt = evt

        org = self.loadPreferredOrigin(eventID)
        if not org:
            return
        self.org = org

        pick = self.loadPicks(self.org)
        if not pick:
            return
        self.pick = pick

        ampl = self.loadAmplitudes(self.org)
        if not ampl:
            return
        self.ampl = ampl

        return evt, org, pick, ampl


def RecordIterator(stream):
        count = 0
        inp = seiscomp3.IO.RecordInput(stream, seiscomp3.Core.Array.INT, seiscomp3.Core.Record.SAVE_RAW)
        while 1:
            try:
                rec = inp.next()
            except Exception, exc:
                sys.stderr.write("ERROR: " + str(exc) + "\n")
                rec = None

            if not rec:
                break
            count += 1
            sys.stderr.write("%-20s %6d\r" % (rec.streamID(), count))
            yield rec


class RecordDumperApp(EventLoaderApp):

    def __init__(self, argc, argv):
        EventLoaderApp.__init__(self, argc, argv)
        self.setRecordStreamEnabled(True)

    def _getDistancesArrivalsSorted(self, org):
        # sort arrival list by distance
        dist_arr = []
        for i in xrange(org.arrivalCount()):
            arr = org.arrival(i)
            if arr.weight() < 0.1:
                continue
            pha = arr.phase().code()
            if pha not in ["P","Pn","Pg","Pb","Pdiff","PKP"]:
                continue
            dist_arr.append((arr.distance(), arr))
        dist_arr.sort()
        return dist_arr

    def _dumpWaveform(self, evt, org):
        waveform_windows = []
        expected_filenames = []
        for dist, arr in self.dist_arr:
            p = seiscomp3.DataModel.Pick.Find(arr.pickID())
            if p is None:
                continue
            wfid = p.waveformID()
            net = wfid.networkCode()
            sta = wfid.stationCode()
            loc = wfid.locationCode()
            cha = wfid.channelCode()

            # Sometimes manual picks produced by scolv have only
            # "BH" etc. as channel code. IIRC this is to accomodate
            # 3-component picks where "BHZ" etc. would be misleading.
            # But here it doesn't matter for the data request.
            if len(cha) == 2:
                cha = cha+"Z"
            t0 = p.time().value()
            t1, t2 = t0 + seiscomp3.Core.TimeSpan(-beforeP), t0 + seiscomp3.Core.TimeSpan(afterP)
            waveform_windows.append( (t1, t2, net, sta, loc, cha) )
            expected_filenames.append("%s/%s.%s.%s.%s.mseed" % (evt.publicID(), net, sta, loc, cha))

        # request waveforms and dump them to one file per stream
        data = {}
        stream = seiscomp3.IO.RecordStream.Open(self.recordStreamURL())
        stream.setTimeout(300)
        for t1, t2, net, sta, loc, cha in waveform_windows:
            for c in "ZNE12":
                stream.addStream(net, sta, loc, cha[:2]+c, t1, t2)
        for rec in RecordIterator(stream):
            if not rec.streamID() in data:
                data[rec.streamID()] = ""

            # append binary (raw) MiniSEED record to data string
            data[rec.streamID()] += rec.raw().str()
        count = 0
        for key in data:
            count += len(data[key])/512
        sys.stderr.write("Read %d records for %d streams\n" % (count, len(data.keys())))

        for streamID in data:
            file(evt.publicID()+"/"+streamID+".mseed", "w").write(data[streamID])

        # check for missing files (data we requested but which is missing)
        missing_filenames = []
        found_filenames = glob.glob("%s/*.*.*.*.mseed" % evt.publicID())
        for filename in expected_filenames:
            if filename not in found_filenames:
                missing_filenames.append(filename)
        mffilename = evt.publicID()+"/missing-files"
        if os.path.exists(mffilename):
            os.unlink(mffilename)
        if missing_filenames:
            missing_filenames.sort()
            file(mffilename,"w").write("\n".join(missing_filenames))

    def _dumpPickList(self, evt, org, filename="picks"):
        ampl = self.loadAmplitudes(org)
        mags = {}
        nmag = org.stationMagnitudeCount()
        for i in xrange(nmag):
            mag = org.stationMagnitude(i)
            typ = mag.type()
            if typ == "MLv": typ = "ML"
            if typ not in mags:
                mags[typ] = {}

            sta = mag.waveformID().stationCode()
            mags[typ][sta] = mag

        pick_lines = []
        for dist, arr in self.dist_arr:
            p = seiscomp3.DataModel.Pick.Find(arr.pickID())
            if p is None:
                continue

            snr = 0.
            for key in ampl:
                amp = ampl[key]
                if amp.type() != "snr":
                    continue
                if amp.pickID() == arr.pickID():
                    snr = amp.amplitude().value()

            wfid = p.waveformID()
            net = wfid.networkCode()
            sta = wfid.stationCode()
            loc = wfid.locationCode()
            cha = wfid.channelCode()

            t0 = p.time().value()

            pst = "A"
            if p.evaluationMode() != seiscomp3.DataModel.AUTOMATIC:
                pst = "M"
            amp = per = 0.
            for typ in ["mb","ML","mB"]:
                try:
                    m = mags[typ][sta]
                    if typ=="mb":
                        ampid = m.amplitudeID()
                        a = seiscomp3.DataModel.Amplitude.Find(ampid)
                        if a is None:
                            obj = self.query().loadObject(seiscomp3.DataModel.Amplitude.TypeInfo(), ampid)
                            a   = seiscomp3.DataModel.Amplitude.Cast(obj)
                        if a:
                            per = a.period().value()
                            amp = a.amplitude().value()
                except KeyError:
                    pass

            line = "%s %-2s %-6s %-3s %-2s %6.1f %10.3f %4.1f %1s %-6s %s" \
                % (t0.toString("%Y-%m-%d %H:%M:%S.%f000000")[:22], net, sta, cha, [loc,"__"][loc==""], snr, amp, per, pst, arr.phase().code(), p.publicID())
            pick_lines.append(((dist,t0), line))

        # dump the pick lines to one single file
        pick_lines.sort()
        file(evt.publicID()+"/"+filename, "w").write("%s\n" % "\n".join([ line for x,line in pick_lines ]))

    def dumpEvent(self, eventID):
        evt, org, pick, ampl = self.loadAll(eventID)

        # create event directory
        try:
            os.mkdir(self.evt.publicID())
        except OSError:
            pass # we interpret this as already existing event directory
        
        self.dist_arr = self._getDistancesArrivalsSorted(org)
        seiscomp3.Logging.info("dumping waveforms for preferred origin '%s'" % org.publicID())
        self._dumpWaveform(evt, org)
        seiscomp3.Logging.info("dumping waveforms for preferred origin '%s' FINISHED" % org.publicID())
        seiscomp3.Logging.info("dumping picks for preferred origin '%s'" % org.publicID())
        self._dumpPickList(evt, org)
        seiscomp3.Logging.info("dumping picks for preferred origin '%s' FINISHED" % org.publicID())

        #################################################################
        ### If you don't want to dump the picks for the largest automatic
        ### origin, then uncomment this:
        # return # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        #################################################################

        # find largest automatic origin

        # loop over all origins
        origins = [ org for org in self.query().getOrigins(eventID) ]
        # This DB query must be finished before we start iterating over the origins
        # as otherwise we get netsted queries, which are not allowed.

        if len(origins) > 0:
            sorted = []
            for org in origins:
                # there should be a cleaner way...
                org = seiscomp3.DataModel.Origin.Cast(org)
                if not org: continue
                org = self.query().loadObject(seiscomp3.DataModel.Origin.TypeInfo(), org.publicID())
                if not org: continue
                org = seiscomp3.DataModel.Origin.Cast(org)
                if not org: continue
                try:
                    if org.evaluationMode() != seiscomp3.DataModel.AUTOMATIC:
                        continue
                except:
                    continue
                sorted.append( (org.arrivalCount(), org) )
            if len(sorted) > 0:
                # get origin with largest arrival count
                sorted.sort()
                arrivalCount, org = sorted[-1]
                seiscomp3.Logging.info("dumping picks for automatic origin '%s'" % org.publicID())
                # we need to load arrivals and picks for that origin as well
                self.dist_arr = self._getDistancesArrivalsSorted(org)
                pick = self.loadPicks(org)
                self._dumpPickList(evt, org, filename="picks-automatic")

    def run(self):
        try:
            try:
                eventID = self.commandline().optionString("event")
            except:
                sys.stderr.write("You must specify event id\n")
                return False

            self.dumpEvent(eventID)
            return True

        except:
            info = traceback.format_exception(*sys.exc_info())
            for i in info: sys.stderr.write(i)
            sys.exit(-1)

def main():
    app = RecordDumperApp(len(sys.argv), sys.argv)
    app()

if __name__ == "__main__":
    main()
