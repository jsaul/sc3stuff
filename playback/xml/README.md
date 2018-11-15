XML-based scautoloc playbacks
=============================

This directory contains a set of scripts to generate XML playbacks and play them back using scautoloc.

- `make-xml-playback.sh`

    Create files needed by scautoloc to run an XML playback without connecting to the database

    Usage:

    ```
    make-xml-playback.sh "$event" "$comment"
    ```

    For instance:

    ```
    make-xml-playback.sh gfz2015iatp "Nepal Earthquake"
    ```

    Based in the specified event ID, it loads all picks, manual and automatic, plus the associated amplitudes, from the database and dumps them to an XML file. If present, also all *manual* origins
belonging to the event are dumped. These are not used normally but can be used to simulate a manual location done by the user at any time "during" the event.

    The comment is optional.

    *Before* you run the `make-xml-playback.sh` script, you need to edit it at the top to make the 'db' variable point to your SC3 database. Normally you just substitute geofon-proc with localhost if you run the script locally on your SC3 host.

    The time window around the event is -20 ... +30 minutes relative to the origin time, which is OK for teleseismic events. For playing back local events, this time window may be adjusted at the top of
the dump-picks-to-xml.py script.

    As scautoloc in offline mode also needs the station coordinates, we dump these to a file, too, to make sure we have them available. For completeness, we also dump the bulletin for the event.

- `run-xml-playback-autoloc.sh`

    This script calls scautoloc to play back the picks. Its only parameter is the event ID.

This is work in progress! The goal of this is to collect playbacks
for all kinds of scenarios, and use them for systematic and automated
unit testing.

If something doesn't work for you let me know.     
