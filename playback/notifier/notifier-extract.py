#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys, optparse
import seiscomp.core

description="%prog - extract notifiers from log based on start and end time"

p = optparse.OptionParser(usage="%prog --start-time t2 --end-time t2  >", description=description)
p.add_option("-s", "--start-time", action="store", help="specify start time")
p.add_option("-e", "--end-time", action="store", help="specify end time")
p.add_option("-v", "--verbose", action="store_true", help="run in verbose mode")

(opt, filenames) = p.parse_args()

class Item: pass

def read_notifiers(filename, startTime, endTime):
    if filename.endswith(".gz"):
        import gzip
        f = gzip.open(filename)
    else:
        f = file(filename)

    while True:
        while True:
            line = f.readline()
            if not line:
                # empty input / EOF
                return
            line = line.strip()
            if not line:
                # blank line
                continue
            if line[0] == "#":
                break

        if len(line.split()) == 3:
            sharp, timestamp, nbytes = line.split()
        elif len(line.split()) == 4:
            sharp, timestamp, nbytes, sbytes = line.split()
            assert sbytes == "bytes"
        elif len(line.split()) == 5:
            sharp, timestamp, md5hash, nbytes, sbytes = line.split()
            assert sbytes == "bytes"
        else:
            return

        assert sharp[0] == "#"
        time = seiscomp.core.Time.GMT()
        time.fromString(timestamp, "%FT%T.%fZ")
        if startTime is not None and time < startTime:
            continue
        if endTime is not None and time > endTime:
            break

        nbytes = int(nbytes)
        assert sharp[0] == "#"
        xml = f.read(nbytes)

        item = Item()
        item.time = time
        item.line = line
        item.xml = xml

        yield item

def parseTime(s):
    for fmtstr in "%FT%TZ", "%FT%T.%fZ":
        t = seiscomp.core.Time.GMT()
        if t.fromString(s, fmtstr):
            return t
    raise ValueError("could not parse time string '%s'" %s)

startTime = parseTime(opt.start_time)
endTime   = parseTime(opt.end_time)

for filename in filenames:
    if opt.verbose:
        print("working on input file '%s'" % filename, file=sys.stderr)
    for item in read_notifiers(filename, startTime, endTime):
        print(item.line)
        print(item.xml)
