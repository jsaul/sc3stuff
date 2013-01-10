#!/usr/bin/env python

import sys, time, traceback
import seiscomp3.Client, seiscomp3.DataModel

stream_whitelist = ["BH", "SH","HH"]
component_whitelist = [] # set to ["Z"] for vertical component only
network_blacklist = ["TE"]
network_whitelist = [] # all except blacklist

# seconds before and after origin time
before, after = 1800, 5400

sort = True   # will produce sorted files with ".sorted-mseed" extension
#sort = False # will produce UNsorted files with ".unsorted-mseed" extension
### NOTE: unsorted output will be irrelevant for most users.


def filterStreams(streams):
    # if we have HH and BH streams use only BH etc.

    filtered = []

    for net, sta, loc, cha in streams:
        if cha[:2] in [ "HH", "SH" ] and (net, sta, loc, "BH"+cha[-1]) in streams:
            continue
        filtered.append( (net, sta, loc, cha) )

    return filtered


def getCurrentStreams(dbr):
    now = seiscomp3.Core.Time.GMT()
    inv = seiscomp3.DataModel.Inventory()
    dbr.loadNetworks(inv)

    result = []
    
    for inet in xrange(inv.networkCount()):
        network = inv.network(inet)
        if network_blacklist and network.code()     in network_blacklist:
            continue
        if network_whitelist and network.code() not in network_whitelist:
            continue
        dbr.load(network);
        for ista in xrange(network.stationCount()):
            station = network.station(ista)
            try:
                start = station.start()
            except:
                continue

            try:
                end = station.end()
                if not start <= now <= end:
                    continue
            except:
                pass

            # now we know that this is an operational station

            for iloc in xrange(station.sensorLocationCount()):
                loc = station.sensorLocation(iloc)

                for istr in xrange(loc.streamCount()):
                    stream = loc.stream(istr)
                    if stream.code()[:2] not in stream_whitelist:
                        continue

#                   print network.code(), station.code(), loc.code(), stream.code()
                    result.append( (network.code(), station.code(), loc.code(), stream.code()) )

    return filterStreams(result)


class DumperApp(seiscomp3.Client.Application):

    def __init__(self, argc, argv):
        seiscomp3.Client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(True)
        self.setDatabaseEnabled(True, True)
        self.setLoggingToStdErr(True)
        self.setDaemonEnabled(False)
        self.setRecordStreamEnabled(True)

    def validateParameters(self):
        try:
            if seiscomp3.Client.Application.validateParameters(self) == False:
                return False
            return True

        except:
            info = traceback.format_exception(*sys.exc_info())
            for i in info: sys.stderr.write(i)
            sys.exit(-1)

    def createCommandLineDescription(self):
        try:
            try:
                self.commandline().addGroup("Dump")
                self.commandline().addStringOption("Dump", "event,E", "ID of event to dump")
            except:
                seiscomp3.Logging.warning("caught unexpected error %s" % sys.exc_info())
            return True
        except:
            info = traceback.format_exception(*sys.exc_info())
            for i in info: sys.stderr.write(i)
            sys.exit(-1)

    def get_and_write_data(self, t1, t2, out):
        dbr = seiscomp3.DataModel.DatabaseReader(self.database())
        streams = getCurrentStreams(dbr)

        # split all streams into groups of same net
        netsta_streams = {}
        for net, sta, loc, cha in streams:
            netsta = net
            if not netsta in netsta_streams:
                netsta_streams[netsta] = []
            netsta_streams[netsta].append( (net, sta, loc, cha) )

        data = []
        netsta_keys = netsta_streams.keys()
        netsta_keys.sort()
        for netsta in netsta_keys:

            for attempt in 1,2,3:
                stream = seiscomp3.IO.RecordStream.Open(self.recordStreamURL())
                stream.setTimeout(3600)
                for net, sta, loc, cha in netsta_streams[netsta]:
                    if component_whitelist and cha[-1] not in component_whitelist:
                        continue
                    stream.addStream(net, sta, loc, cha, t1, t2)

                count = 0
                input = seiscomp3.IO.RecordInput(stream, seiscomp3.Core.Array.INT, seiscomp3.Core.Record.SAVE_RAW)
                while 1:
                    try:
                        rec = input.next()
                    except:
                        break
                    if not rec:
                        break

                    count += 1
#                   sys.stderr.write("%-20s %6d\r" % (rec.streamID(), count))
                    if sort:
                        nslc = tuple(rec.streamID().split("."))
                        data.append( (rec.endTime(), nslc, rec.raw().str()) )
                    else:
                        out.write("%s" % rec.raw().str())

                sys.stderr.write("Read %d records for %d streams\n" % (count, len(netsta_streams[netsta])))
                if count > 0:
                    break
                sys.stderr.write("Trying again\n")
                time.sleep(5)

        if sort:
            data.sort()

        if sort:
            # finally write sorted data and ensure uniqueness
            previous = None
            for endTime, nslc, raw in data:
                if previous is not None and raw[6:] == previous[6:]:
                    # unfortunately duplicates do happen sometimes
                    continue
                out.write("%s" % raw)
                previous = raw


    def dump(self, eventID):
        evt = self._dbq.loadObject(seiscomp3.DataModel.Event.TypeInfo(), eventID)
        evt = seiscomp3.DataModel.Event.Cast(evt)
        if evt is None:
            raise TypeError, "unknown event '" + eventID + "'"

        originID = evt.preferredOriginID()
        org = self._dbq.loadObject(seiscomp3.DataModel.Origin.TypeInfo(), originID) 
        org = seiscomp3.DataModel.Origin.Cast(org)

        magID = evt.preferredMagnitudeID()
        mag = self._dbq.loadObject(seiscomp3.DataModel.Magnitude.TypeInfo(), magID)
        mag = seiscomp3.DataModel.Magnitude.Cast(mag)

        now = seiscomp3.Core.Time.GMT()
        try:
            val = mag.magnitude().value()
            if sort:
                out = "%s-M%3.1f.sorted-mseed" % (eventID, val)
            else:
                out = "%s-M%3.1f.unsorted-mseed" % (eventID, val)
            out = file(out, "w")

            t0 = org.time().value()
            t1, t2 = t0 + seiscomp3.Core.TimeSpan(-before), t0 + seiscomp3.Core.TimeSpan(after)

            self.get_and_write_data(t1,t2,out)
            return True

        except:
            info = traceback.format_exception(*sys.exc_info())
            for i in info: sys.stderr.write(i)
            sys.exit(-1)

    def run(self):
        try:
            self._dbq = self.query()
            evid = self.commandline().optionString("event")
            self.dump(evid)

        except:
            info = traceback.format_exception(*sys.exc_info())
            for i in info: sys.stderr.write(i)
            sys.exit(-1)
        

def main():
    app = DumperApp(len(sys.argv), sys.argv)
    app()

if __name__ == "__main__":
    main()
