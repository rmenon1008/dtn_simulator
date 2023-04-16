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
    EXPIRATION_LIFESPAN = 200  # defines how long a Bundle should exist before expiration.
                              # units = simulation steps

    def __init__(self, bundle_id, dest_id, payload:  Payload, creation_timestamp):
        self.bundle_id = bundle_id  # the id of the bundle
        self.dest_id = dest_id  # the id of the destination node
        self.payload = payload
        self.expiration_timestamp = creation_timestamp + self.EXPIRATION_LIFESPAN
        # TODO:  Add more params here + modify existing ones in the future!