playbacks
=========

*Scripts to support playbacks in SeisComP 3*

There are many different objectives for doing playbacks and
therefore different mechanisms that can be used.

* Full waveform playback

  Waveform playbacks innvolve the processing of a data time window
that can range in length from just minutes to years. Short playbacks
are usually made for testing (incl. stress tests) or demo purposes.
Long playbacks are used for offline processing of large quantities
of waveforms. This is typically the case after a seismological field
experiment has been finalized and the waveform data shall be
analyzed for local seismicity.


* Parameter-only playback

  Waveform playbacks are relatively "heavy" as the full waveform
processing requires a lot of system resources. In some cases,
especially for testing and debugging, much lighter parameter-only
playbacks are preferred because they are much easier to run ad hoc
and repeeatedly. This kind of playback is particularly useful for
modules like scautoloc, which doesn't process waveforms directly.
Instead it only processes picks and amplitudes previously measured
by a picker like scautopick. Both picks and amplitudes are usually
static. This means that they are determined once and are unlikely to
change later on. Therefore we can retrieve these objects from the
database and simulate the real-time processing by using the object
creation time to reproduce (and possibly debug) the real-time
behaviour. This works by reading the picks and amplitudes from an
XML file, sorting them according to their creation times and
playing them back in that order.



Content:

* xml/
    XML based parameter playback (mainly for picks/amplitudes)
    primarily for testing and debugging of scautoloc

* notifier/
    XML based parameter playbacks using notifier logs.

* mseed/
    generation of sorted, multiplexed MiniSEED files suitable for
    full waveform playback in SeisComP 3
