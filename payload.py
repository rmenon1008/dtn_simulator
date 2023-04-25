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

    def __init__(self, drop_id, source_client_id, dest_client_id, creation_timestamp, lifespan):
        self.drop_id = drop_id
        self.source_client_id = source_client_id
        self.dest_client_id = dest_client_id
        self.expiration_timestamp = creation_timestamp + lifespan
        self.creation_timestamp = creation_timestamp # used for metrics, to calculate the total latency

    """
    Returns a string which can be used to identify this payload. 
    """
    def get_identifier(self):
        id_str = "payload(src[{}],dst[{}],exp[{}])".format(self.source_client_id, self.dest_client_id, self.expiration_timestamp)
        return id_str
    
    def serialize(self):
        return {
                "drop_id": self.drop_id,
                "source_id": self.source_client_id,
                "dest_client_id": self.dest_client_id,
                "expiration_timestamp": self.expiration_timestamp,
                "creation_timestamp": self.creation_timestamp,
            }


"""
Payload class for Bundles sent as Client beacons.
"""
class ClientBeaconPayload(Payload):
    def __init__(self, client_id):
        self.client_id = client_id