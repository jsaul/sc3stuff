#!/bin/sh

# dummy program

evid=$1

mkdir -p logs

# This is effectively a locking as mkdir can only
# succeed once for a given event ID.
mkdir logs/$evid || exit

# For the time being do some nonsense for testing.
for i in `seq 1 1 3600`
do
    echo $evid $i `date`
    sleep 2
done > logs/$evid/out.txt
