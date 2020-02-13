#!/usr/bin/env seiscomp-python
#
# Dump origin, magnitude and moment tensor information for an
# event to SeisComP XML.
#
# Could be invoked in a pipeline like:
#
#  python scxmldump-public-with-mt.py --debug -d "$db" -E "$evid" |
#  sccnv -f -i trunk:- -o qml1.2:"$evid-mt.QuakeML"
#
# The above will dump the event information to QuakeML 1.2

import sys
import seiscomp.client, seiscomp.datamodel, seiscomp.io
import sc3stuff.util


class MomentTensorDumper(seiscomp.client.Application):

    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, False)

    def createCommandLineDescription(self):
        seiscomp.client.Application.createCommandLineDescription(self)
        self.commandline().addGroup("Dump")
        self.commandline().addStringOption("Dump", "event,E", "compute a time window from the event")
        self.commandline().addOption("Dump", "include-full-creation-info,I", "include full creation info")
        self.commandline().addOption("Dump", "all-magnitudes,m", "include network magnitudes of all available types, not only the preferred magnitude")
        self.commandline().addOption("Dump", "comments,c", "include comments")

    def _removeCommentsIfRequested(self, obj):
        if obj is not None and not self.commandline().hasOption("comments"):
            while obj.commentCount() > 0:
                obj.removeComment(0)

    def _stripOrigin(self, org):
        # Remove all arrivals and magnitudes from the origin.
        #
        # If the origin was loaded using query().getObject()
        # this is actually not needed.
        while org.arrivalCount() > 0:
            org.removeArrival(0)
        while org.magnitudeCount() > 0:
            org.removeMagnitude(0)
        while org.stationMagnitudeCount() > 0:
            org.removeStationMagnitude(0)

    def _stripCreationInfo(self, obj):
        ## strip creationInfo entirely:
        #empty = seiscomp.datamodel.CreationInfo()
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
        #
        # Returns either the event instance
        # or None if event could not be loaded.
        #
        # use loadObject() because we want the complete descriptions
        event = self.query().loadObject(seiscomp.datamodel.Event.TypeInfo(), evid)
        event = seiscomp.datamodel.Event.Cast(event)
        if event:
            if event.eventDescriptionCount() == 0:
                self.query().loadEventDescriptions(event)
            self._removeCommentsIfRequested(event)
        return event

    def _loadOrigin(self, orid):
        # Retrieve origin from DB
        #
        # Returns either the origin instance
        # or None if origin could not be loaded.
        #
        # Remark: An Origin can be loaded using loadObject() and
        # getObject(). The difference is that getObject() doesn't
        # load the arrivals hence is a *lot* faster.
        # origin = self.query().loadObject(seiscomp.datamodel.Origin.TypeInfo(), orid)
        origin = self.query().getObject(seiscomp.datamodel.Origin.TypeInfo(), orid)
        origin = seiscomp.datamodel.Origin.Cast(origin)
        if origin:
            self._stripOrigin(origin)
            self._removeCommentsIfRequested(origin)
        return origin

    def _loadMagnitude(self, orid):
        # Retrieve magnitude from DB
        # 
        # Returns either the Magnitude instance
        # or None if Magnitude could not be loaded.
        obj = self.query().getObject(seiscomp.datamodel.Magnitude.TypeInfo(), orid)
        mag = seiscomp.datamodel.Magnitude.Cast(obj)
