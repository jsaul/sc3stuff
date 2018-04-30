from __future__ import print_function
import sys, seiscomp3.Client, seiscomp3.DataModel

class PickClient(seiscomp3.Client.Application):
    def __init__(self, argc, argv):
        seiscomp3.Client.Application.__init__(self,argc,argv)
        self.setMessagingEnabled(True)
        self.setLoggingToStdErr(True)
        self.addMessagingSubscription("PICK")

    def addObject(self, parentID, obj):
        pick = seiscomp3.DataModel.Pick.Cast(obj)
        if pick:
            print("new pick", pick.publicID())

app = PickClient(len(sys.argv), sys.argv)
app()
