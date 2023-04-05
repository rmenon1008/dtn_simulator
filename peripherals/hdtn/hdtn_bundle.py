"""
Contains a class which represents a HDTN bundle.
"""


class Bundle:

    def __init__(self, bundle_id, dest_id):
        self.bundle_id = bundle_id  # the id of the bundle
        self.dest_id = dest_id  # the id of the destination node
        # TODO:  Add more params here + modify existing ones in the future!