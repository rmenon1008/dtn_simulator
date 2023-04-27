"""
Contains the peripheral used by an Epidemic agent to exchange 
- ClientPayload data with a client + 
- client mappings with other routers.
"""

from payload import ClientPayload

from peripherals.routing_protocol.routing_protocol_common import Bundle


class EpidemicPayloadHandler:
    def __init__(self, agent_id, model, epidemic_router):
        self.agent_id = agent_id
        self.model = model
        self.seen_payload_ids = set() # for deduping

        self.epidemic_router = epidemic_router  # the Epidemic router used to handle bundles

        self.num_payloads_received = 0 # from another router
        self.num_drops_picked_up = 0 # from the ground
        self.received_payloads = []
        self.received_payload_latencies = []

    """
    This is called when an Epidemic agent encounters a payload on the ground.
    - Note, this is not called if the payload on the ground is for itself (the model prevents agents from picking it up)
    - Immediately turns the payload into N bundles, where N is the # of agents in the simulation.
    - Hands these bundles over to the Epidemic protocol
    """
    def store_payload(self, payload: ClientPayload):
        if payload.get_identifier() in self.seen_payload_ids:
            return # ignore payloads we've already seen
        else:
            self.seen_payload_ids.add(payload.get_identifier())

        self.num_drops_picked_up += 1
        # Make a bundle targeted to the payload's target
        bundle_id = "bundle(routerdst[{}]creationtime[{}],{})".format(payload.dest_client_id, self.model.schedule.time, payload.get_identifier())
        bundle = Bundle(bundle_id, payload.dest_client_id, payload, self.model.schedule.time, self.model.model_params["bundle_lifespan"])
        self.epidemic_router.handle_bundle(bundle) # epidemic will store-and-forward
   
    """
    This is called when an Epidemic agent unwraps a bundle received from another agent,
    which was meant for itself.
    """
    def handle_payload(self, payload: ClientPayload):
        if payload.get_identifier() in self.seen_payload_ids:
            return # ignore payloads we've already seen
        else:
            self.seen_payload_ids.add(payload.get_identifier())

        self.num_payloads_received += 1
        latency = self.model.schedule.time - payload.creation_timestamp
        received_payload_serialized = {
            "drop_id": payload.drop_id,
            "source_id": payload.source_client_id,
            "dest_client_id": payload.dest_client_id,
            "expiration_timestamp": payload.expiration_timestamp,
            "creation_timestamp": payload.creation_timestamp,
            "delivery_timestamp": self.model.schedule.time,
            "delivery_latency": latency,
        }
        self.received_payloads.append(received_payload_serialized)
        self.received_payload_latencies.append(self.model.schedule.time - payload.creation_timestamp)

    """
    Refreshes the state of the RouterClientPayloadHandler.
    """
    def refresh(self):
        pass