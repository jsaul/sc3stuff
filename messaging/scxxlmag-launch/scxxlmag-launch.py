import sys, os, traceback
from eventclient import EventClient, info,error,debug


class Launcher(EventClient):

    def __init__(self):
        EventClient.__init__(self)
        self._program = './program.sh %s'
        self._launched = []

    def changed_origin(self, event_id, previous_id, current_id):
        info("Launcher.changed_origin") 
        info("event %s: CHANGED preferredOriginID" % event_id)
        info("    from %s" % previous_id)
        info("      to %s" % current_id)
        self.cleanup()
        self.launch(event_id)


    def changed_magnitude(self, event_id, previous_id, current_id):
        info("Launcher.changed_magnitude") 
        info("event %s: CHANGED preferredMagnitudeID" % event_id)
        info("    from %s" % previous_id)
        info("      to %s" % current_id)
        self.cleanup()


    def launch(self, event_id):
        if event_id in self._launched:
            return # nothing to do any more
        cmd = self._program % event_id
        cmd += " &"
        info("starting '%s'" % cmd)
        os.system(cmd)
        self._launched.append(event_id) 

app = Launcher()
sys.exit(app())
