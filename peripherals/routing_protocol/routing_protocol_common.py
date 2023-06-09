"""
Contains content shared across the networking protocol classes.
"""
from payload import Payload, ClientMappingDictPayload, ClientPayload, ClientBeaconPayload


"""
Used to easily process + handle payloads on the destination routing nodes.
"""
def handle_payload(model, local_node_id, payload):
    # handle different payload types differently.
    if isinstance(payload, ClientMappingDictPayload):
        model.get_client_payload_handler_object(local_node_id).handle_mapping_dict(payload)
    elif isinstance(payload, ClientPayload):
        model.get_client_payload_handler_object(local_node_id).handle_payload(payload)
    elif isinstance(payload, ClientBeaconPayload):
        model.get_client_payload_handler_object(local_node_id).update_client_mapping(payload)
    else:
        pass
    # add more cases here if new payload types are added which need special router-level handling!


"""
Represents a Bundle on the network.
"""
class Bundle:
    def __init__(self, bundle_id, dest_id, payload:  Payload, creation_timestamp, lifespan):
        self.bundle_id = bundle_id  # the id of the bundle
        self.dest_id = dest_id  # the id of the destination node
        self.payload = payload
        self.expiration_timestamp = creation_timestamp + lifespan
        self.creation_timestamp = creation_timestamp
        #  add more params here + modify existing ones in the future as necessary.

    def serialize(self):
        return {
            "bundle_id": self.bundle_id,
            "dest_id": self.dest_id,
            "expiration_timestamp": self.expiration_timestamp,
            "creation_timestamp": self.creation_timestamp,
            "payload": self.payload.serialize()
        }