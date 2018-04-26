#!/usr/bin/env python
############################################################################
#                                                                          #
#    Copyright (C) 2015 by GFZ Potsdam                                     #
#                                                                          #
#    author: Joachim Saul                                                  #
#    email:  saul@gfz-potsdam.de                                           #
#                                                                          #
############################################################################

from __future__ import print_function
import sys, traceback
import seiscomp3.Client, seiscomp3.DataModel
import sc3stuff.util

line_template = "%(time)s %(net)-2s %(sta)5s %(cha)3s %(loc)2s %(residual)7.2f %(delta)7.3f %(azimuth)5.1f %(status)s %(phase)-5s %(weight)g\n"

yaml_template = """-
  net: %(net)s
  sta: %(sta)s
  loc: %(loc)s
  cha: %(cha)s
  time: %(time)s
  residual: %(residual).3f
  delta: %(delta).3f
  azimuth: %(azimuth).3f
  status: %(status)s
  phase: %(phase)s
  weight: %(weight)g
  id: %(pid)s
  author: %(author)s
"""


def _todict(pick, arrival, pad_location_code=True):
    d = dict(pid=pick.publicID())
    n,s,l,c = sc3stuff.util.nslc(pick.waveformID())
    if l=="" and pad_location_code is True:  l="--"
    d["net"], d["sta"], d["loc"], d["cha"] = n, s, l, c
    d["time"]     = sc3stuff.util.format_time(pick.time().value())
    d["residual"] = arrival.timeResidual()
    d["delta"]    = arrival.distance()
    d["azimuth"]  = arrival.azimuth()
    d["weight"]   = arrival.weight()
    d["phase"]    = arrival.phase().code() 
    d["author"]   = pick.creationInfo().author() 
    d["status"]   = "A" if sc3stuff.util.automatic(pick) else "M"
    return d


def printPickList(event, origin, pick, ampl, fm, min_weight=-1, f=sys.stdout):
    for eventID in event:
        evt = event[eventID]
        for originID in origin:
            if originID != evt.preferredOriginID():
                continue
            org = origin[originID]
            for i in xrange(org.arrivalCount()):
                a = org.arrival(i)
                if a.weight() < min_weight:
                    continue
                p = pick[a.pickID()]

#               f.write(line_template % _todict(p, a))
                f.write(yaml_template % _todict(p, a))


class EventLoaderApp(seiscomp3.Client.Application):

    def __init__(self, argc, argv):
        seiscomp3.Client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setLoggingToStdErr(True)
        self.setDaemonEnabled(False)
        self.setRecordStreamEnabled(False)


    def createCommandLineDescription(self):
        self.commandline().addGroup("Dump")
        self.commandline().addStringOption("Dump", "event,E", "ID of event to dump")
        self.commandline().addGroup("Input")
        self.commandline().addStringOption("Input", "xml", "specify xml file")
        return True


    def validateParameters(self):
        # This is where BOTH
        #   (1) the command line arguments are accessible
        #   (2) the set...Enabled methods have an effect
        # Thus e.g. enabling/disabling the database MUST take place HERE.
        # NEITHER in __init__(), where command line arguments are not yet accessible
        # NOR in init() where the database has been configured and set up already.
        if not seiscomp3.Client.Application.validateParameters(self):
            return False

        try:
            self._xmlFile = self.commandline().optionString("xml")
        except:
            self._xmlFile = None
        try:
            self._eventID = self.commandline().optionString("event")
        except:
            self._eventID = None

        if self._xmlFile:
            self.setDatabaseEnabled(False, False)
        else:
            self.setDatabaseEnabled(True, True)

        return True


    def _readEventParametersFromXML(self):
        ep = sc3stuff.util.readEventParametersFromXML(self._xmlFile)
        if ep is None:
            raise TypeError, self._xmlFile + ": no eventparameters found"
        return ep


    def _readEventParametersFromDB(self):
        # load event and preferred origin
        evt = self.query().loadObject(seiscomp3.DataModel.Event.TypeInfo(), self._eventID)
        evt = seiscomp3.DataModel.Event.Cast(evt)
        if evt is None:
            seiscomp3.Logging.error("unknown event '%s'" % self._eventID)
            return
        originID = evt.preferredOriginID()
        org = self.query().loadObject(seiscomp3.DataModel.Origin.TypeInfo(), originID)
        org = seiscomp3.DataModel.Origin.Cast(org)
        if not org:
            seiscomp3.Logging.error("origin '%s' not loaded" % originID)
            return

        pick = {}
        for obj in self.query().getPicks(originID):
            p = seiscomp3.DataModel.Pick.Cast(obj)
            key = p.publicID()
            pick[key] = p

        ampl = {}
        for obj in self.query().getAmplitudesForOrigin(originID):
            amp = seiscomp3.DataModel.Amplitude.Cast(obj)
            key = amp.publicID()
            ampl[key] = amp

        # create and populate EventParameters instance
        ep = seiscomp3.DataModel.EventParameters()
        ep.add(evt)
        ep.add(org)
        for key in pick:
            ep.add(pick[key])
        for key in ampl:
            ep.add(ampl[key])
        return ep
        # TODO: focal mechanisms for completeness


    def run(self):
        if self._xmlFile:
            ep = self._readEventParametersFromXML()
        else:
            if not self._eventID:
                seiscomp3.Logging.error("need to specify at an event id to read from database")
                return False
            ep = self._readEventParametersFromDB()
        if not ep:
            return False

        event, origin, pick, ampl, fm = sc3stuff.util.extractEventParameters(ep, self._eventID)

        printPickList(event, origin, pick, ampl, fm)

        return True


def main():
    app = EventLoaderApp(len(sys.argv), sys.argv)
    app()

if __name__ == "__main__":
    main()
