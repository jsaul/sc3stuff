#!/bin/sh

ev="gfz2011okdy"
t1="2011-07-24 18:45:00"
python xml-playback-messaging.py --speed 1 --begin "$t1" -u xmlpb --host st127.gfz-potsdam.de --xml picks-"$ev".xml --debug
