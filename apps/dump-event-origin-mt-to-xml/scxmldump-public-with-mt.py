#!/usr/bin/env python
#
# Dump origin and moment tensor information for an event to SC3 XML.
#
# Could be invoked in a pipeline like:
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


    def _removeComments(self, obj):
        if obj is not None and not self.commandline().hasOption("include-comments"):
            while obj.commentCount() > 0:
                obj.removeComment(0)

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

    def _stripMomentTensor(self, mt):
        mt.setGreensFunctionID("")
        while mt.momentTensorStationContributionCount() > 0:
            mt.removeMomentTensorStationContribution(0)
        while mt.momentTensorPhaseSettingCount() > 0:
            mt.removeMomentTensorPhaseSetting(0)

    def _loadEvent(self, evid):
        # Retrieve event from DB
        # May return None
        event = self.query().loadObject(DataModel.Event.TypeInfo(), evid)
        event = DataModel.Event.Cast(event)
        if event:
            self._removeComments(event)
        return event

    def _loadOrigin(self, orid):
        # Retrieve origin from DB
        # May return None
        obj = self.query().loadObject(DataModel.Origin.TypeInfo(), orid)
        origin = DataModel.Origin.Cast(obj)
        if origin:
            self._stripOrigin(origin)
            self._removeComments(origin)
        return origin

    def _loadFocalMechanism(self, fmid):
        # Retrieve FocalMechanism from DB
        # May return None
        obj = self.query().loadObject(DataModel.FocalMechanism.TypeInfo(), fmid)
        fm = DataModel.FocalMechanism.Cast(obj)
        if fm:
            self.query().loadMomentTensors(fm)
            for i in xrange(fm.momentTensorCount()):
                mt = fm.momentTensor(i)
                self._stripMomentTensor(mt)
        return fm

    def run(self):
        evid = self.commandline().optionString("event")

        ep = DataModel.EventParameters()

        event = self._loadEvent(evid)
        if event is None:
            raise ValueError, "unknown event '" + evid + "'"

        preferredOrigin = self._loadOrigin(event.preferredOriginID())
        if preferredOrigin is None:
            raise ValueError, "unknown origin '" + event.preferredOriginID() + "'"

        focalMechanism = self._loadFocalMechanism(event.preferredFocalMechanismID())

        if focalMechanism is None:
            momentTensor = derivedOrigin = triggeringOrigin = None
        else:
            if self.commandline().hasOption("include-triggering-origin"):
                if event.preferredOriginID() != focalMechanism.triggeringOriginID():
                    triggeringOrigin = self._loadOrigin(focalMechanism.triggeringOriginID())
                else:
                    triggeringOrigin = preferredOrigin
            else:
                triggeringOrigin = None
                focalMechanism.setTriggeringOriginID("")

            momentTensor = focalMechanism.momentTensor(0)
            derivedOrigin = self._loadOrigin(momentTensor.derivedOriginID())

        # take care if Origin/FocalMechanism references
        while (event.originReferenceCount() > 0):
            event.removeOriginReference(0)
        if preferredOrigin:
            event.add(DataModel.OriginReference(preferredOrigin.publicID()))
        if derivedOrigin:
            event.add(DataModel.OriginReference(derivedOrigin.publicID()))
        if triggeringOrigin is not None:
            if event.preferredOriginID() != triggeringOrigin.publicID():
                event.add(DataModel.OriginReference(triggeringOrigin.publicID()))
        while (event.focalMechanismReferenceCount() > 0):
            event.removeFocalMechanismReference(0)
        if focalMechanism:
            event.add(DataModel.FocalMechanismReference(focalMechanism.publicID()))
            self._removeComments(focalMechanism)

        # strip creation info
        if not self.commandline().hasOption("include-full-creation-info"):
            self._stripCreationInfo(event)
            if focalMechanism:
                self._stripCreationInfo(focalMechanism)
                for i in xrange(focalMechanism.momentTensorCount()):
                    self._stripCreationInfo(focalMechanism.momentTensor(i))
            for org in [ preferredOrigin, triggeringOrigin, derivedOrigin ]:
                if org is not None:
                    self._stripCreationInfo(org)
                    for i in xrange(org.magnitudeCount()):
                        self._stripCreationInfo(org.magnitude(i))

        ep.add(event)
        ep.add(preferredOrigin)
        if focalMechanism:
            if triggeringOrigin:
                if triggeringOrigin is not preferredOrigin:
                    ep.add(triggeringOrigin)
            if derivedOrigin:
                ep.add(derivedOrigin)
            ep.add(focalMechanism)

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
