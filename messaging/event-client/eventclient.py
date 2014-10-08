import sys, traceback
from seiscomp3.Core import Time, TimeSpan
from seiscomp3.Client import Application
from seiscomp3.DataModel import Event, Origin, Magnitude, PublicObject
from seiscomp3.Communication import Protocol 
from seiscomp3.Logging import info, debug, warning, error


# Compound event with preferred origin/magnitude on board as well as some relevant state variables
class EventState:
    __slots__ = ("event", "origin", "magnitude", "preferredOriginID", "preferredMagnitudeID")

    def __init__(self, evt=None):
        self.event = evt
        self.origin = None
        self.magnitude = None
        self.preferredOriginID = None
        self.preferredMagnitudeID = None


class EventClient(Application):

    def __init__(self):
        Application.__init__(self, len(sys.argv), sys.argv)
        self.setMessagingEnabled(True)
        self.setDatabaseEnabled(True, True)
        self.setPrimaryMessagingGroup(Protocol.LISTENER_GROUP)
        self.addMessagingSubscription("EVENT")
        self.addMessagingSubscription("LOCATION")
        self.addMessagingSubscription("MAGNITUDE")
        self.setAutoApplyNotifierEnabled(True)

        # object buffers
        self._state = {}
        self._origin = {}
        self._magnitude = {}

        self._cleanupCounter = 0
        self._xdebug = False
        self._cleanup_interval = 3600.


    def cleanup(self):
        self._cleanupCounter += 1
        if self._cleanupCounter < 5:
            return
        info("before cleanup:")
        info("   _state               %d" % len(self._state))
        info("   _origin              %d" % len(self._origin))
        info("   _magnitude           %d" % len(self._magnitude))
        info("   public object count  %d" % (PublicObject.ObjectCount()))
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

        info("After cleanup:")
        info("   _state               %d" % len(self._state))
        info("   _origin              %d" % len(self._origin))
        info("   _magnitude           %d" % len(self._magnitude))
        info("   public object count  %d" % (PublicObject.ObjectCount()))
        info("-------------------------------")
        self._cleanupCounter = 0


    def changed_origin(self, event_id, previous_id, current_id):
        # to be implemented in a derived class
        raise NotImplementedError


    def changed_magnitude(self, event_id, previous_id, current_id):
        # to be implemented in a derived class
        raise NotImplementedError


    def _get_origin(self, oid):
        if oid not in self._origin:
             self._load_origin(oid)
        return self._origin[oid]


    def _get_magnitude(self, oid):
        if oid not in self._magnitude:
             self._load_magnitude(oid)
        return self._magnitude[oid]


    def _load(self, oid, tp):
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


    def _load_origin(self, oid):
        self._origin[oid] = self._load(oid, Origin)


    def _load_magnitude(self, oid):
        self._magnitude[oid] = self._load(oid, Magnitude)


    def _process_event(self, evt):
        evid = evt.publicID()

        if self._xdebug:
            debug("_process_event %s start" % evid)

        st = self._state[evid]
        previous_preferredOriginID = st.preferredOriginID
        previous_preferredMagnitudeID = st.preferredMagnitudeID

        # possibly updated preferredOriginID/preferredMagnitudeID
        preferredOriginID = evt.preferredOriginID()
        preferredMagnitudeID = evt.preferredMagnitudeID()

        info("%s preferredOriginID    %s  %s" % (evid, previous_preferredOriginID, preferredOriginID))
        info("%s preferredMagnitudeID %s  %s" % (evid, previous_preferredMagnitudeID, preferredMagnitudeID))


        # Test whether there have been any (for us!) relevant
        # changes in the event. We test for preferredOriginID
        # and preferredMagnitudeID.
        if preferredOriginID != previous_preferredOriginID:
            st.origin = self._get_origin(preferredOriginID)
            self.changed_origin(evid, previous_preferredOriginID, preferredOriginID)
            st.preferredOriginID = preferredOriginID

        if preferredMagnitudeID != previous_preferredMagnitudeID:
            st.magnitude = self._get_magnitude(preferredMagnitudeID)
            self.changed_magnitude(evid, previous_preferredMagnitudeID, preferredMagnitudeID)
            st.preferredMagnitudeID = preferredMagnitudeID

        self.cleanup()

        if self._xdebug:
            debug("_process_event %s end" % evid)


    def _process_origin(self, obj):
#       self.cleanup()
        pass # currently nothing to do here


    def _process_magnitude(self, obj):
#       self.cleanup()
        pass # currently nothing to do here


    def updateObject(self, parentID, updated):
        # called if an updated object is received
        for tp in [ Magnitude, Origin, Event ]:
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

        if self._xdebug:
            debug("updateObject end")


    def addObject(self, parentID, added):
        # called if a new object is received
        for tp in [ Magnitude, Origin, Event ]:
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

        if self._xdebug:
            debug("addObject end")
