import xmlrpc.server
import xmlrpc.client

class Worker
    def __init__(self, tracker_uri):
        self.tracker_uri = tracker_uri

    def register(self):
        with xmlrpc.client.ServerProxy(self.tracker_uri) as proxy:
