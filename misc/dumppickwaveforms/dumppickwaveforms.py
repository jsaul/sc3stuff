############################################################################
#    Copyright (C) 2009 by GFZ Potsdam                                     #
#                                                                          #
#    author: Joachim Saul                                                  #
#    email:  saul@gfz-potsdam.de                                           #
#                                                                          #
#    This program is free software; you can redistribute it and/or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################

import sys, os, glob
import seiscomp.core, seiscomp.datamodel, seiscomp.io, seiscomp.logging
import sc3stuff.eventloader, sc3stuff.util

beforeP = afterP = 360

def usage(exitcode=0):
    sys.exit(exitcode)


def RecordIterator(recordstream, showprogress=False):
        count = 0
        inp = seiscomp.io.RecordInput(recordstream, seiscomp.core.Array.INT, seiscomp.core.Record.SAVE_RAW)
        while 1:
            try:
                rec = inp.next()
            except Exception, exc:
                sys.stderr.write("ERROR: " + str(exc) + "\n")
                rec = None

            if not rec:
                break
            if showprogress:
                count += 1
                sys.stderr.write("%-20s %6d\r" % (rec.streamID(), count))
            yield rec


class RecordDumperApp(sc3stuff.eventloader.EventLoaderApp):

    def __init__(self, argc, argv):
        sc3stuff.eventloader.EventLoaderApp.__init__(self, argc, argv)
        self.setRecordStreamEnabled(True)

    def loadAll(self, eventID):
        ep = self.readEventParameters()

        event, origin, pick, ampl, fm = sc3stuff.util.extractEventParameters(ep, eventID)

        evt = event[eventID]
        org = origin[evt.preferredOriginID()]

        return evt, org, pick, ampl

    def _getDistancesArrivalsSorted(self, org):
        # sort arrival list by distance
        dist_arr = []
        for i in xrange(org.arrivalCount()):
            arr = org.arrival(i)
            if arr.weight() < 0.1:
                continue

            phase_whitelist = ["P","Pn","Pg","Pb","Pdiff","PKP","S","Sg"]
# uncomment this to allow all phases (incl. S)
#           phase_whitelist = None
            if phase_whitelist:
                phase = arr.phase().code()
                if phase not in phase_whitelist:
                    continue

            p = seiscomp.datamodel.Pick.Find(arr.pickID())
            if p is None:
                continue
            t0 = p.time().value()
            dist_arr.append((t0, arr))
