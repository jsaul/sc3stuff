dump-active-streams
===================

* reads the config from database
* iterates over the config
* prints a list of all active streams, i.e. those for which a
  detecLocId and detecStreamId entry exists in the config. This is
  normally e.g. the streams used for picking
* output is net sta loc stream
