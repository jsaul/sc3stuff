Notifier playbacks
==================

A rather complete history of an event can be captured by
logging also the transient state of objects in the form of notifier
messages. There will likely be support for this in SC3 in future.
Some proof-of-concept Python scripts to demonstrate the power of
this playback mechanism are included here already.  The idea is to
subscribe to all relevant messaging groups and grab all notifier
messages that come around.  Each received notifier message is saved
as XML document to a notifier log. Each log entry is preceded by a
header line containing a time stamp for synchonization and the
length of the following XML document in bytes. This log will have to
be run continuously and stored e.g. in day files.

Relevant scripts
----------------

* `notifier-logger.py`

    Creates the notifier logs. Currently notifier log files
    containing one hour of notifiers is written and gzipped once
    finished. The output directory needs to be specified; please
    refer to the `run-notifier-logger.sh` script for an example of
    how to run the logger.

* `notifier-extract.py`

    Extracts time slices of notifiers from the specified notifier
    log files, which may be gzipped (generally are, if created using
    the `notifier-logger.py` script. Need to specify start and end
    time as well as the input files.

    Call it like e.g.
>     python notifier-extract.py \
>       -s "2018-05-18T08:00:00Z" -e "2018-05-18T09:10:00Z" \
>       ~/log/notifiers/notifier-log.2018-05-18T0* > gfz2018jqzl-notifier-playback

* `notifier-player.py`

    Example program that plays back notifiers from file. It doesn't do much, just
    extracts the `NotifierMessage` objects from the notifier log and if the
    time matches the time specified window it passes the message on
    to `handleMessage()`. In a real-world program this workflow could
    substitute an existing messaging workflow, without any changes required
    downstream. After all, the SC3 messaging is also based on notifier
    messages and whether we retrieve these from a messaging or from an
    XML file doesn't make much difference.


Format of the notifier playback files
-------------------------------------

Each `NotifierMessage` object is saved as complete XML document in the
same order in which they were received by the notifier logger
client. In a real-time processing system, this time is practically
identical with the time all other clients in the processing receive
the message. Therefore by saving the time of reception and using
this time later in the notifier playback, we are able to reproduce
the message flow exactly as in real-time.

`NotifierMessage` objects don't contain a `creationInfo` attribute like
for instance `Pick` objects. This means that we have to save the
message reception time somewhere else. We therefore use one header
line before each `NotifierMessage` XML block. This header also
contains the size (in bytes) of the entire following XML block,
which allows to efficiently read in the XML block as a string,
before moving on to the next header line and so on. If no header
line could be read, we assume that the end of the file was reached.
In addition to the reception time and XML size the header line
contains a hash, which is used to identify the `NotifierMessage`
object. This is in order to avoid duplicate `NotifierMessage`'s.

In summary, the header line consists of `####` followed by the UTC time stamp, the hash and the number of bytes as well as the word `bytes` indicating that the number is actually the number of bytes. That's all.

Example:
```
####  2018-06-14T00:00:53.270025Z  1bd21eabe25cfa2762a978201756bd88  1030 bytes
<?xml version="1.0" encoding="UTF-8"?>
<seiscomp xmlns="http://geofon.gfz-potsdam.de/ns/seiscomp3-schema/0.10" version="0.10">
  <notifier_message>
    <notifier parentID="EventParameters" operation="add">
    ...
    </notifier>
  </notifier_message>
</seiscomp>
####  2018-06-14T00:00:54.686178Z  f421b67fa4741fa84d5693ac0ce3208e  992 bytes
<?xml version="1.0" encoding="UTF-8"?>
<seiscomp xmlns="http://geofon.gfz-potsdam.de/ns/seiscomp3-schema/0.10" version="0.10">
  <notifier_message>
    <notifier parentID="EventParameters" operation="add">
    ...
```

Note that in principle it is possible to simulate data latencies by altering the notifier reception time in the header lines. However, since the notifier playbacks are expected to be ordered in time, sorting the notifier messages would be required before the playback.


Warning!
--------

The notifier playback incl. the format of the notifier log is still experimental! Actual programs supporting notifier playbacks are currently under development and are not yet part of the SC3 package.

Any feedback and suggestions are highly appreciated!

