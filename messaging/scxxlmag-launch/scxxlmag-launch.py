import sys, os, traceback
from eventclient import EventClient, info, warning, error, debug


class Launcher(EventClient):

    def __init__(self):
        EventClient.__init__(self)
        self._program = './scxxlmag-wrap.sh %s'
        self._minmag = 5.0
        self._maxdep = 150.
        self._launched = []

    def changed_origin(self, event_id, previous_id, current_id):
        info("Launcher.changed_origin") 
        info("event %s: CHANGED preferredOriginID" % event_id)
        info("    from %s" % previous_id)
        info("      to %s" % current_id)
#       self.launch(event_id)


    def changed_magnitude(self, event_id, previous_id, current_id):
        info("Launcher.changed_magnitude") 
        info("event %s: CHANGED preferredMagnitudeID" % event_id)
        info("    from %s" % previous_id)
        info("      to %s" % current_id)
        self.launch(event_id)


    def launch(self, event_id):
        if event_id in self._launched:
            return # nothing to do any more
        ste = self._state[event_id]
        try:
            dep = self._state[event_id].origin.depth().value()
            mag = self._state[event_id].magnitude.magnitude().value()
        except AttributeError:
            warning("Launcher.launch event %s incomplete" % event_id)
            return
        if dep > self._maxdep:
            info("Launcher.launch event %s too deep" % event_id)
            return
        if mag < self._minmag:
            info("Launcher.launch event %s too small" % event_id)
            return

        cmd = self._program % event_id
        cmd += " &"
        info("starting '%s'" % cmd)
        os.system(cmd)
        self._launched.append(event_id) 


app = Launcher()
sys.exit(app())
