"""
Contains the peripheral used by the client to exchange ClientPayload data with a router.

For high-level details on this handshake process, look at the README in this directory.
"""
from copy import copy

from payload import ClientPayload


class ClientClientPayloadHandler:

    def __init__(self, client_id, model):
        self.client_id = client_id
        self.model = model
        self.payloads_to_send = []  # elements are ClientPayloads.
        self.already_received_payload_ids = []  # elements are tuples of ('id', 'expiration timestamp').

        # vars used to record stats for measurements + evaluation
        self.num_payloads_sent = 0
        self.num_payloads_received = 0
        self.received_payload_latencies = []
        self.received_payloads = []
        self.num_drops_picked_up = 0

    """
    Stores a ClientPayload to be sent later over the network.
    """

    def store_payload(self, payload: ClientPayload):
        self.payloads_to_send.append(payload)
        self.already_received_payload_ids.append((payload.get_identifier(), payload.expiration_timestamp))
        self.num_drops_picked_up += 1

    """
    Executes "step 1" of the handshake process described in README.md.
    
    In this step, the client asks the router if there are any ClientPayloads waiting for the client.
        
    NOTE:  This method does _not_ verify that the device is in-range of the router--that needs to be done separately
           before this method is called.
    """

    def handshake_1(self, router_handler):
        router_handler.handshake_2(self)

    """
    Executes "step 3" of the handshake process described in README.md.
    
    In this step, the client looks at list, figures out which ClientPayloads it needs.  It then asks the router for 
    ClientPayloads it doesn't have.
    
    'payloads_for_client_metadata' = list of (payload_id, expiration timestamp) tuples

    NOTE:  This method does _not_ verify that the device is in-range of the router--that needs to be done separately
           before this method is called.
    """

    def handshake_3(self, router_handler, payloads_for_client_metadata: list):
        # if no payloads were sent by the router, skip to step 5.
        if len(payloads_for_client_metadata) == 0:
            self.handshake_5(router_handler, [])

        # otherwise, analyze the metadata received from the router.
        else:
            # extract the list of payload IDs we don't have from "payloads_for_client_metadata".
            desired_payload_ids = [payload_id for (payload_id, expiration_timestamp)
                                   in payloads_for_client_metadata
                                   if (payload_id, expiration_timestamp) not in self.already_received_payload_ids]
            # TODO: track metrics for # bundles ignored by client bc they were duplicates
            # ask the RouterClientPayloadHandler for the ClientPayloads associated with desired_payload_ids.
            router_handler.handshake_4(self, desired_payload_ids)

    """
    Executes "step 5" of the handshake process described in README.md.
    
    In this step, the client uploads to the router any ClientPayloads it needs to send.
    
    'payloads_for_client' = list of ClientPayloads

    NOTE:  This method does _not_ verify that the device is in-range of the router--that needs to be done separately
           before this method is called.
    """

    def handshake_5(self, router_handler, payloads_for_client: list):
        # store the metadata for the payloads from the router.
        for payload in payloads_for_client:
            self.already_received_payload_ids.append((payload.get_identifier(), payload.expiration_timestamp))
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

        # send the stored outgoing payloads to the router.
        # note: if false, this if statement ends the handshake early
        if len(self.payloads_to_send) > 0:
            router_handler.handshake_6(copy(self.payloads_to_send))
            self.num_payloads_sent += len(self.payloads_to_send)
            print("client", self.client_id, "is sending", len(self.payloads_to_send), "payload(s) to router", router_handler.router_id)
            # clear the list of payloads to send (since we've now sent them into the DTN network).
            self.payloads_to_send.clear()

    """
    Refreshes the state of the ClientClientPayloadHandler.
    
    In this case, it means going thru and removing all records we have for expired ClientPayloads.
    """

    def refresh(self):
        self.payloads_to_send = [payload for payload in
                                 self.payloads_to_send if payload.expiration_timestamp > self.model.schedule.time]
        self.already_received_payload_ids = [(payload, expiration_timestamp) for (payload, expiration_timestamp) in
                                             self.already_received_payload_ids if expiration_timestamp > self.model.schedule.time]
