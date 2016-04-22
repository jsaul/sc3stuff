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
        self.commandline().addOption("Dump", "include-full-creation-info,I", "include full creation info")
        self.commandline().addOption("Dump", "include-comments,C", "include all comments")


    def _removeCommentsIfRequested(self, obj):
        if obj is not None and not self.commandline().hasOption("include-comments"):
            while obj.commentCount() > 0:
                obj.removeComment(0)

    def _stripOrigin(self, org):
        # remove arrivals and magnitudes
        while org.arrivalCount() > 0:
            # If the origin was loaded using query().getObject()
            # this is actually not needed.
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
        # use loadObject() because we want the complete descriptions
        event = self.query().loadObject(DataModel.Event.TypeInfo(), evid)
        event = DataModel.Event.Cast(event)
        if event:
            self._removeCommentsIfRequested(event)
        return event

    def _loadOrigin(self, orid):
        # Retrieve origin from DB
        # May return None
        # Remark: An Origin can be loaded using loadObject() and
        # getObject(). The difference is that getObject() doesn't
        # load the arrivals hence is a *lot* faster.
        # origin = self.query().loadObject(DataModel.Origin.TypeInfo(), orid)
        origin = self.query().getObject(DataModel.Origin.TypeInfo(), orid)
        origin = DataModel.Origin.Cast(origin)
        if origin:
            self._stripOrigin(origin)
            self._removeCommentsIfRequested(origin)
        return origin

    def _loadMagnitude(self, orid):
        # Retrieve magnitude from DB
        # May return None
        obj = self.query().getObject(DataModel.Magnitude.TypeInfo(), orid)
        mag = DataModel.Magnitude.Cast(obj)
#       if mag:
#           self._stripMagnitude(mag)
#           self._removeCommentsIfRequested(mag)
        return mag

    def _loadFocalMechanism(self, fmid):
        # Retrieve FocalMechanism from DB
        # May return None
        obj = self.query().getObject(DataModel.FocalMechanism.TypeInfo(), fmid)
        fm = DataModel.FocalMechanism.Cast(obj)
        if fm:
            self.query().loadMomentTensors(fm)
            for i in xrange(fm.momentTensorCount()):
                mt = fm.momentTensor(i)
                self._stripMomentTensor(mt)
        return fm

    def run(self):
        evid = self.commandline().optionString("event")

        # Load event and preferred origin. This is the minimum
        # required info and if it can't be loaded, give up.
        event = self._loadEvent(evid)
        if event is None:
            raise ValueError, "unknown event '" + evid + "'"
        preferredOrigin = self._loadOrigin(event.preferredOriginID())
        if preferredOrigin is None:
            raise ValueError, "unknown origin '" + event.preferredOriginID() + "'"
        # take care of origin references
        while (event.originReferenceCount() > 0):
            event.removeOriginReference(0)
        if preferredOrigin:
            event.add(DataModel.OriginReference(preferredOrigin.publicID()))

        # try to read focal mechanism, moment tensor, moment magnitude and related origins
        momentTensor = momentMagnitude = derivedOrigin = triggeringOrigin = None   # default
        focalMechanism = self._loadFocalMechanism(event.preferredFocalMechanismID())
        if focalMechanism:
            if focalMechanism.triggeringOriginID():
                if event.preferredOriginID() != focalMechanism.triggeringOriginID():
                    triggeringOrigin = self._loadOrigin(focalMechanism.triggeringOriginID())
                else:
                    triggeringOrigin = preferredOrigin

            if focalMechanism.momentTensorCount() > 0:
                momentTensor = focalMechanism.momentTensor(0) # FIXME What if there is more than one MT?
                if momentTensor.derivedOriginID():
                    derivedOrigin = self._loadOrigin(momentTensor.derivedOriginID())
                if momentTensor.momentMagnitudeID():
                    momentMagnitude = self._loadMagnitude(momentTensor.momentMagnitudeID())

            # take care of FocalMechanism and related references
            if derivedOrigin:
                event.add(DataModel.OriginReference(derivedOrigin.publicID()))
            if triggeringOrigin:
                if event.preferredOriginID() != triggeringOrigin.publicID():
                    event.add(DataModel.OriginReference(triggeringOrigin.publicID()))
            while (event.focalMechanismReferenceCount() > 0):
                event.removeFocalMechanismReference(0)
            if focalMechanism:
                event.add(DataModel.FocalMechanismReference(focalMechanism.publicID()))
                self._removeCommentsIfRequested(focalMechanism)

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

        # populate EventParameters instance
        ep = DataModel.EventParameters()
        ep.add(event)
        ep.add(preferredOrigin)
        if focalMechanism:
            if triggeringOrigin:
                if triggeringOrigin is not preferredOrigin:
                    ep.add(triggeringOrigin)
            if derivedOrigin:
                if momentMagnitude:
                    derivedOrigin.add(momentMagnitude)
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
