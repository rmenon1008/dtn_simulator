"""
Contains a class which represents a HDTN bundle.
"""
from payload import Payload


class Bundle:
    EXPIRATION_LIFESPAN = 200  # defines how long a Bundle should exist before expiration.
                              # units = simulation steps

    def __init__(self, bundle_id, dest_id, payload:  Payload, creation_timestamp):
        self.bundle_id = bundle_id  # the id of the bundle
        self.dest_id = dest_id  # the id of the destination node
        self.payload = payload
        self.expiration_timestamp = creation_timestamp + self.EXPIRATION_LIFESPAN
        # TODO:  Add more params here + modify existing ones in the future!