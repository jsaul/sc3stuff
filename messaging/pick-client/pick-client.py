import sys, traceback, seiscomp3.Client

class PickClient(seiscomp3.Client.Application):

    def __init__(self):
        seiscomp3.Client.Application.__init__(self, len(sys.argv), sys.argv)
        self.setMessagingEnabled(True)
        self.setPrimaryMessagingGroup(seiscomp3.Communication.Protocol.LISTENER_GROUP)
        self.addMessagingSubscription("PICK")

    def doSomethingWithPick(self, obj):
        try:
            #######################################
            #### Include your custom code here ####
            print "publicID = %s" % obj.publicID()
            print "time     = %s" % obj.time().value()
            print "station  = %s" % obj.waveformID().stationCode()
            print "network  = %s" % obj.waveformID().networkCode()
            print
            #######################################
        except:
            info = traceback.format_exception(*sys.exc_info())
            for i in info: sys.stderr.write(i)

    def updateObject(self, parentID, object):
        # called if an updated object is received
        obj = seiscomp3.DataModel.Pick.Cast(object)
        if obj:
            name = obj.ClassName()
            print "received new %s object" % name
            self.doSomethingWithPick(obj)

    def addObject(self, parentID, obj):
        # called if a new object is received
        obj = seiscomp3.DataModel.Pick.Cast(obj)
        if obj:
            name = obj.ClassName()
            print "received new %s object" % name
            self.doSomethingWithPick(obj)

    def run(self):
        # needs not be re-implemented
        print "Hi! The %s is now running." % type(self).__name__
        return seiscomp3.Client.Application.run(self)

app = PickClient()
sys.exit(app())
