"""
Contains the peripheral used by the router to exchange ClientPayload data with a client.

For high-level details on this handshake process, look at the README in this directory.
"""

from payload import ClientPayload

from peripherals.dtn.hdtn_bundle import Bundle
from peripherals.roaming_dtn_client_payload_handlers.cilent_payload_handler import ClientClientPayloadHandler


class RouterClientPayloadHandler:

    def __init__(self, router_id, model, dtn):
        self.router_id = router_id
        self.model = model
        self.payloads_received_for_client = {}  # map of client_ids->[list of ClientPayloads]
        self.outgoing_payloads_to_send = []  # stores payloads for us to attempt to send with each `refresh()`

        # TODO:  Fully implement everything which has to do with this map.
        self.client_router_list_map = {}  # map of client_id->([list of router_ids], expiration_timestamp)
                                          # which represents DTN router(s) known to be associated with the specified client.
        self.dtn = dtn  # the DTN object we can use to send out Bundles over the DTN network.

    """
    Stores a payload to be sent later over the network.
    """

    def handle_payload(self, payload: ClientPayload, expiration_timestamp):
        self.payloads_received_for_client.append((payload, expiration_timestamp))

    """
    Executes "step 2" of the handshake process described in README.md.
    
    In this step, the router returns a list of IDs of all ClientPayloads it has on-hand for the client.
        
    NOTE:  This method does _not_ verify that the device is in-range of the router--that needs to be done separately
           before this method is called.
    """
    def handshake_2(self, client_handler:  ClientClientPayloadHandler):
        # get a list of metadata for the payloads waiting for the client.
        payloads_for_client_metadata = []
        for payload in self.payloads_received_for_client[client_handler.client_id]:
            payloads_for_client_metadata.append((payload.get_identifier(), payload.expiration_timestamp))

        # send the metadata list back to the client.
        client_handler.handshake_3(self, payloads_for_client_metadata)

    """
    Executes "step 4" of the handshake process described in README.md.
    
    In this step, the router sends the client a list containing the ClientPayloads requested by the client.

    'desired_payload_ids' = list of the ids correlating with the ClientPayloads desired by the client.

    NOTE:  This method does _not_ verify that the device is in-range of the router--that needs to be done separately
           before this method is called.
    """

    def handshake_4(self, client_handler:  ClientClientPayloadHandler, desired_payload_ids: list):
        # obtain the payloads the client wants.
        payloads_for_client = [payload for payload
                              in self.payloads_received_for_client[client_handler.client_id]
                              if payload.get_identifier()
                              in desired_payload_ids]

        # send the payloads to the client.
        client_handler.handshake_5(self, payloads_for_client)


    """
    Executes "step 6" of the handshake process described in README.md.

    In this step, the router returns a list of IDs of all ClientPayloads it has on-hand for the client.

    'payloads_from_client' = list of ClientPayloads being sent from the client.

    NOTE:  This method does _not_ verify that the device is in-range of the router--that needs to be done separately
           before this method is called.
    """

    def handshake_6(self, payloads_from_client: list):
        # store the payloads so that they can be sent out at the next refresh.
        self.outgoing_payloads_to_send.append(payloads_from_client)

    """
    Refreshes the state of the RouterClientPayloadHandler.

    In this case, it means going thru and removing all records we have for expired ClientPayloads.
    """
    def refresh(self):
        # remove expired payloads from payloads_received_for_client
        self.payloads_received_for_client = [payload for payload in self.payloads_received_for_client if payload.expiration_timestamp > self.model.schedule.time]

        # attempt to send all stored outgoing payloads.
        self.__try_send_stored_outgoing_payloads()

    """
    Attempts to send each currently-stored payload.
    
    If the payload cannot be sent, it's kept locally as long as it hasn't expired.
    """
    def __try_send_stored_outgoing_payloads(self):
        unhandled_payloads = []
        for payload in self.outgoing_payloads_to_send:
            # if payload has expired, do not process it.
            if payload.expiration_timestamp > self.model.schedule.time:
                continue

            # see if we can get any router_id for a router associated with the payload's client
            router_ids = self.client_router_list_map[payload.get_identifier]

            # if we have any router_id we can send to, send to them.
            if router_ids is not None and router_ids.len > 0:
                for router_id in router_ids:
                    # create the Bundle.
                    bundle = Bundle(payload.get_identifier, router_id,payload)

                    # send the Bundle.
                    self.dtn.handle_bundle(bundle)

            # if we were unable to send out the payload, store it for later.
            else:
                unhandled_payloads.append(payload)

        # update the locally-stored payloads.
        self.outgoing_payloads_to_send = unhandled_payloads
