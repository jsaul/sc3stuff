#!/bin/sh

# This is the host to send the messages to.
host=geofon-proc

# Comment this out to actually send the pick which. You don't want to do
# with the dummy picker unless the target messaging target is only a
# test setup.
test=--test

./dummypicker.sh |
seiscomp exec python picksender.py $test --debug -H $host
