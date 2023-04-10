"""
Contains the various payload types which are stored in Bundles and sent over the DTN network.

These payloads should store application-level data, not DTN-network-level data.
"""


"""
Base class.
"""
class Payload:
    pass


"""
Payload class containing a dict used to specify the client-router mappings for the client network.
"""
class ClientMappingDictPayload(Payload):
    def __init__(self, client_mappings:  dict):
        self.client_mappings = client_mappings


"""
Payload class containing the Bundle payload sent by the client.
"""
class ClientBundlePayload(Payload):
    def __init__(self, source_client_id, dest_client_id, seqnum):
        self.source_client_id = source_client_id
        self.dest_client_id = dest_client_id
        self.seqnum = seqnum

    """
    Returns a string which can be used to identify this payload. 
    """
    def get_identifier(self):
        return "src:  " + self.source_client_id + "\tdst:  " + self.dest_client_id + "\tseqnum:  " + self.seqnum


"""
Payload class for Bundles sent as Router beacons.
"""
class RouterBeaconPayload(Payload):
    def __init__(self, node_id, client_id_list: list):
        self.node_id = node_id
        self.client_id_list = client_id_list  # client_list = the list of clients currently connected.


"""
Payload class for Bundles sent as Client beacons.
"""
class ClientBeaconPayload(Payload):
    def __init__(self, client_id):
        self.client_id = client_id