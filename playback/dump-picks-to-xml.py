#!/usr/bin/env python

###### configuration #######
# time window relative to
# origin time:
before = 1200.   # 20 min.
after  = 1800.   # 30 min.
############################

import sys, traceback
from seiscomp3 import Core, Client, DataModel, Communication, IO

class PickLoader(Client.Application):

    def __init__(self):
        Client.Application.__init__(self, len(sys.argv), sys.argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, False)
        self._startTime = self._endTime = None

    def createCommandLineDescription(self):
        Client.Application.createCommandLineDescription(self)
        self.commandline().addGroup("Dump")
        self.commandline().addStringOption("Dump", "begin", "specify start of time window")
        self.commandline().addStringOption("Dump", "end", "specify end of time window")
        self.commandline().addStringOption("Dump", "event", "compute a time window from the event")
        self.commandline().addStringOption("Dump", "origins", "specify space separated list of origin ids to be also loaded")

    def _processCommandLineOptions(self):
        try:    start = self.commandline().optionString("begin")
        except: start = None

        try:    end = self.commandline().optionString("end")
        except: end = None

        try:
            orids = self.commandline().optionString("origins")
            self._orids = orids.split()
        except:
            self._orids = []

        try:
            self._evid = self.commandline().optionString("event")
        except:
            self._evid = ""


        if start:
            self._startTime = Core.Time.GMT()
            if self._startTime.fromString(start, "%F %T") == False:
                print >> sys.stderr, "Wrong 'begin' format"
                return False
        if end:
            self._endTime = Core.Time.GMT()
            if self._endTime.fromString(end, "%F %T") == False:
                print >> sys.stderr, "Wrong 'end' format"
                return False
        return True

    def run(self):
        if not self._processCommandLineOptions():
            sys.exit(5)

        dbq = self.query()
        ep  = DataModel.EventParameters()

        # If we got an event ID as command-line argument...
        if self._evid:
            # Retrieve event from DB
            evt = dbq.loadObject(DataModel.Event.TypeInfo(), self._evid)
            evt = DataModel.Event.Cast(evt)
            if evt is None:
                raise TypeError, "unknown event '" + self._evid + "'"
            # If start time was not specified, compute it from origin time.
            if self._startTime is None:
                orid = evt.preferredOriginID()
                org = dbq.loadObject(DataModel.Origin.TypeInfo(), orid)
                org = DataModel.Origin.Cast(org)
                t0 = org.time().value()
                self._startTime = t0 + Core.TimeSpan(-before)
                self._endTime   = t0 + Core.TimeSpan(after)
                print>>sys.stderr, "time window: %s ... %s" % (self._startTime, self._endTime)

            # Loop over all origins of the event
            for org in dbq.getOrigins(self._evid):
                org = DataModel.Origin.Cast(org)
                # We only look for manual events.
                if org.evaluationMode() != DataModel.MANUAL:
                    continue
                self._orids.append(org.publicID())

        # FIRST the pick query loop, THEN the amplitude query loop!
        # NESTED QUERY LOOPS ARE NOT ALLOWED!!!
        picks = []
        for obj in dbq.getPicks(self._startTime, self._endTime):
            pick = DataModel.Pick.Cast(obj)
            if pick:
                picks.append(pick)
                ep.add(pick)
        print >> sys.stderr, "loaded %d picks                         " % ep.pickCount()

        for i,pick in enumerate(picks):
            # amplitude query loop for each pick, see above comments.
            for obj in dbq.getAmplitudesForPick(pick.publicID()):
                ampl = DataModel.Amplitude.Cast(obj)
                if ampl:
                    ep.add(ampl)
            sys.stderr.write("loaded amplitudes for %d of %d picks\r" % (i,len(picks)))
        print >> sys.stderr, "loaded %d amplitudes                    " % ep.amplitudeCount()

        for i,orid in enumerate(self._orids):
            # XXX There was occasionally a problem with:
            #   org = dbq.loadObject(DataModel.Origin.TypeInfo(), orid)
            #   org = DataModel.Origin.Cast(org)
            # NOTE when org was directly overwritten.
            # resulting in a segfault. The reason is not clear, but
            # is most probably in the Python wrapper. The the segfault
            # can be avoided by creating an intermediate object 'obj'.
            obj = dbq.loadObject(DataModel.Origin.TypeInfo(), orid)
            org = DataModel.Origin.Cast(obj)
            ep.add(org)
            sys.stderr.write("loaded %d of %d manual origins\r" % (i,len(self._orids)))
        print >> sys.stderr, "loaded %d origins                       " % ep.originCount()

        # finally dump event parameters as formatted XML archive to stdout
        ar = IO.XMLArchive()
        ar.setFormattedOutput(True)
        ar.create("-")
        ar.writeObject(ep)
        ar.close()

        del ep


def main():
    app = PickLoader()
    app()

if __name__ == "__main__":
    main()
