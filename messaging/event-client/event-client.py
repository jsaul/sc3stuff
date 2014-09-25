import sys, traceback
from seiscomp3.Client import Application
from seiscomp3.DataModel import Event, Origin, Magnitude
from seiscomp3.Communication import Protocol 


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

        # event id is the key for these dicts:
        self._event = {}
        self._preferredOriginID = {}
        self._preferredMagnitudeID = {}

        self._preferredOrigin = {}
        self._preferredMagnitude = {}

        # temporary buffer for non-preferred magnitudes
        self._origin = {}
        self._magnitude = {}


    def log(self, msg):
        sys.stdout.write("%s\n" % msg)


    def changed_origin(self, event_id, previous_id, current_id):
        self.log("event %s: CHANGED preferredOriginID" % event_id)
        self.log("    from %s" % previous_id)
        self.log("      to %s" % current_id)


    def changed_magnitude(self, event_id, previous_id, current_id):
        self.log("event %s: CHANGED preferredMagnitudeID" % event_id)
        self.log("    from %s" % previous_id)
        self.log("      to %s" % current_id)


    def _process_event(self, obj):
        self.log("_process_event %s" % obj.publicID())

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


    def _process_origin(self, obj):
        oid = obj.publicID()
        self.log("_process_origin %s" % oid)


    def _process_magnitude(self, obj):
        oid = obj.publicID()
        self.log("_process_magnitude %s" % oid)


    def _load_event(self, oid):
        tmp = Event.Cast(self.query().loadObject(Event.TypeInfo(), oid))
        if tmp:
            self.log("loaded event %s" % oid)
        self._event[oid] = tmp


    def _load_origin(self, oid):
        tmp = Origin.Cast(self.query().loadObject(Origin.TypeInfo(), oid))
        if tmp:
            self.log("loaded origin %s" % oid)
        self._origin[oid] = tmp


    def _load_magnitude(self, oid):
        tmp = Magnitude.Cast(self.query().loadObject(Magnitude.TypeInfo(), oid))
        if tmp:
            self.log("loaded magnitude %s" % oid)
        self._magnitude[oid] = tmp


    def process(self, obj):
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
                

    def updateObject(self, parentID, updated):
        # called if an updated object is received
        for tp in [ Magnitude, Origin, Event ]:
            # try to convert to any of the above types
            obj = tp.Cast(updated)
            if not obj:
                continue

            oid = obj.publicID()

            # our utility may have been offline during addObject, so we need to check
            # whether this is the first time that we see this object.
            # If that is the case, we load that object from the database in order to
            # be sure that we are working with the complete object.
            if tp is Event:
                if oid in self._event:
                    # *update* the existing instance - do *not* overwrite it!
                    self._event[oid].assign(obj)
                else:
                    self._load_event(oid)
            elif tp is Origin:
                if oid in self._origin:
                    # *update* the existing instance - do *not* overwrite it!
                    self._origin[oid].assign(obj)
                else:
                    self._load_origin(oid)
            elif tp is Magnitude:
                if oid in self._magnitude:
                    # *update* the existing instance - do *not* overwrite it!
                    self._magnitude[oid].assign(obj)
                else:
                    self._load_magnitude(oid)
            break

        if not obj: return # probably other type

        self.log("UPD %-15s object %s   parent: %s" % (obj.ClassName(), oid, parentID))
        self.process(obj)


    def addObject(self, parentID, object):
        # called if a new object is received
        for tp in [ Magnitude, Origin, Event ]:
            obj = tp.Cast(object)
            if not obj:
                continue

            oid = obj.publicID()

            if tp is Event:
                assert oid not in self._event
                self._event[oid] = obj
            elif tp is Origin:
                assert oid not in self._origin
                self._origin[oid] = obj
            elif tp is Magnitude:
                assert oid not in self._magnitude
                self._magnitude[oid] = obj

        if not obj: return # probably other type

        self.log("NEW %-15s object %s   parent: %s" % (obj.ClassName(), oid, parentID))
        self.process(obj)


app = EventClient()
sys.exit(app())
