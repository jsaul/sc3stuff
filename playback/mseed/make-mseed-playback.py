#!/usr/bin/env python

import sys, time
import seiscomp.client, seiscomp.datamodel

stream_whitelist = ["BH", "SH","HH"]
component_whitelist = [] # set to ["Z"] for vertical component only
network_blacklist = ["TE"]
network_whitelist = [] # all except blacklist

# seconds before and after origin time
before, after = 1800, 1*3600+1800

sort = True   # will produce sorted files with ".sorted-mseed" extension


def filterStreams(streams):
    # NOTE that the criteria here are quite application dependent:
    # If we have HH and BH streams use only BH etc., but in other
    # contexts HH would have priority over BH

    filtered = []

    for net, sta, loc, cha in streams:
        if cha[:2] in [ "HH", "SH" ] and (net, sta, loc, "BH"+cha[-1]) in streams:
            continue
        filtered.append( (net, sta, loc, cha) )

    return filtered


def getCurrentStreams(dbr):
    now = seiscomp.core.Time.GMT()
    inv = seiscomp.datamodel.Inventory()
    dbr.loadNetworks(inv)

    result = []
    
    for inet in range(inv.networkCount()):
        network = inv.network(inet)
        if network_blacklist and network.code()     in network_blacklist:
            continue
        if network_whitelist and network.code() not in network_whitelist:
            continue
        dbr.load(network);
        for ista in range(network.stationCount()):
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

            for iloc in range(station.sensorLocationCount()):
                loc = station.sensorLocation(iloc)

                for istr in range(loc.streamCount()):
                    stream = loc.stream(istr)
                    if stream.code()[:2] not in stream_whitelist:
                        continue

                    result.append( (network.code(), station.code(), loc.code(), stream.code()) )

    return filterStreams(result)


class DumperApp(seiscomp.client.Application):

    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, True)
        self.setLoggingToStdErr(True)
        self.setDaemonEnabled(False)
        self.setRecordStreamEnabled(True)


    def validateParameters(self):
        if seiscomp.client.Application.validateParameters(self) == False:
            return False
        return True


    def createCommandLineDescription(self):
        try:
            self.commandline().addGroup("Dump")
            self.commandline().addStringOption("Dump", "event,E", "ID of event to dump")
            self.commandline().addOption("Dump", "unsorted,U", "produce unsorted output (not suitable for direct playback!)")
        except:
            seiscomp.logging.warning("caught unexpected error %s" % sys.exc_info())

    def get_and_write_data(self, t1, t2, out):
        dbr = seiscomp.datamodel.DatabaseReader(self.database())
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

            # experts only:
            # increase in case of connection problems, normally not needed
            number_of_attempts = 1

            for attempt in range(number_of_attempts):
                if self.isExitRequested(): return

                stream = seiscomp.io.RecordStream.Open(self.recordStreamURL())
                stream.setTimeout(3600)
                for net, sta, loc, cha in netsta_streams[netsta]:
                    if component_whitelist and cha[-1] not in component_whitelist:
                        continue
                    stream.addStream(net, sta, loc, cha, t1, t2)

                count = 0
                input = seiscomp.io.RecordInput(stream, seiscomp.core.Array.INT, seiscomp.core.Record.SAVE_RAW)
                while 1:
                    try:
                        rec = input.next()
                    except:
                        break
                    if not rec:
                        break

                    count += 1
                    if sort:
                        data.append( (rec.endTime(), rec.raw().str()) )
                    else:
                        out.write("%s" % rec.raw().str())

                sys.stderr.write("Read %d records for %d streams\n" % (count, len(netsta_streams[netsta])))
                if count > 0 or attempt+1 == number_of_attempts:
                    break
                if self.isExitRequested(): return
                sys.stderr.write("Trying again\n")
                time.sleep(5)

        if sort:
            data.sort()

        if sort:
            # finally write sorted data and ensure uniqueness
            previous = None
            for endTime, raw in data:
                if previous is not None and raw[6:] == previous[6:]:
                    # unfortunately duplicates do happen sometimes
                    continue
                out.write("%s" % raw)
                previous = raw


    def dump(self, eventID):
        self._dbq = self.query()
        evt = self._dbq.loadObject(seiscomp.datamodel.Event.TypeInfo(), eventID)
        evt = seiscomp.datamodel.Event.Cast(evt)
        if evt is None:
            raise TypeError("unknown event '" + eventID + "'")

        originID = evt.preferredOriginID()
        org = self._dbq.loadObject(seiscomp.datamodel.Origin.TypeInfo(), originID) 
        org = seiscomp.datamodel.Origin.Cast(org)

        magID = evt.preferredMagnitudeID()
        mag = self._dbq.loadObject(seiscomp.datamodel.Magnitude.TypeInfo(), magID)
        mag = seiscomp.datamodel.Magnitude.Cast(mag)

        now = seiscomp.core.Time.GMT()
 
        val = mag.magnitude().value()
        if sort:
            out = "%s-M%3.1f.sorted-mseed" % (eventID, val)
        else:
            out = "%s-M%3.1f.unsorted-mseed" % (eventID, val)
        out = open(out, "w")

        t0 = org.time().value()
        t1, t2 = t0 + seiscomp.core.TimeSpan(-before), t0 + seiscomp.core.TimeSpan(after)

        self.get_and_write_data(t1,t2,out)
        return True


    def run(self):
        if self.commandline().hasOption("unsorted"):
            sort = False

        evid = self.commandline().optionString("event")
        return self.dump(evid):


def main():
    app = DumperApp(len(sys.argv), sys.argv)
    app()

if __name__ == "__main__":
    main()
