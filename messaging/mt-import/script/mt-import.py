#!/usr/bin/env python

#########################################################################
# Copyright (C) by GFZ Potsdam                                          #
#                                                                       #
# author: Joachim Saul                                                  #
# email:  saul@gfz-potsdam.de                                           #
#########################################################################

import sys
import seiscomp.core, seiscomp.datamodel, seiscomp.client, seiscomp.logging

class MyFocMec: pass

class FocalMechanismImporter(seiscomp.client.Application):

    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setDatabaseEnabled(True, True)
        self.setMessagingEnabled(True)
        self.setPrimaryMessagingGroup("LOCATION")
        self.setRecordStreamEnabled(False)

    def createCommandLineDescription(self):
        seiscomp.client.Application.createCommandLineDescription(self)
        self.commandline().addGroup("Mode");
        self.commandline().addOption("Mode", "test", "Do not send any object");
        self.commandline().addGroup("Event");
        self.commandline().addStringOption("Event", "event,E", "ID of event to attach the focal mechanism to")
        self.commandline().addStringOption("Event", "sdr1", "strike,dip,rake of nodal plane 1")
        self.commandline().addStringOption("Event", "sdr2", "strike,dip,rake of nodal plane 2")
        self.commandline().addStringOption("Event", "mw", "moment magnitude")

    def init(self):
        if not seiscomp.client.Application.init(self):
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

        now = seiscomp.core.Time.GMT()
        crea = seiscomp.datamodel.CreationInfo()
        crea.setAuthor("MT import script")
        crea.setAgencyID("TEST")
        crea.setCreationTime(now)
        crea.setModificationTime(now)

        event = self.query().loadObject(seiscomp.datamodel.Event.TypeInfo(), eventID)
        event = seiscomp.datamodel.Event.Cast(event)
        if event is None:
            seiscomp.logging.error("unknown event '%s'" % eventID)
            return False

        originID = event.preferredOriginID()
        origin = self.query().loadObject(seiscomp.datamodel.Origin.TypeInfo(), originID)
        origin = seiscomp.datamodel.Origin.Cast(origin)
        if not origin:
            seiscomp.logging.error("origin '%s' not loaded" % originID)
            return False

        # clone origin to attach Mw to it
        publicID = "MT#Origin#"+origin.publicID()
        origin = seiscomp.datamodel.Origin.Cast(origin.clone())
        origin.setPublicID(publicID)
        origin.setCreationInfo(crea)

        if fm.Mw:
            magnitude = seiscomp.datamodel.Magnitude.Create()
            magnitude.setCreationInfo(crea)
            magnitude.setStationCount(0)
            magnitude.setMagnitude(seiscomp.datamodel.RealQuantity(fm.Mw))
            magnitude.setType("Mw")
            origin.add(magnitude)

        # create and populate a focal mechanism
        focmecID = "FM#"+eventID+now.toString("#%Y%m%d.%H%M%S.%f000000")[:20] 
        focmec = seiscomp.datamodel.FocalMechanism.Create(focmecID)
        focmec.setTriggeringOriginID(originID)

        try:
            np1 = seiscomp.datamodel.NodalPlane()
            np1.setStrike( seiscomp.datamodel.RealQuantity(fm.str1) )
            np1.setDip(    seiscomp.datamodel.RealQuantity(fm.dip1) )
            np1.setRake(   seiscomp.datamodel.RealQuantity(fm.rak1) )
        except AttributeError:
            np1 = None

        try:
            np2 = seiscomp.datamodel.NodalPlane()
            np2.setStrike( seiscomp.datamodel.RealQuantity(fm.str2) )
            np2.setDip(    seiscomp.datamodel.RealQuantity(fm.dip2) )
            np2.setRake(   seiscomp.datamodel.RealQuantity(fm.rak2) )
        except AttributeError:
            npr21 = None

        np = seiscomp.datamodel.NodalPlanes()
        if np1:
            np.setNodalPlane1(np1)
        if np2:
            np.setNodalPlane2(np2)
 
        focmec.setNodalPlanes(np) 
        focmec.setCreationInfo(crea)
        focmec.setEvaluationStatus(seiscomp.datamodel.REVIEWED)
        focmec.setEvaluationMode(seiscomp.datamodel.MANUAL)

        # create moment tensor and populate it with (just) Mw
        momtenID = "MT#"+eventID+now.toString("#%Y%m%d.%H%M%S.%f000000")[:20] 
        momten = seiscomp.datamodel.MomentTensor.Create(momtenID)
        momten = seiscomp.datamodel.MomentTensor.Cast(momten)
        momten.setDerivedOriginID(origin.publicID())
        if fm.Mw:
            momten.setMomentMagnitudeID(magnitude.publicID())
        momten.setCreationInfo(crea)
        # Obviously we could populate the entire moment tensor
        # elements, but we don't here to keep things simple and
        # because it's just for demo purposes.
        focmec.add(momten)

        # add the created objects to the EventParameters
        # then retrieve and send corresponding notifier messages
        ep = seiscomp.datamodel.EventParameters()
        seiscomp.datamodel.Notifier.Enable()
        ep.add(focmec)
        msg = seiscomp.datamodel.Notifier.GetMessage()
        if msg and not self.commandline().hasOption("test"):
            if not self.connection().send("FOCMECH", msg):
                sys.stderr.write("Failed to send focmec %s\n" % focmecID)
        seiscomp.datamodel.Notifier.Disable()

        seiscomp.datamodel.Notifier.Enable()
        ep.add(origin)
        msg = seiscomp.datamodel.Notifier.GetMessage()
        if msg and not self.commandline().hasOption("test"):
            if not self.connection().send("LOCATION", msg):
                sys.stderr.write("Failed to send origin %s\n" % originID)
        seiscomp.datamodel.Notifier.Disable()

        return True


app = FocalMechanismImporter(len(sys.argv), sys.argv)
app.setMessagingUsername("imp-fm")
sys.exit(app())
