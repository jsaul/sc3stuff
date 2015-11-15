from __future__ import print_function
import sys
from seiscomp3.Core import Time, TimeSpan
from seiscomp3.Client import Application
from seiscomp3.DataModel import Event, Origin, Magnitude, PublicObject, FocalMechanism
from seiscomp3.Communication import Protocol 
import seiscomp3.Logging

info    = seiscomp3.Logging.info
debug   = seiscomp3.Logging.info # XXX
warning = seiscomp3.Logging.warning
error   = seiscomp3.Logging.error


# Compound event with preferred origin/magnitude on board as well as some relevant state variables
class EventState:
    __slots__ = ("event", "origin", "magnitude", "focalmechanism", "preferredOriginID", "preferredMagnitudeID", "preferredFocalMechanismID")

    def __init__(self, evt=None):
        self.event = evt
        self.origin = None
        self.magnitude = None
        self.focalmechanism = None
        self.preferredOriginID = None
        self.preferredMagnitudeID = None
        self.preferredFocalMechanismID = None


class EventClient(Application):

    def __init__(self, argc, argv):
        Application.__init__(self, argc, argv)
        self.setMessagingEnabled(True)
        self.setDatabaseEnabled(True, True)
        self.addMessagingSubscription("EVENT")
        self.addMessagingSubscription("LOCATION")
        self.addMessagingSubscription("MAGNITUDE")
        self.addMessagingSubscription("FOCMECH")
        self.setAutoApplyNotifierEnabled(True)

        # object buffers
        self._state = {}
        self._origin = {}
        self._magnitude = {}
        self._focalmechanism = {}

        self._cleanupCounter = 0
        self._xdebug = False
        self._cleanup_interval = 3600.


    def cleanup(self):
        self._cleanupCounter += 1
        if self._cleanupCounter < 5:
            return
        debug("before cleanup:")
        debug("   _state               %d" % len(self._state))
        debug("   _origin              %d" % len(self._origin))
        debug("   _magnitude           %d" % len(self._magnitude))
        debug("   _focalmechanism      %d" % len(self._focalmechanism))
        debug("   public object count  %d" % (PublicObject.ObjectCount()))
        # we first remove those origins and magnitudes, which are
        # older than one hour and are not preferred anywhere.
        limit = Time.GMT() + TimeSpan(-self._cleanup_interval)

        originIDs = self._origin.keys()
        for oid in originIDs:
            if self._origin[oid].creationInfo().creationTime() < limit:
                del self._origin[oid]

        magnitudeIDs = self._magnitude.keys()
        for oid in magnitudeIDs:
            if self._magnitude[oid] is None:
                # This should actually never happen!
                error("Magnitude %s is None!" % oid)
                del self._magnitude[oid]
                continue
            if self._magnitude[oid].creationInfo().creationTime() < limit:
                del self._magnitude[oid]

        focalmechanismIDs = self._focalmechanism.keys()
        for oid in focalmechanismIDs:
            if self._focalmechanism[oid].creationInfo().creationTime() < limit:
                del self._focalmechanism[oid]

        # finally remove all remaining objects older than two hours
        limit = Time.GMT() + TimeSpan(-2*self._cleanup_interval)
        to_delete = []
        for evid in self._state:
            org = self._state[evid].origin
            if org and org.time().value() > limit:
                continue # nothing to do with this event
            to_delete.append(evid)
        for evid in to_delete:
            del self._state[evid]

        debug("After cleanup:")
        debug("   _state               %d" % len(self._state))
        debug("   _origin              %d" % len(self._origin))
        debug("   _magnitude           %d" % len(self._magnitude))
        debug("   _focalmechanism      %d" % len(self._focalmechanism))
        debug("   public object count  %d" % (PublicObject.ObjectCount()))
        debug("-------------------------------")
        self._cleanupCounter = 0


    def changed_origin(self, event_id, previous_id, current_id):
        # to be implemented in a derived class
        raise NotImplementedError


    def changed_magnitude(self, event_id, previous_id, current_id):
        # to be implemented in a derived class
        raise NotImplementedError


    def changed_focalmechanism(self, event_id, previous_id, current_id):
        # to be implemented in a derived class
        raise NotImplementedError


    def _get_origin(self, oid):
        if oid not in self._origin:
             self._load_origin(oid)
        if oid in self._origin:
            return self._origin[oid]


    def _get_magnitude(self, oid):
        if oid not in self._magnitude:
             self._load_magnitude(oid)
        if oid in self._magnitude:
            return self._magnitude[oid]


    def _get_focalmechanism(self, oid):
        if oid not in self._focalmechanism:
             self._load_focalmechanism(oid)
        if oid in self._focalmechanism:
            return self._focalmechanism[oid]


    def _load(self, oid, tp):
        assert oid is not None
        debug("trying to load %s %s" % (str(tp), oid))
        tmp = tp.Cast(self.query().loadObject(tp.TypeInfo(), oid))
        if tmp:
            debug("loaded %s %s" % (tmp.ClassName(), oid))
        return tmp


    def _load_event(self, oid):
        evt = self._load(oid, Event)
        self._state[oid] = EventState(evt)
        # if we do this here, then we override the preferred* here and are not able to detect the difference!
        self._state[oid].origin = self._get_origin(evt.preferredOriginID())
        self._state[oid].magnitude = self._get_magnitude(evt.preferredMagnitudeID())
        self._state[oid].focalmechanism = self._get_focalmechanism(evt.preferredFocalMechanismID())


    def _load_origin(self, oid):
        self._origin[oid] = self._load(oid, Origin)


    def _load_magnitude(self, oid):
        self._magnitude[oid] = self._load(oid, Magnitude)


    def _load_focalmechanism(self, oid):
        obj = self._load(oid, FocalMechanism)
        if obj:
            self._focalmechanism[oid] = obj
            warning("focalmechanism ID %s" % obj.publicID())
        else:
            warning("focalmechanism is None")


    def _process_event(self, evt):
        evid = evt.publicID()

        if self._xdebug:
            debug("_process_event %s start" % evid)

        st = self._state[evid]
        previous_preferredOriginID = st.preferredOriginID
        previous_preferredMagnitudeID = st.preferredMagnitudeID
        previous_preferredFocalMechanismID = st.preferredFocalMechanismID

        # possibly updated preferredOriginID/preferredMagnitudeID
        preferredOriginID = evt.preferredOriginID()
        preferredMagnitudeID = evt.preferredMagnitudeID()
        preferredFocalMechanismID = evt.preferredFocalMechanismID()
        if not preferredOriginID:
            preferredOriginID = None
        if not preferredMagnitudeID:
            preferredMagnitudeID = None
        if not preferredFocalMechanismID:
            preferredFocalMechanismID = None

        info("%s preferredOriginID         %s  %s" % (evid, previous_preferredOriginID, preferredOriginID))
        info("%s preferredMagnitudeID      %s  %s" % (evid, previous_preferredMagnitudeID, preferredMagnitudeID))
        info("%s preferredFocalMechanismID %s  %s" % (evid, previous_preferredFocalMechanismID, preferredFocalMechanismID))


        # Test whether there have been any (for us!) relevant
        # changes in the event. We test for preferredOriginID,
        # preferredMagnitudeID and preferredFocalMechanismID
        if preferredOriginID is not None and preferredOriginID != previous_preferredOriginID:
            st.origin = self._get_origin(preferredOriginID)
            self.changed_origin(evid, previous_preferredOriginID, preferredOriginID)
            st.preferredOriginID = preferredOriginID

        if preferredMagnitudeID is not None and preferredMagnitudeID != previous_preferredMagnitudeID:
            st.magnitude = self._get_magnitude(preferredMagnitudeID)
            self.changed_magnitude(evid, previous_preferredMagnitudeID, preferredMagnitudeID)
            st.preferredMagnitudeID = preferredMagnitudeID

        if preferredFocalMechanismID is not None and preferredFocalMechanismID != previous_preferredFocalMechanismID:
            st.focalmechanism = self._get_focalmechanism(preferredFocalMechanismID)
            self.changed_focalmechanism(evid, previous_preferredFocalMechanismID, preferredFocalMechanismID)
            st.preferredFocalMechanismID = preferredFocalMechanismID

        self.cleanup()

        if self._xdebug:
            debug("_process_event %s end" % evid)


    def _process_origin(self, obj):
