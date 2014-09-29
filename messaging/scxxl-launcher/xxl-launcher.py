import sys, traceback
from eventclient import EventClient, info,error,debug


class Launcher(EventClient):

    def changed_origin(self, event_id, previous_id, current_id):
        info("Launcher.changed_origin") 
        info("event %s: CHANGED preferredOriginID" % event_id)
        info("    from %s" % previous_id)
        info("      to %s" % current_id)
        self.cleanup()


    def changed_magnitude(self, event_id, previous_id, current_id):
        info("Launcher.changed_magnitude") 
        info("event %s: CHANGED preferredMagnitudeID" % event_id)
        info("    from %s" % previous_id)
        info("      to %s" % current_id)
        self.cleanup()
    

app = Launcher()
sys.exit(app())
