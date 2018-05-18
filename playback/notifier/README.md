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

All the stuff in here is experimental! Any feedback and suggestions are highly appreciated.

