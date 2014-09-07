#!/usr/bin/env python

#########################################################################
# Copyright (C) by GFZ Potsdam                                          #
#                                                                       #
# author: Joachim Saul                                                  #
# email:  saul@gfz-potsdam.de                                           #
#########################################################################

import sys
from seiscomp3 import Core, DataModel, Client, Logging

class MyFocMec: pass

class FocalMechanismImporter(Client.Application):

    def __init__(self, argc, argv):
        Client.Application.__init__(self, argc, argv)
        self.setDatabaseEnabled(True, True)
        self.setMessagingEnabled(True)
        self.setPrimaryMessagingGroup("LOCATION")
        self.setRecordStreamEnabled(False)

    def createCommandLineDescription(self):
        Client.Application.createCommandLineDescription(self)
        self.commandline().addGroup("Mode");
        self.commandline().addOption("Mode", "test", "Do not send any object");
        self.commandline().addGroup("Event");
        self.commandline().addStringOption("Event", "event,E", "ID of event to attach the focal mechanism to")
        self.commandline().addStringOption("Event", "sdr1", "strike,dip,rake of nodal plane 1")
        self.commandline().addStringOption("Event", "sdr2", "strike,dip,rake of nodal plane 2")
        self.commandline().addStringOption("Event", "mw", "moment magnitude")

    def init(self):
        if not Client.Application.init(self):
            return False
        return True

    def run(self):
        try:
            eventID = self.commandline().optionString("event")
        except:
            sys.stderr.write("You must specify event id\n")
            return False

        fm = MyFocMec()

        try:
            sdr1 = self.commandline().optionString("sdr1")
            fm.str1, fm.dip1, fm.rak1 = tuple(map(float,sdr1.split(",")))
        except:
            sys.stderr.write("You must specify at least NP1\n")
            return False

        try:
            sdr2 = self.commandline().optionString("sdr2")
            fm.str2, fm.dip2, fm.rak2 = tuple(map(float,sdr2.split(",")))
        except:
            pass

        try:
            fm.Mw = self.commandline().optionString("mw")
            fm.Mw = float(fm.Mw)
        except:
            fm.Mw = None

        return self.importFocalMechanism(eventID, fm)


    def importFocalMechanism(self, eventID, fm):

        now = Core.Time.GMT()
        crea = DataModel.CreationInfo()
        crea.setAuthor("MT import script")
        crea.setAgencyID("TEST")
        crea.setCreationTime(now)
        crea.setModificationTime(now)

        event = self.query().loadObject(DataModel.Event.TypeInfo(), eventID)
        event = DataModel.Event.Cast(event)
        if event is None:
            Logging.error("unknown event '%s'" % eventID)
            return False

        originID = event.preferredOriginID()
        origin = self.query().loadObject(DataModel.Origin.TypeInfo(), originID)
        origin = DataModel.Origin.Cast(origin)
        if not origin:
            Logging.error("origin '%s' not loaded" % originID)
            return False

        # clone origin to attach Mw to it
        publicID = "MT#Origin#"+origin.publicID()
        origin = DataModel.Origin.Cast(origin.clone())
        origin.setPublicID(publicID)
        origin.setCreationInfo(crea)

        if fm.Mw:
            magnitude = DataModel.Magnitude.Create()
            magnitude.setCreationInfo(crea)
            magnitude.setStationCount(0)
            magnitude.setMagnitude(DataModel.RealQuantity(fm.Mw))
            magnitude.setType("Mw")
            origin.add(magnitude)

        # create and populate a focal mechanism
        focmecID = "FM#"+eventID+now.toString("#%Y%m%d.%H%M%S.%f000000")[:20] 
        focmec = DataModel.FocalMechanism.Create(focmecID)
        focmec.setTriggeringOriginID(originID)

        try:
            np1 = DataModel.NodalPlane()
            np1.setStrike( DataModel.RealQuantity(fm.str1) )
            np1.setDip(    DataModel.RealQuantity(fm.dip1) )
            np1.setRake(   DataModel.RealQuantity(fm.rak1) )
        except AttributeError:
            np1 = None

        try:
            np2 = DataModel.NodalPlane()
            np2.setStrike( DataModel.RealQuantity(fm.str2) )
            np2.setDip(    DataModel.RealQuantity(fm.dip2) )
            np2.setRake(   DataModel.RealQuantity(fm.rak2) )
        except AttributeError:
            npr21 = None

        np = DataModel.NodalPlanes()
        if np1:
            np.setNodalPlane1(np1)
        if np2:
            np.setNodalPlane2(np2)
 
        focmec.setNodalPlanes(np) 
        focmec.setCreationInfo(crea)
        focmec.setEvaluationStatus(DataModel.REVIEWED)
        focmec.setEvaluationMode(DataModel.MANUAL)


        # create and populate a moment tensor
        momtenID = "MT#"+eventID+now.toString("#%Y%m%d.%H%M%S.%f000000")[:20] 
        momten = DataModel.MomentTensor.Create(momtenID)
        momten = DataModel.MomentTensor.Cast(momten)
        momten.setDerivedOriginID(origin.publicID())
        if fm.Mw:
            momten.setMomentMagnitudeID(magnitude.publicID())
        momten.setCreationInfo(crea)
        focmec.add(momten)

        ep = DataModel.EventParameters()
        DataModel.Notifier.Enable()
        ep.add(focmec)
        msg = DataModel.Notifier.GetMessage()
        if not self.commandline().hasOption("test"):
            if not self.connection().send("FOCMECH", msg):
                sys.stderr.write("Failed to send focmec %s\n" % focmecID)
        DataModel.Notifier.Disable()

        DataModel.Notifier.Enable()
        ep.add(origin)
        msg = DataModel.Notifier.GetMessage()
        if not self.commandline().hasOption("test"):
            if not self.connection().send("LOCATION", msg):
                sys.stderr.write("Failed to send origin %s\n" % originID)
        DataModel.Notifier.Disable()

        if fm.Mw:
            DataModel.Notifier.Enable()
            msg = DataModel.Notifier.GetMessage()
            if not self.commandline().hasOption("test"):
                if not self.connection().send("MAGNITUDE", msg):
                    sys.stderr.write("Failed to send magnitude\n")
            DataModel.Notifier.Disable()

        return True

app = FocalMechanismImporter(len(sys.argv), sys.argv)
app.setMessagingUsername("imp-fm")
sys.exit(app())
