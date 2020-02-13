#!/usr/bin/env python

from __future__ import print_function

import sys
import seiscomp.core, seiscomp.client, seiscomp.datamodel
import seiscomp.io, seiscomp.logging


def parse_time_string(s):
    t = seiscomp.core.Time.GMT()
    for fmt in [ "%FT%T.%fZ", "%FT%TZ", "%F %T" ]:
        if t.fromString(s, fmt):
            return t
    print("Wrong time format", file=sys.stderr)


class PickLoader(seiscomp.client.Application):

    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, False)
        self._startTime = self._endTime = None
        # time window relative to origin time of specified event:
        self._before = 4*3600. # 4 hours
        self._after  = 1*3600. # 1 hour

    def createCommandLineDescription(self):
        seiscomp.client.Application.createCommandLineDescription(self)
        self.commandline().addGroup("Dump")
        self.commandline().addStringOption("Dump", "begin", "specify start of time window")
        self.commandline().addStringOption("Dump", "end", "specify end of time window")
        self.commandline().addStringOption("Dump", "event", "compute a time window from the event")
        self.commandline().addStringOption("Dump", "before", "start time window this many seconds before origin time")
        self.commandline().addStringOption("Dump", "after",  "end time window this many seconds after origin time")
        self.commandline().addStringOption("Dump", "origins", "specify space separated list of origin ids to be also loaded")
        self.commandline().addStringOption("Dump", "network-blacklist", "specify space separated list of network codes to be excluded")
        self.commandline().addOption("Dump", "no-origins", "don't include any origins")
        self.commandline().addOption("Dump", "no-manual-picks", "don't include any manual picks")

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

        # only if we got an event ID we need to look for "--before" and "--after"
        if self._evid:
            if self.commandline().hasOption("before"):
                before = self.commandline().optionString("before")
                self._before = float(before)
            if self.commandline().hasOption("after"):
                after  = self.commandline().optionString("after")
                self._after = float(after)

        if start:
            self._startTime = parse_time_string(start)
            if not self._startTime:
                return False
        if end:
            self._endTime = parse_time_string(end)
            if not self._endTime:
                return False
        try:
            self._networkBlacklist = self.commandline().optionString("network-blacklist").split()
        except:
            self._networkBlacklist = []

        return True

    def run(self):
        if not self._processCommandLineOptions():
            return False

        dbq = self.query()
        ep  = seiscomp.datamodel.EventParameters()

        # If we got an event ID as command-line argument...
        if self._evid:
            # Retrieve event from DB
            evt = dbq.loadObject(seiscomp.datamodel.Event.TypeInfo(), self._evid)
            evt = seiscomp.datamodel.Event.Cast(evt)
            if evt is None:
                raise TypeError("unknown event '" + self._evid + "'")
            # If start time was not specified, compute it from origin time.
            if self._startTime is None:
                orid = evt.preferredOriginID()
                org = dbq.loadObject(seiscomp.datamodel.Origin.TypeInfo(), orid)
                org = seiscomp.datamodel.Origin.Cast(org)
                t0 = org.time().value()
                self._startTime = t0 + seiscomp.core.TimeSpan(-self._before)
                self._endTime   = t0 + seiscomp.core.TimeSpan( self._after)
#               print("time window: %s ... %s" % (self._startTime, self._endTime), file=sys.stderr)

            if not self.commandline().hasOption("no-origins"):
                # Loop over all origins of the event
                for org in dbq.getOrigins(self._evid):
                    org = seiscomp.datamodel.Origin.Cast(org)
                    # We only look for manual events.
                    if org.evaluationMode() != seiscomp.datamodel.MANUAL:
                        continue
                    self._orids.append(org.publicID())

        picks = {}
        for obj in dbq.getPicks(self._startTime, self._endTime):
            pick = seiscomp.datamodel.Pick.Cast(obj)
            if pick:
                if pick.evaluationMode() == seiscomp.datamodel.MANUAL and self.commandline().hasOption("no-manual-picks"):
                    continue
                if pick.waveformID().networkCode() in self._networkBlacklist:
                    continue
                picks[pick.publicID()] = pick
                ep.add(pick)
        seiscomp.logging.debug("loaded %d picks" % ep.pickCount())

        for obj in dbq.getAmplitudes(self._startTime, self._endTime):
            ampl = seiscomp.datamodel.Amplitude.Cast(obj)
            if ampl:
                if not ampl.pickID():
                    continue
                if ampl.pickID() not in picks:
                    continue
                ep.add(ampl)
        del picks
        seiscomp.logging.debug("loaded %d amplitudes" % ep.amplitudeCount())

        if not self.commandline().hasOption("no-origins"):
            for i,orid in enumerate(self._orids):
                # XXX There was occasionally a problem with:
                #   org = dbq.loadObject(seiscomp.datamodel.Origin.TypeInfo(), orid)
                #   org = seiscomp.datamodel.Origin.Cast(org)
                # NOTE when org was directly overwritten.
                # resulting in a segfault. The reason is not clear, but
                # is most probably in the Python wrapper. The the segfault
                # can be avoided by creating an intermediate object 'obj'.
                obj = dbq.loadObject(seiscomp.datamodel.Origin.TypeInfo(), orid)
                org = seiscomp.datamodel.Origin.Cast(obj)
                ep.add(org)
            seiscomp.logging.debug("loaded %d manual origins" % ep.originCount())

        # finally dump event parameters as formatted XML archive to stdout
        ar = seiscomp.io.XMLArchive()
        ar.setFormattedOutput(True)
        ar.create("-")
        ar.writeObject(ep)
        ar.close()
        del ep
        return True


def main():
    app = PickLoader(len(sys.argv), sys.argv)
    app()

if __name__ == "__main__":
    main()
