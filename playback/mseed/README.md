See example.sh for usage instructions. ;)

This script loads for a given event the waveforms from the waveform
server as configured. The waveforms are loaded per network in order
to deal with smaller pieces and not to interfere with the server's
normal operation.

This is meant as a starting point for own adoptions. Many things
could be improved e.g. the stream filtering should be based on nscl
patterns etc. but for our normal operation this is used as provided
here. The aim is to really save all waveform for a time window
around an event to be able to reproduce all aspects of the event
incl. possible fake event generation due to distant stations etc.
