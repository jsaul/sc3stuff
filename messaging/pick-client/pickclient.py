import sys, seiscomp.client, seiscomp.datamodel

def nslc(obj):
    n = obj.waveformID().networkCode()
    s = obj.waveformID().stationCode()
    l = obj.waveformID().locationCode()
    c = obj.waveformID().channelCode()
    return n,s,l,c


class PickClient(seiscomp.client.Application):

    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(True)
        self.addMessagingSubscription("PICK")
        self.addMessagingSubscription("AMPLITUDE")

    def greeting(self):
        print("Hi! The %s is now running.\n" % type(self).__name__)

    def doSomethingWithPick(self, pick):
        #######################################
        #### Include your custom code here ####
        print("publicID = %s" % pick.publicID())
        print("time     = %s" % pick.time().value())
        print("n,s,l,c  = %s" % str(nslc(pick)))
        #######################################

    def doSomethingWithAmplitude(self, amplitude):
        #######################################
        #### Include your custom code here ####
        print("publicID = %s" % amplitude.publicID())
        print("n,s,l,c  = %s" % str(nslc(amplitude)))
        print("type     = %s" % amplitude.type())
        print("value    = %s" % amplitude.amplitude().value())
        print("pickID   = %s" % amplitude.pickID())
        #######################################

    def updateObject(self, parentID, obj):
        # called if an updated object is received
        pick = seiscomp.datamodel.Pick.Cast(obj)
        if pick:
            # note that the object's ClassName is only accessible
            # *after* the cast
            print("received updated %s object" % pick.ClassName())
            self.doSomethingWithPick(pick)
            return
        amplitude = seiscomp.datamodel.Amplitude.Cast(obj)
        if amplitude:
            print("received updated %s object" % amplitude.ClassName())
            self.doSomethingWithAmplitude(amplitude)
            return

    def addObject(self, parentID, obj):
        # called if a new object is received
        pick = seiscomp.datamodel.Pick.Cast(obj)
        if pick:
            print("received new %s object" % pick.ClassName())
            self.doSomethingWithPick(pick)
            return
        amplitude = seiscomp.datamodel.Amplitude.Cast(obj)
        if amplitude:
            print("received new %s object" % amplitude.ClassName())
            self.doSomethingWithAmplitude(amplitude)
            return

    def run(self):
        self.greeting()
        return seiscomp.client.Application.run(self)

if __name__ == "__main__":
    app = PickClient(len(sys.argv), sys.argv)
    sys.exit(app())
