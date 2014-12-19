from __future__ import print_function
import sys, traceback, seiscomp3.Client

def nslc(obj):
    n = obj.waveformID().networkCode()
    s = obj.waveformID().stationCode()
    l = obj.waveformID().locationCode()
    c = obj.waveformID().channelCode()
    return n,s,l,c


class PickClient(seiscomp3.Client.Application):

    def __init__(self):
        seiscomp3.Client.Application.__init__(self, len(sys.argv), sys.argv)
        self.setMessagingEnabled(True)
        self.setPrimaryMessagingGroup(seiscomp3.Communication.Protocol.LISTENER_GROUP)
        self.addMessagingSubscription("PICK")
        self.addMessagingSubscription("AMPLITUDE")

    def greeting(self):
        print("Hi! The %s is now running.\n" % type(self).__name__)

    def doSomethingWithPick(self, pick):
        try:
            #######################################
            #### Include your custom code here ####
            print("publicID =", pick.publicID())
            print("time     =", pick.time().value())
            print("n,s,l,c  =", nslc(pick))
            #######################################
        except:
            info = traceback.format_exception(*sys.exc_info())
            for i in info: sys.stderr.write(i)

    def doSomethingWithAmplitude(self, amplitude):
        try:
            #######################################
            #### Include your custom code here ####
            print("publicID =", amplitude.publicID())
            print("n,s,l,c  =", nslc(amplitude))
            print("type     =", amplitude.type())
            print("value    =", amplitude.amplitude().value())
            print("pickID   =", amplitude.pickID())
            #######################################
        except:
            info = traceback.format_exception(*sys.exc_info())
            for i in info: sys.stderr.write(i)

    def updateObject(self, parentID, obj):
        # called if an updated object is received
        pick = seiscomp3.DataModel.Pick.Cast(obj)
        if pick:
            # note that the object's ClassName is only accessible
            # *after* the cast
            print("received updated %s object" % pick.ClassName())
            self.doSomethingWithPick(pick)
            return
        amplitude = seiscomp3.DataModel.Amplitude.Cast(obj)
        if amplitude:
            print("received updated %s object" % amplitude.ClassName())
            self.doSomethingWithAmplitude(amplitude)
            return

    def addObject(self, parentID, obj):
        # called if a new object is received
        pick = seiscomp3.DataModel.Pick.Cast(obj)
        if pick:
            print("received new %s object" % pick.ClassName())
            self.doSomethingWithPick(pick)
            return
        amplitude = seiscomp3.DataModel.Amplitude.Cast(obj)
        if amplitude:
            print("received new %s object" % amplitude.ClassName())
            self.doSomethingWithAmplitude(amplitude)
            return

    def run(self):
        self.greeting()
        return seiscomp3.Client.Application.run(self)

if __name__ == "__main__":
    app = PickClient()
    sys.exit(app())
