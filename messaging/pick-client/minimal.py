import sys, seiscomp.client, seiscomp.datamodel

class PickClient(seiscomp.client.Application):
    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self,argc,argv)
        self.setMessagingEnabled(True)
        self.setLoggingToStdErr(True)
        self.addMessagingSubscription("PICK")

    def addObject(self, parentID, obj):
        pick = seiscomp.datamodel.Pick.Cast(obj)
        if pick:
            print("new pick %s" % pick.publicID())

app = PickClient(len(sys.argv), sys.argv)
app()