#       self.cleanup()
        pass # currently nothing to do here


    def _process_magnitude(self, obj):
#       self.cleanup()
        pass # currently nothing to do here


    def _process_focalmechanism(self, obj):
#       self.cleanup()
        pass # currently nothing to do here


    def updateObject(self, parentID, updated):
        # called if an updated object is received
        for tp in [ Magnitude, Origin, Event, FocalMechanism ]:
            # try to convert to any of the above types
            obj = tp.Cast(updated)
            if obj:
                break

        if not obj:
            return

        oid = obj.publicID()

        if self._xdebug:
            debug("updateObject start %s  oid=%s" % (obj.ClassName(), oid))

        # our utility may have been offline during addObject, so we
        # need to check whether this is the first time that we see
        # this object. If that is the case, we load that object from
        # the database in order to be sure that we are working with
        # the complete object.
        if tp is Event:
            if oid in self._state:
                # *update* the existing instance - do *not* overwrite it!
                self._state[oid].event.assign(obj)
            else:
                self._load_event(oid)
            self._process_event(obj)

        elif tp is Origin:
            if oid in self._origin:
                # *update* the existing instance - do *not* overwrite it!
                self._origin[oid].assign(obj)
            else:
                self._load_origin(oid)
            self._process_origin(obj)

        elif tp is Magnitude:
            if oid in self._magnitude:
                # *update* the existing instance - do *not* overwrite it!
                self._magnitude[oid].assign(obj)
            else:
                self._load_magnitude(oid)
            self._process_magnitude(obj)

        elif tp is FocalMechanism:
            if oid in self._focalmechanism:
                # *update* the existing instance - do *not* overwrite it!
                self._focalmechanism[oid].assign(obj)
            else:
                self._load_focalmechanism(oid)
            self._process_focalmechanism(obj)

        if self._xdebug:
            debug("updateObject end")


    def addObject(self, parentID, added):
        # called if a new object is received
        for tp in [ Magnitude, Origin, Event, FocalMechanism ]:
            obj = tp.Cast(added)
            if obj:
                break

        if not obj:
            return

        oid = obj.publicID()

        if self._xdebug:
            debug("addObject start %s  oid=%s" % (obj.ClassName(), oid))

        tmp = PublicObject.Find(oid)
        if not tmp:
            error("PublicObject.Find failed on %s %s" % (tmp.ClassName(), oid))
            return
        # can we get rid of this?
        tmp = tp.Cast(tmp)
        tmp.assign(obj)
        obj = tmp

        if tp is Event:
            if oid not in self._state:
                self._state[oid] = EventState(obj)
                self._state[oid].origin = self._get_origin(obj.preferredOriginID())
                self._state[oid].magnitude = self._get_magnitude(obj.preferredMagnitudeID())
            else:
                error("event %s already in self._state" % oid)
            self._process_event(obj)

        elif tp is Origin:
            if oid not in self._origin:
                self._origin[oid] = obj
            else:
                error("origin %s already in self._origin" % oid)
            self._process_origin(obj)

        elif tp is Magnitude:
            if oid not in self._magnitude:
                self._magnitude[oid] = obj
            else:
                error("magnitude %s already in self._magnitude" % oid)
            self._process_magnitude(obj)

        elif tp is FocalMechanism:
            if oid not in self._focalmechanism:
                self._focalmechanism[oid] = obj
            else:
                error("focalmechanism %s already in self._focalmechanism" % oid)
            self._process_focalmechanism(obj)

        if self._xdebug:
            debug("addObject end")


