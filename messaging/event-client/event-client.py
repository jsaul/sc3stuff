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


    def _process_event(self, obj):
        print "_process_event", obj.publicID()

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
                print "event %s: CHANGED preferredOriginID" % obj.publicID()
                print "    from", previous_preferredOriginID
                print "      to", preferredOriginID

        if previous_preferredMagnitudeID:
            if preferredMagnitudeID != previous_preferredMagnitudeID:
                print "event %s: CHANGED preferredMagnitudeID" % obj.publicID()
                print "    from", previous_preferredMagnitudeID
                print "      to", preferredMagnitudeID
        # TODO: Do some real work here :-)


    def _process_origin(self, obj):
        oid = obj.publicID()
        print "_process_origin", oid

    def _process_magnitude(self, obj):
        oid = obj.publicID()
        print "_process_magnitude", oid

    def _load_event(self, oid):
        tmp = Event.Cast(self.query().loadObject(Event.TypeInfo(), oid))
        if tmp:
            print "loaded event %s from db" % oid
        self._event[oid] = tmp

    def _load_origin(self, oid):
        tmp = Origin.Cast(self.query().loadObject(Origin.TypeInfo(), oid))
        if tmp:
            print "loaded origin %s from db" % oid
        self._origin[oid] = tmp

    def _load_magnitude(self, oid):
        tmp = Magnitude.Cast(self.query().loadObject(Magnitude.TypeInfo(), oid))
        if tmp:
            print "loaded magnitude %s from db" % oid
        self._magnitude[oid] = tmp

    def process(self, obj):
        try:
            if obj.ClassName() == "Event":
                obj = self._event[obj.publicID()]
                self._process_event(obj)
            elif obj.ClassName() == "Origin":
                obj = self._preferredOrigin[obj.publicID()]
                self._process_origin(obj)
            elif obj.ClassName() == "Magnitude":
                obj = self._preferredMagnitude[obj.publicID()]
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

        print "UPD %-15s object %s   parent: %s" % (obj.ClassName(), oid, parentID)
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

        print "NEW %-15s object %s   parent: %s" % (obj.ClassName(), oid, parentID)
        self.process(obj)


app = EventClient()
sys.exit(app())
