#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#                                                                          #
#    Copyright (C) 2015 by GFZ Potsdam                                     #
#                                                                          #
#    author: Joachim Saul                                                  #
#    email:  saul@gfz-potsdam.de                                           #
#                                                                          #
############################################################################

from __future__ import print_function

import seiscomp3.Client, seiscomp3.DataModel
import sc3stuff.util


class EventLoaderApp(seiscomp3.Client.Application):

    def __init__(self, argc, argv):
        self.setXmlEnabled(True)
        seiscomp3.Client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setLoggingToStdErr(True)
        self.setDaemonEnabled(False)
        self.setRecordStreamEnabled(False)


    def setXmlEnabled(self, enable=True):
        """ To be called from __init__() """
        self._xmlEnabled = enable

    def xmlEnabled(self):
        return self._xmlEnabled


    def createCommandLineDescription(self):
        self.commandline().addGroup("Dump")
        self.commandline().addStringOption("Dump", "event,E", "ID of event to dump")

        if self.xmlEnabled():
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

        self._xmlFile = None
        try:
            if self.xmlEnabled():
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

    def readEventParameters(self):
        if self._xmlFile:
            ep = self._readEventParametersFromXML()
        else:
            if not self._eventID:
                seiscomp3.Logging.error("need to specify at an event id to read from database")
                return False
            ep = self._readEventParametersFromDB()
        if ep:
            return ep
        return None

    def run(self):
        if not self._ep:
            self._ep = self.readEventParameters()
        if not self._ep:
            return False
        return True