#       if mag:
#           self._stripMagnitude(mag)
#           self._removeCommentsIfRequested(mag)
        return mag

    def _loadFocalMechanism(self, fmid):
        # Retrieve FocalMechanism from DB
        # 
        # Returns either the FocalMechanism instance
        # or None if FocalMechanism could not be loaded.
        #
        obj = self.query().getObject(seiscomp.datamodel.FocalMechanism.TypeInfo(), fmid)
        fm = seiscomp.datamodel.FocalMechanism.Cast(obj)
        if fm:
            self.query().loadMomentTensors(fm)
            for i in range(fm.momentTensorCount()):
                mt = fm.momentTensor(i)
                self._stripMomentTensor(mt)
        return fm

    def run(self):
        ep = seiscomp.datamodel.EventParameters()
        evids = self.commandline().optionString("event").split()
        for evid in evids:
            # each of the specified events is added to the
            # EventParameters instance
            self.do_one_event(evid, ep)

        # finally dump event parameters as formatted XML archive to stdout
        sc3stuff.util.writeEventParametersToXML(ep)

        del ep
        return True

    def do_one_event(self, evid, ep):
        """
        Things to do:
        * load event
        * load preferred origin without arrivals
        * load at least the preferred magnitude if available, all magnitudes if requested
        * load focal mechanism incl. moment tensor depending on availability, incl. Mw from derived origin
        """

        # Load event and preferred origin. This is the minimum
        # required info and if it can't be loaded, give up.
        event = self._loadEvent(evid)
        if event is None:
            raise ValueError("unknown event '" + evid + "'")
        preferredOrigin = self._loadOrigin(event.preferredOriginID())
        if preferredOrigin is None:
            raise ValueError("unknown origin '" + event.preferredOriginID() + "'")

        # take care of origin references and leave just one for the preferred origin
        while (event.originReferenceCount() > 0):
            event.removeOriginReference(0)
        if preferredOrigin:
            event.add(seiscomp.datamodel.OriginReference(preferredOrigin.publicID()))
        if self.commandline().hasOption("comments"):
            self.query().loadComments(preferredOrigin)

        # load all magnitudes for preferredOrigin
        if self.commandline().hasOption("all-magnitudes"):
            self.query().loadMagnitudes(preferredOrigin)
            magnitudes = [ preferredOrigin.magnitude(i) for i in range(preferredOrigin.magnitudeCount()) ]
        else:
            magnitudes = []
        if event.preferredMagnitudeID():
            # try to load from memory
            for mag in magnitudes:
                if mag.publicID() == event.preferredMagnitudeID():
                    preferredMagnitude = mag
                    break
#           preferredMagnitude = seiscomp.datamodel.Magnitude.Find(event.preferredMagnitudeID())
            else:
                # try to load it from database
                preferredMagnitude = self._loadMagnitude(event.preferredMagnitudeID())
        else:
            preferredMagnitude = None

        # try to load focal mechanism, moment tensor, moment magnitude and related origins
        momentTensor = momentMagnitude = derivedOrigin = triggeringOrigin = None   # default
        focalMechanism = self._loadFocalMechanism(event.preferredFocalMechanismID())
        if focalMechanism:
            if focalMechanism.triggeringOriginID():
                if event.preferredOriginID() == focalMechanism.triggeringOriginID():
                    triggeringOrigin = preferredOrigin
                else:
                    triggeringOrigin = self._loadOrigin(focalMechanism.triggeringOriginID())

            if focalMechanism.momentTensorCount() > 0:
                momentTensor = focalMechanism.momentTensor(0) # FIXME What if there is more than one MT?
                if momentTensor.derivedOriginID():
                    derivedOrigin = self._loadOrigin(momentTensor.derivedOriginID())
                if momentTensor.momentMagnitudeID():
                    if momentTensor.momentMagnitudeID() == event.preferredMagnitudeID():
                        momentMagnitude = preferredMagnitude
                    else:
                        momentMagnitude = self._loadMagnitude(momentTensor.momentMagnitudeID())

            # take care of FocalMechanism and related references
            if derivedOrigin:
                event.add(seiscomp.datamodel.OriginReference(derivedOrigin.publicID()))
            if triggeringOrigin:
                if event.preferredOriginID() != triggeringOrigin.publicID():
                    event.add(seiscomp.datamodel.OriginReference(triggeringOrigin.publicID()))
            while (event.focalMechanismReferenceCount() > 0):
                event.removeFocalMechanismReference(0)
            if focalMechanism:
                event.add(seiscomp.datamodel.FocalMechanismReference(focalMechanism.publicID()))
                self._removeCommentsIfRequested(focalMechanism)

        # strip creation info
        if not self.commandline().hasOption("include-full-creation-info"):
            self._stripCreationInfo(event)
            if focalMechanism:
                self._stripCreationInfo(focalMechanism)
                for i in range(focalMechanism.momentTensorCount()):
                    self._stripCreationInfo(focalMechanism.momentTensor(i))
            for org in [ preferredOrigin, triggeringOrigin, derivedOrigin ]:
                if org is not None:
                    self._stripCreationInfo(org)
                    for i in range(org.magnitudeCount()):
                        self._stripCreationInfo(org.magnitude(i))

        # populate EventParameters instance
        ep.add(event)
        if preferredMagnitude and preferredMagnitude is not momentMagnitude:
            preferredOrigin.add(preferredMagnitude)
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


def main():
    argv = sys.argv
    argc = len(argv)
    app = MomentTensorDumper(argc, argv)
    app()

if __name__ == "__main__":
    main()
