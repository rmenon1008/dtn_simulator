"""
Contains a class which represents a HDTN bundle.
"""
from payload import Payload


class Bundle:

    def __init__(self, bundle_id, dest_id, payload:  Payload):
        self.bundle_id = bundle_id  # the id of the bundle
        self.dest_id = dest_id  # the id of the destination node
        self.payload = payload
        # TODO:  Add more params here + modify existing ones in the future!