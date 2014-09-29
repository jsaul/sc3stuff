import sys, traceback
from eventclient import EventClient, info,error,debug


class Launcher(EventClient):

    def changed_origin(self, event_id, previous_id, current_id):
        EventClient.changed_origin(self, event_id, previous_id, current_id)
        info("Launcher.changed_origin") 
        self.cleanup()


    def changed_magnitude(self, event_id, previous_id, current_id):
        EventClient.changed_origin(self, event_id, previous_id, current_id)
        info("Launcher.changed_magnitude") 
        self.cleanup()
    

app = Launcher()
sys.exit(app())
