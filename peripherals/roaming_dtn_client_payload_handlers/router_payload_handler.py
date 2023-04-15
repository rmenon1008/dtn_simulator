"""
Contains the peripheral used by the router to exchange ClientPayload data with a client.

For high-level details on this handshake process, look at the README in this directory.
"""

from payload import ClientPayload, ClientMappingDictPayload, ClientBeaconPayload

from peripherals.dtn.hdtn_bundle import Bundle


class RouterClientPayloadHandler:
    CLIENT_MAPPING_TIMEOUT = 100  # defines how long a router-client should exist before it is considered expired.
                                  # units = simulation steps

    def __init__(self, router_id, model, dtn):
        self.router_id = router_id
        self.model = model
        self.payloads_received_for_client = {}  # map of client_ids->[list of ClientPayloads]
        self.outgoing_payloads_to_send = []  # stores payloads for us to attempt to send with each `refresh()`
        self.client_router_mapping_dict = {}  # dict of client_id->(dict of router_id->(expiration timestamp))
                                              # which represents DTN router(s) known to be associated with the specified
                                              # client.
        self.dtn = dtn  # the DTN object we can use to send out Bundles over the DTN network.

    """
    Updates that this router can connect to a particular client.
    
    This method should be called whenever a ClientBeaconPayload is received.
    """

    # TODO Have this method be called when ClientBeaconPayload is received by agent.
    def update_client_mapping(self, client_beacon_payload:  ClientBeaconPayload):
        # if we don't have _any_ entry for the client_id in our local map, add one with an empty list.
        if client_beacon_payload.client_id not in self.client_router_mapping_dict.keys():
            self.client_router_mapping_dict[client_beacon_payload.client_id] = {}

        # store a mapping of client->this router locally.
        self.client_router_mapping_dict.get(client_beacon_payload.client_id)[self.router_id] \
            = self.model.schedule.time + self.CLIENT_MAPPING_TIMEOUT

    """
    Handles mapping dicts received from other routers on the network.
    
    This means...
    - Adding new entries from the map in the received payload.
    - Updating expiration timestamps on-hand if the one stored in the received map is higher.
    """

    def handle_mapping_dict(self, mapping_dict_payload:  ClientMappingDictPayload):
        for client_id in mapping_dict_payload.client_mappings.keys():
            # if we don't have _any_ entry for the client_id in our local map, add one with an empty list.
            if client_id not in self.client_router_mapping_dict.keys():
                self.client_router_mapping_dict[client_id] = {}

            for router_id in mapping_dict_payload.client_mappings.get(client_id).keys():
                payload_map_expiration = mapping_dict_payload.client_mappings.get(client_id).get(router_id)
                current_expiration = self.client_router_mapping_dict.get(client_id).get(router_id)

                # if no such entry for the router_id is currently stored locally OR the locally stored entry has a
                # less-recent expiration timestamp, store the data from the payload map.
                if not current_expiration or payload_map_expiration > current_expiration:
                    self.client_router_mapping_dict.get(client_id)[router_id] = payload_map_expiration

    """
    Stores a payload to be sent later over the network.
    """

    def handle_payload(self, payload: ClientPayload):
        # if no list exists in the dict for the client, add one.
        if payload.dest_client_id not in self.payloads_received_for_client.keys():
            self.payloads_received_for_client[payload.dest_client_id] = []

        # store the payload in the dict for the client.
        self.payloads_received_for_client[payload.dest_client_id].append(payload)

    """
    Executes "step 2" of the handshake process described in README.md.
    
    In this step, the router returns a list of IDs of all ClientPayloads it has on-hand for the client.
        
    NOTE:  This method does _not_ verify that the device is in-range of the router--that needs to be done separately
           before this method is called.
    """
    def handshake_2(self, client_handler):
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

    def handshake_4(self, client_handler, desired_payload_ids: list):
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
        self.outgoing_payloads_to_send.extend(payloads_from_client)

    """
    Refreshes the state of the RouterClientPayloadHandler.

    In this case, it means going thru and removing all records we have for expired ClientPayloads.
    """
    def refresh(self):
        # remove expired payloads from payloads_received_for_client
        self.payloads_received_for_client = [payload for payload in self.payloads_received_for_client if payload.expiration_timestamp > self.model.schedule.time]

        # remove expired router-client mappings.
        for client_dict in self.client_router_mapping_dict.values():
            for router_id in self.client_router_mapping_dict.keys():
                if client_dict.get(router_id) <= self.model.schedule.time:
                    del(client_dict[router_id])

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
            router_ids_map = self.client_router_mapping_dict[payload.get_identifier]

            # if we have any router_id we can send to, send to them.
            if router_ids_map is not None:
                for router_id in router_ids_map.keys():
                    # create the Bundle.
                    bundle = Bundle(payload.get_identifier, router_id,payload)

                    # send the Bundle.
                    self.dtn.handle_bundle(bundle)

            # if we were unable to send out the payload, store it for later.
            else:
                unhandled_payloads.append(payload)

        # update the locally-stored payloads.
        self.outgoing_payloads_to_send = unhandled_payloads