class EventWatch(EventClient):

    def __init__(self, argc, argv):
        EventClient.__init__(self, argc, argv)

    def _print(self, evid):
        s = self._state[evid]
        org = s.origin
        mag = s.magnitude
        foc = s.focalmechanism
        print("EVT %s" % evid)
        if not org:
            return
        print("ORG %s" % (org.time().value()))
        if not mag:
            return
        print("MAG %.2f %s" % (mag.magnitude().value(), mag.type()))
        if not foc:
            return
        nmt = foc.momentTensorCount()
        print("FOC %d" % (nmt))

        try:
            print("  misfit: %.3f" % (mt.misfit()))
        except:
            pass

        try:
            print("  azigap: %.1f" % (mt.azimuthalGap()))
        except:
            pass
            
        for i in xrange(foc.momentTensorCount()):
            mt = foc.momentTensor(i)
            try:
                print("  clvd %.2f" % (mt.clvd()))
            except:
                pass
            try:
                print("  iso  %.2f" % (mt.iso()))
            except:
                pass
#           print("  %s" % (mt.momentMagnitudeID()))
            mw = Magnitude.Find(mt.momentMagnitudeID())
            mw = Magnitude.Cast(mw)
            if mw:
                print("  MW %.2f %s" % (mw.magnitude().value(), mw.type()))
#           print("  dataUsedCount            %d" % mt.dataUsedCount())
            totalStationWeight = 0.
            totalComponentWeight = 0.
            for k in xrange(mt.momentTensorStationContributionCount()):
                sc = mt.momentTensorStationContribution(k)
                totalStationWeight += sc.weight()
                for j in xrange(sc.momentTensorComponentContributionCount()):
                    cc = sc.momentTensorComponentContribution(j)
                    totalComponentWeight += cc.weight()
            print("  stationContribution %.2f" % totalStationWeight)
            print("  componentContribution %.2f" % totalComponentWeight)

            # this could be the centroid location
            dorg = Origin.Find(mt.derivedOriginID())
            if dorg:
                print("  time  %s" % (dorg.time().value()))
                print("  lat   %.2f" % dorg.latitude().value())
                print("  lon   %.2f" % dorg.longitude().value())
                print("  dep   %.1f" % dorg.depth().value())
            else:
                print("  no origin found for derivedOriginID() '%s'" % mt.derivedOriginID())

    def changed_origin(self, event_id, previous_id, current_id):
        debug("EventWatch.changed_origin")
        debug("event %s: CHANGED preferredOriginID" % event_id)
        debug("    from %s" % previous_id)
        debug("      to %s" % current_id)
        self._print(event_id)

    def changed_magnitude(self, event_id, previous_id, current_id):
        debug("EventWatch.changed_magnitude")
        debug("event %s: CHANGED preferredMagnitudeID" % event_id)
        debug("    from %s" % previous_id)
        debug("      to %s" % current_id)
        self._print(event_id)

    def changed_focalmechanism(self, event_id, previous_id, current_id):
        debug("EventWatch.changed_focalmechanism")
        debug("event %s: CHANGED preferredFocalMechanismID" % event_id)
        debug("    from %s" % previous_id)
        debug("      to %s" % current_id)
        self._print(event_id)

if __name__ == "__main__":
    app = EventWatch(len(sys.argv), sys.argv)
    sys.exit(app())

