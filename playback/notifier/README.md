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

Relevant scripts:

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
>        python notifier-extract.py -s "2018-05-18T08:00:00Z" -e "2018-05-18T09:10:00Z" ~/log/notifiers/notifier-log.2018-05-18T0* > gfz2018jqzl-notifier-playback

* `notifier-player.py`

    Plays back notifiers from file. It doesn't do much, just
    extracts the notifier messages from the notifier log and if the
    time matches the time specified window if passes the message on
    to `handleMessage()`. In a real-world program this workflow could
    substitute an existing messaging workflow, without any changes needed
    downstream. After all, the SC3 messaging is also based on notifier
    messages and whether we retrieve these from a messaging or from an
    XML file doesn't make much difference.

All the stuff in here is experimental! Any feedback and suggestions are highly appreciated.

