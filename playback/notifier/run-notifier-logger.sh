#!/bin/sh

d=$HOME/log/notifiers
p=$d/notifier-log
mkdir -p $d

$HOME/seiscomp3/bin/seiscomp exec python notifier-logger.py -H geofon-proc -u ntflog2 --debug --prefix=$p
