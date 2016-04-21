#!/usr/bin/env python

# Dump Origin and moment tensor information to SC3 XML.
#
# Could be invoked like:
#
#  python scxmldump-public-with-mt.py --debug -d "$db" -E "$evid" |
#  sccnv -f -i trunk:- -o qml1.2:"$evid-mt.QuakeML"
#
# The above will dump the event information to QuakeML 1.2

import sys, traceback
from seiscomp3 import Core, Client, DataModel, Communication, IO

class MomentTensorDumper(Client.Application):

    def __init__(self):
        Client.Application.__init__(self, len(sys.argv), sys.argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, False)
        self._startTime = self._endTime = None

    def createCommandLineDescription(self):
        Client.Application.createCommandLineDescription(self)
        self.commandline().addGroup("Dump")
        self.commandline().addStringOption("Dump", "event,E", "compute a time window from the event")
        self.commandline().addOption("Dump", "include-triggering-origin,T", "include triggering origin")
        self.commandline().addOption("Dump", "include-full-creation-info,I", "include full creation info")
        self.commandline().addOption("Dump", "include-comments,C", "include all comments")

    def _stripOrigin(self, org):
        # remove arrivals and magnitudes
        while org.arrivalCount() > 0:
            org.removeArrival(0)
        while org.magnitudeCount() > 0:
            org.removeMagnitude(0)
        while org.stationMagnitudeCount() > 0:
            org.removeStationMagnitude(0)

    def _stripCreationInfo(self, obj):
        ## strip creationInfo entirely:
        #empty = DataModel.CreationInfo()
        #obj.setCreationInfo(empty)
        obj.creationInfo().setAuthor("")

    def run(self):
        evid = self.commandline().optionString("event")

        ep = DataModel.EventParameters()

        # If we got an event ID as command-line argument...
        # Retrieve event from DB
        event = self.query().loadObject(DataModel.Event.TypeInfo(), evid)
        event = DataModel.Event.Cast(event)
        if event is None:
            raise TypeError, "unknown event '" + evid + "'"

        i = event.preferredOriginID()
        obj = self.query().loadObject(DataModel.Origin.TypeInfo(), i)
        preferredOrigin = DataModel.Origin.Cast(obj)
        self._stripOrigin(preferredOrigin)

        i = event.preferredFocalMechanismID()
        obj = self.query().loadObject(DataModel.FocalMechanism.TypeInfo(), i)
        focalMechanism = DataModel.FocalMechanism.Cast(obj)
        self.query().loadMomentTensors(focalMechanism)
        for i in xrange(focalMechanism.momentTensorCount()):
            momentTensor = focalMechanism.momentTensor(i)
            momentTensor.setGreensFunctionID("")
            while momentTensor.momentTensorStationContributionCount() > 0:
                momentTensor.removeMomentTensorStationContribution(0)
            while momentTensor.momentTensorPhaseSettingCount() > 0:
                momentTensor.removeMomentTensorPhaseSetting(0)

        if self.commandline().hasOption("include-triggering-origin"):
            if event.preferredOriginID() != focalMechanism.triggeringOriginID():
                i = focalMechanism.triggeringOriginID()
                obj = self.query().loadObject(DataModel.Origin.TypeInfo(), i)
                triggeringOrigin = DataModel.Origin.Cast(obj)
                self._stripOrigin(preferredOrigin)
            else:
                triggeringOrigin = preferredOrigin
        else:
            triggeringOrigin = None
            focalMechanism.setTriggeringOriginID("")

        momentTensor = focalMechanism.momentTensor(0)
        i = momentTensor.derivedOriginID()
        obj = self.query().loadObject(DataModel.Origin.TypeInfo(), i)
        derivedOrigin = DataModel.Origin.Cast(obj)

        while (event.originReferenceCount() > 0):
            event.removeOriginReference(0)
        event.add(DataModel.OriginReference(preferredOrigin.publicID()))
        event.add(DataModel.OriginReference(derivedOrigin.publicID()))
        if triggeringOrigin is not None:
            if event.preferredOriginID() != triggeringOrigin.publicID():
                event.add(DataModel.OriginReference(triggeringOrigin.publicID()))
        while (event.focalMechanismReferenceCount() > 0):
            event.removeFocalMechanismReference(0)
        event.add(DataModel.FocalMechanismReference(focalMechanism.publicID()))

        # strip comments
        if not self.commandline().hasOption("include-comments"):
            for obj in [ event, preferredOrigin, triggeringOrigin, derivedOrigin, focalMechanism ]:
                if obj is not None:
                    while obj.commentCount() > 0:
                        obj.removeComment(0)

        # strip creation info
        if not self.commandline().hasOption("include-full-creation-info"):
            self._stripCreationInfo(event)
            self._stripCreationInfo(focalMechanism)
            for i in xrange(focalMechanism.momentTensorCount()):
                self._stripCreationInfo(focalMechanism.momentTensor(i))
            for org in [ preferredOrigin, triggeringOrigin, derivedOrigin ]:
                if org is None:
                    continue
                self._stripCreationInfo(org)
                for i in xrange(org.magnitudeCount()):
                    self._stripCreationInfo(org.magnitude(i))

        ep.add(event)
        ep.add(preferredOrigin)
        if triggeringOrigin is not preferredOrigin:
            ep.add(triggeringOrigin)
        ep.add(focalMechanism)
        ep.add(derivedOrigin)

        # finally dump event parameters as formatted XML archive to stdout
        ar = IO.XMLArchive()
        ar.setFormattedOutput(True)
        ar.create("-")
        ar.writeObject(ep)
        ar.close()

        del ep


def main():
    app = MomentTensorDumper()
    app()

if __name__ == "__main__":
    main()
