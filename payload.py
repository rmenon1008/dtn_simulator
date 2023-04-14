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
The mappings should be client_id->(dict of router_id->(expiration timestamp)).
"""
class ClientMappingDictPayload(Payload):
    def __init__(self, client_mappings:  dict):
        self.client_mappings = client_mappings


"""
Payload class containing the payloads sent between the clients on the network.
"""
class ClientPayload(Payload):
    EXPIRATION_LIFESPAN = 20  # defines how long a ClientPayload should exist before expiration.
                              # units = simulation steps

    def __init__(self, source_client_id, dest_client_id, seqnum):
        self.source_client_id = source_client_id
        self.dest_client_id = dest_client_id
        self.seqnum = seqnum
        self.expiration_timestamp = seqnum + ClientPayload.EXPIRATION_LIFESPAN

    """
    Returns a string which can be used to identify this payload. 
    """
    def get_identifier(self):
        return "src:  " + self.source_client_id + "\tdst:  " + self.dest_client_id + "\tseqnum:  " + self.seqnum


"""
Payload class for Bundles sent as Router beacons.
"""
class RouterBeaconPayload(Payload):
    def __init__(self, node_id):
        self.node_id = node_id


"""
Payload class for Bundles sent as Client beacons.
"""
class ClientBeaconPayload(Payload):
    def __init__(self, client_id):
        self.client_id = client_id