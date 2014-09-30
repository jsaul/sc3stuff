import sys, traceback
from seiscomp3.Core import Time, TimeSpan
from seiscomp3.Client import Application
from seiscomp3.DataModel import Event, Origin, Magnitude, PublicObject
from seiscomp3.Communication import Protocol 
from seiscomp3.Logging import info, debug, error

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
        self._event = {}
        self._origin = {}
        self._magnitude = {}

        # event id is the key for these dicts
        self._preferredOriginID = {}
        self._preferredMagnitudeID = {}
        self._cleanupCounter = 0
        print>>sys.stderr, self.changed_origin


    def cleanup(self):
        self._cleanupCounter += 1
        if self._cleanupCounter < 5:
            return
        info("before cleanup:")
        info("   _event                 %d" % len(self._event))
        info("   _origin                %d" % len(self._origin))
        info("   _magnitude             %d" % len(self._magnitude))
        info("   _preferredOriginID     %d" % len(self._preferredOriginID))
        info("   _preferredMagnitudeID  %d" % len(self._preferredMagnitudeID))
        info("   public object count    %d" % (PublicObject.ObjectCount()))
        # we first remove those origins and magnitudes, which are
        # older than one hour and are not preferred anywhere.
        limit = Time.GMT() + TimeSpan(-360)
        preferredOriginIDs = []
        preferredMagnitudeIDs = []
        for oid in self._event:
            try:
                preferredOriginIDs.append(self._preferredOriginID[oid])
                preferredMagnitudeIDs.append(self._preferredMagnitudeID[oid])
            except KeyError: # FIXME
                continue
        originIDs = self._origin.keys()
        for oid in originIDs:
            if oid not in preferredOriginIDs:
                if self._origin[oid].creationInfo().creationTime() < limit:
                    del self._origin[oid]
        magnitudeIDs = self._magnitude.keys()
        for oid in magnitudeIDs:
            if oid not in preferredMagnitudeIDs:
                if self._magnitude[oid] is None:
                    # This should actually never happen!
                    error("Magnitude %s is None!" % oid)
                    del self._magnitude[oid]
                    continue
                if self._magnitude[oid].creationInfo().creationTime() < limit:
                    del self._magnitude[oid]

        # finally remove all remaining objects older than two hours
        limit = Time.GMT() + TimeSpan(-720)
        to_delete = []
        for evid in self._event:
            poid = self._preferredOriginID[evid]
            pmid = self._preferredMagnitudeID[evid]
            org = self._origin[poid]
            if org.time().value() > limit:
                continue # nothing to do with this event
            to_delete.append(evid)
        for evid in to_delete:
            del self._origin[self._preferredOriginID[evid]]
            del self._magnitude[self._preferredMagnitudeID[evid]]
            del self._preferredOriginID[evid]
            del self._preferredMagnitudeID[evid]
            del self._event[evid]

        info("After cleanup:")
        info("   _event                 %d" % len(self._event))
        info("   _origin                %d" % len(self._origin))
        info("   _magnitude             %d" % len(self._magnitude))
        info("   _preferredOriginID     %d" % len(self._preferredOriginID))
        info("   _preferredMagnitudeID  %d" % len(self._preferredMagnitudeID))
        info("   public object count    %d" % (PublicObject.ObjectCount()))
        info("-------------------------------")
        self._cleanupCounter = 0

    def changed_origin(self, event_id, previous_id, current_id):
        # to be implemented in a derived class
        raise NotImplementedError


    def changed_magnitude(self, event_id, previous_id, current_id):
        # to be implemented in a derived class
        raise NotImplementedError


    def _process_event(self, obj):
        debug("_process_event %s start" % obj.publicID())

        try:
            previous_preferredOriginID = self._preferredOriginID[obj.publicID()]
        except KeyError:
            previous_preferredOriginID = None

        try:
            previous_preferredMagnitudeID = self._preferredMagnitudeID[obj.publicID()]
        except KeyError:
            previous_preferredMagnitudeID = None

        preferredOriginID = obj.preferredOriginID()
        preferredMagnitudeID = obj.preferredMagnitudeID()

        # check if we have the origin/magnitude we have set preferred
        if preferredOriginID not in self._origin:
            self._load_origin(preferredOriginID)

        if preferredMagnitudeID not in self._magnitude:
            self._load_magnitude(preferredMagnitudeID)

        # update preferredOriginID and preferredMagnitudeID
        self._preferredOriginID[obj.publicID()] = preferredOriginID
        self._preferredMagnitudeID[obj.publicID()] = preferredMagnitudeID


        # Test, whether there has been any (for us!) relevant
        # changes in the event. We test for preferredOriginID
        # and preferredMagnitudeID.
        if previous_preferredOriginID:
            if preferredOriginID != previous_preferredOriginID:
                self.changed_origin(obj.publicID(), previous_preferredOriginID, preferredOriginID)

        if previous_preferredMagnitudeID:
            if preferredMagnitudeID != previous_preferredMagnitudeID:
                self.changed_magnitude(obj.publicID(), previous_preferredMagnitudeID, preferredMagnitudeID)
        # TODO: Do some real work here :-)
        debug("_process_event %s end" % obj.publicID())


    def _process_origin(self, obj):
        pass # currently nothing to do here


    def _process_magnitude(self, obj):
        pass # currently nothing to do here


    def _load(self, oid, tp):
        tmp = tp.Cast(self.query().loadObject(tp.TypeInfo(), oid))
        if tmp:
            debug("loaded %s %s" % (tmp.ClassName(), oid))
        return tmp


    def _load_event(self, oid):
        self._event[oid] = self._load(oid, Event)


    def _load_origin(self, oid):
        self._origin[oid] = self._load(oid, Origin)


    def _load_magnitude(self, oid):
        self._magnitude[oid] = self._load(oid, Magnitude)


    def process(self, obj):
        debug("process start")
        try:
            if obj.ClassName() == "Event":
                obj = self._event[obj.publicID()]
                self._process_event(obj)
            elif obj.ClassName() == "Origin":
                obj = self._origin[obj.publicID()]
                self._process_origin(obj)
            elif obj.ClassName() == "Magnitude":
                obj = self._magnitude[obj.publicID()]
                self._process_magnitude(obj)
        except:
            info = traceback.format_exception(*sys.exc_info())
            for i in info: sys.stderr.write(i)
        debug("process end")
                

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

        debug("updateObject start %s  oid=%s" % (obj.ClassName(), oid))

        # our utility may have been offline during addObject, so we
        # need to check whether this is the first time that we see
        # this object. If that is the case, we load that object from
        # the database in order to be sure that we are working with
        # the complete object.
        if tp is Event:
            debug("updateObject Event")
            if oid in self._event:
                # *update* the existing instance - do *not* overwrite it!
                self._event[oid].assign(obj)
            else:
                self._load_event(oid)
        elif tp is Origin:
            debug("updateObject Origin")
            if oid in self._origin:
                # *update* the existing instance - do *not* overwrite it!
                self._origin[oid].assign(obj)
            else:
                self._load_origin(oid)
        elif tp is Magnitude:
            debug("updateObject Magnitude")
            if oid in self._magnitude:
                # *update* the existing instance - do *not* overwrite it!
                self._magnitude[oid].assign(obj)
            else:
                self._load_magnitude(oid)

        self.process(obj)
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
            if oid not in self._event:
                self._event[oid] = obj
            else:
                error("event %s already in self._event" % oid)
        elif tp is Origin:
            if oid not in self._origin:
                self._origin[oid] = obj
            else:
                error("origin %s already in self._origin" % oid)
        elif tp is Magnitude:
            if oid not in self._magnitude:
                self._magnitude[oid] = obj
            else:
                error("magnitude %s already in self._magnitude" % oid)

        self.process(obj)
        debug("addObject end")
