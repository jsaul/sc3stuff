from __future__ import print_function
import sys, select
import seiscomp.core, seiscomp.client, seiscomp.datamodel

class PickSender(seiscomp.client.Application):

    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(True)
        self.setDatabaseEnabled(False, False)
        self.setPrimaryMessagingGroup("PICK")

    def createCommandLineDescription(self):
        # adds option --test to the default options
        seiscomp.client.Application.createCommandLineDescription(self)
        self.commandline().addGroup("Mode");
        self.commandline().addOption("Mode", "test", "Do not send any object");

    def parse(self, line):
        # parses a line of input and returns a Pick object
        line = line.strip().split()
        pickID, time, net, sta = line[0], line[1], line[2], line[3]

        # this will become the creation time
        now = seiscomp.core.Time.GMT()
        time = seiscomp.core.Time()
        time.fromString("2015-09-25T10:33:42","%Y-%m-%dT%H:%M:%S")
        pick = seiscomp.datamodel.Pick.Create(pickID)
        wfid = seiscomp.datamodel.WaveformStreamID()
        wfid.setNetworkCode(net)
        wfid.setStationCode(sta)
        pick.setWaveformID(wfid)
        crea = seiscomp.datamodel.CreationInfo()
        crea.setAuthor("pick import script")
        crea.setAgencyID("TEST")
        crea.setCreationTime(now)
        crea.setModificationTime(now)
        pick.setCreationInfo(crea)
        pick.setEvaluationStatus(seiscomp.datamodel.REVIEWED)
        pick.setEvaluationMode(seiscomp.datamodel.MANUAL)
        pick.setTime(seiscomp.datamodel.TimeQuantity(time) )
        pick.setCreationInfo(crea)
        return pick

    def process(self, line):
        # parse one input line and send the resulting pick
        ep = seiscomp.datamodel.EventParameters()
        seiscomp.datamodel.Notifier.Enable()
        pick = self.parse(line)
        ep.add(pick)
        msg = seiscomp.datamodel.Notifier.GetMessage()
        if self.commandline().hasOption("test"):
            print("I would now send pick", pick.publicID())
        else:
            if self.connection().send(msg):
                print("Succeeded to send pick", pick.publicID())
            else:
                print("Failed to send pick", pick.publicID())
        seiscomp.datamodel.Notifier.Disable()

    def poll(self):
        # while there is some input available on the input stream...
        while True:
            if not self.poller.poll(100):
                break
            line = sys.stdin.readline()
            self.process(line)

    def handleTimeout(self):
        self.poll()

    def run(self):
        # we poll the input stream sys.stdin
        self.poller = select.poll()
        self.poller.register(sys.stdin)
        #set the polling interval to 1 sec
        self.enableTimer(1)
        print("Hi! The PickSender is now starting.")
        # return to the Application's processing
        return seiscomp.client.Application.run(self)

if __name__ == "__main__":
    app = PickSender(len(sys.argv), sys.argv)
    sys.exit(app())