#           dist_arr.append((arr.distance(), arr))
        dist_arr.sort()
        return dist_arr

    def _dumpWaveform(self, evt, org):
        waveform_windows = []
        expected_filenames = []
        done_nslc = []
        for dist, arr in self.dist_arr:
            p = seiscomp.datamodel.Pick.Find(arr.pickID())
            if p is None:
                continue
            wfid = p.waveformID()
            net = wfid.networkCode()
            sta = wfid.stationCode()
            loc = wfid.locationCode()
            cha = wfid.channelCode()
            nslc = (net,sta,loc,cha)
            if nslc in done_nslc:
                continue

            # Sometimes manual picks produced by scolv have only
            # "BH" etc. as channel code. IIRC this is to accomodate
            # 3-component picks where "BHZ" etc. would be misleading.
            # But here it doesn't matter for the data request.
            if len(cha) == 2:
                cha = cha+"Z"
            t0 = p.time().value()
            t1, t2 = t0 + seiscomp.core.TimeSpan(-beforeP), t0 + seiscomp.core.TimeSpan(afterP)
            waveform_windows.append( (t1, t2, net, sta, loc, cha) )
            expected_filenames.append("%s/%s.%s.%s.%s.mseed" % (evt.publicID(), net, sta, loc, cha))
            done_nslc.append(nslc)

        # request waveforms and dump them to one file per stream
        data = {}
        stream = seiscomp.io.RecordStream.Open(self.recordStreamURL())
        stream.setTimeout(300)
        for t1, t2, net, sta, loc, cha in waveform_windows:
            for c in "ZNE12":
                stream.addStream(net, sta, loc, cha[:2]+c, t1, t2)
        for rec in RecordIterator(stream, showprogress=True):
            if not rec.streamID() in data:
                data[rec.streamID()] = ""

            # append binary (raw) MiniSEED record to data string
            data[rec.streamID()] += rec.raw().str()
        count = 0
        for key in data:
            count += len(data[key])/512
        sys.stderr.write("Read %d records for %d streams\n" % (count, len(data.keys())))

        for streamID in data:
            file(evt.publicID()+"/"+streamID+".mseed", "w").write(data[streamID])

        # check for missing files (data we requested but which is missing)
        missing_filenames = []
        found_filenames = glob.glob("%s/*.*.*.*.mseed" % evt.publicID())
        for filename in expected_filenames:
            if filename not in found_filenames:
                missing_filenames.append(filename)
        mffilename = evt.publicID()+"/missing-files"
        if os.path.exists(mffilename):
            os.unlink(mffilename)
        if missing_filenames:
            missing_filenames.sort()
            file(mffilename,"w").write("\n".join(missing_filenames))

    def _dumpPickList(self, evt, org, filename="picks"):

        pick_lines = []
        for dist, arr in self.dist_arr:
            p = seiscomp.datamodel.Pick.Find(arr.pickID())
            if p is None:
                continue

            wfid = p.waveformID()
            net = wfid.networkCode()
            sta = wfid.stationCode()
            loc = wfid.locationCode()
            cha = wfid.channelCode()

            t0 = p.time().value()

            pst = "A"
            if p.evaluationMode() != seiscomp.datamodel.AUTOMATIC:
                pst = "M"
            amp = per = snr = 0.

            time = t0.toString("%Y-%m-%d %H:%M:%S.%f000000")[:22]
            line = "%s %-2s %-6s %-3s %-2s %6.1f %10.3f %4.1f %1s %-6s %s" \
                % (time, net, sta, cha, [loc,"__"][loc==""], snr, amp, per, pst, arr.phase().code(), p.publicID())
            pick_lines.append(((dist,t0), line))

        # dump the pick lines to one single file
        pick_lines.sort()
        file(evt.publicID()+"/"+filename, "w").write("%s\n" % "\n".join([ line for x,line in pick_lines ]))

    def dumpEvent(self, eventID):
        evt, org, pick, ampl = self.loadAll(eventID)

        # create event directory
        try:
            os.mkdir(eventID)
        except OSError:
            pass # we interpret this as already existing event directory
        
        self.dist_arr = self._getDistancesArrivalsSorted(org)
        seiscomp.logging.info("dumping waveforms for preferred origin '%s'" % org.publicID())
        self._dumpWaveform(evt, org)
        seiscomp.logging.info("dumping waveforms for preferred origin '%s' FINISHED" % org.publicID())
        seiscomp.logging.info("dumping picks for preferred origin '%s'" % org.publicID())
        self._dumpPickList(evt, org)
        seiscomp.logging.info("dumping picks for preferred origin '%s' FINISHED" % org.publicID())

        #################################################################
        ### If you don't want to dump the picks for the largest automatic
        ### origin, then uncomment this:
        # return # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        #################################################################

        # find largest automatic origin

        # loop over all origins
        origins = [ org for org in self.query().getOrigins(eventID) ]
        # This DB query must be finished before we start iterating over the origins
        # as otherwise we get netsted queries, which are not allowed.

        if len(origins) > 0:
            sorted = []
            for org in origins:
                # there should be a cleaner way...
                org = seiscomp.datamodel.Origin.Cast(org)
                if not org: continue
                org = self.query().loadObject(seiscomp.datamodel.Origin.TypeInfo(), org.publicID())
                if not org: continue
                org = seiscomp.datamodel.Origin.Cast(org)
                if not org: continue
                try:
                    if org.evaluationMode() != seiscomp.datamodel.AUTOMATIC:
                        continue
                except:
                    continue
                sorted.append( (org.arrivalCount(), org) )
            if len(sorted) > 0:
                # get origin with largest arrival count
                sorted.sort()
                arrivalCount, org = sorted[-1]
                seiscomp.logging.info("dumping picks for automatic origin '%s'" % org.publicID())
                # we need to load arrivals and picks for that origin as well
                self.dist_arr = self._getDistancesArrivalsSorted(org)
                self._dumpPickList(evt, org, filename="picks-automatic")

    def run(self):
        try:
            eventID = self.commandline().optionString("event")
        except:
            sys.stderr.write("You must specify event id\n")
            return False

        self.dumpEvent(eventID)
        return True


if __name__ == "__main__":
    app = RecordDumperApp(len(sys.argv), sys.argv)
    app()
