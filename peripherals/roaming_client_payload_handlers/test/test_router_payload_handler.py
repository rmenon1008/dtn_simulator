"""
Used to test router-specific functions in the RouterClientPayloadHandler.
"""
import sys

from mockito import verify, mock, spy2, arg_that

import mesa

from payload import ClientPayload, ClientBeaconPayload, ClientMappingDictPayload
from peripherals.routing_protocol.dtn.dtn import Dtn
from peripherals.routing_protocol.routing_protocol_common import Bundle
from peripherals.roaming_client_payload_handlers.router_payload_handler import RouterClientPayloadHandler

"""
Test constants.
"""
ROUTER_ID_0 = "r0"
ROUTER_ID_1 = "r1"
CLIENT_ID_0 = "c0"
CLIENT_ID_1 = "c1"

"""
Tests that payloads stored-to-be-sent-to-a-client can expire.
"""
def test_handle_payload_refresh_payload_expires():
    # set up a dummy model object used by the RouterClientPayloadHandler object.
    schedule = mesa.time.RandomActivation(mesa.Model())
    dummy_model = mock({"schedule": schedule})

    # create the router_handler
    router_handler = RouterClientPayloadHandler(ROUTER_ID_0, dummy_model, Dtn(0, dummy_model))

    # create a payload object.
    payload = ClientPayload(CLIENT_ID_1, CLIENT_ID_0, dummy_model.schedule.time)

    # make the router handle the payload.
    router_handler.handle_payload(payload)

    # assert that the router stored the payload.
    assert payload in router_handler.payloads_received_for_client.get(CLIENT_ID_0)

    # move the schedule forward such that the payload expires.
    expire_timestamp = ClientPayload.EXPIRATION_LIFESPAN + 1
    for i in range(0, expire_timestamp):
        schedule.step()

    # refresh the router_handler.
    router_handler.refresh()

    # assert that the payload object is no longer present in the router_handler.
    assert payload not in router_handler.payloads_received_for_client.get(CLIENT_ID_0)


"""
Tests that payloads stored-to-be-sent-to-a-client can expire.
"""
def test_update_client_mapping_refresh_mapping_expires():
    # set up a dummy model object used by the RouterClientPayloadHandler object.
    schedule = mesa.time.RandomActivation(mesa.Model())
    dummy_model = mock({"schedule": schedule})

    # create the router_handler
    router_handler = RouterClientPayloadHandler(ROUTER_ID_0, dummy_model, Dtn(0, dummy_model))

    # create a ClientBeaconPayload object.
    beacon_payload = ClientBeaconPayload(CLIENT_ID_0)

    # make the router handle the ClientBeaconPayload.
    router_handler.update_client_mapping(beacon_payload)

    # assert that the router stored a record connecting this handler to the client.
    assert ROUTER_ID_0 in router_handler.client_router_mapping_dict.get(CLIENT_ID_0).keys()

    # move the schedule forward such that the entry expires.
    expire_timestamp = RouterClientPayloadHandler.CLIENT_MAPPING_TIMEOUT + 1
    for i in range(0, expire_timestamp):
        schedule.step()

    # refresh the router_handler.
    router_handler.refresh()

    # assert that the router stored a record connecting this handler to the client.
    assert ROUTER_ID_0 not in router_handler.client_router_mapping_dict.get(CLIENT_ID_0)


"""
Tests that with each refresh...
- Outgoing payloads with a known DTN route are sent out.
- Outgoing payloads without a known DTN route are stored.
- Outgoing payloads which are expired are thrown out.
"""
def test_send_stored_outgoing_payloads():
    # set up a dummy model object used by the RouterClientPayloadHandler object.
    schedule = mesa.time.RandomActivation(mesa.Model())
    dummy_model = mock({"schedule": schedule})
    dtn = Dtn(0, dummy_model)
    spy2(dtn.handle_bundle)

    # create the router_handler
    router_handler = RouterClientPayloadHandler(ROUTER_ID_0, dummy_model, dtn)

    # store a dict with a route to CLIENT_ID_1 in the router_handler.
    router_handler.client_router_mapping_dict = {CLIENT_ID_1: {ROUTER_ID_1: sys.maxsize}}

    # create + store the three payloads in the router_handler.
    known_payload = ClientPayload(CLIENT_ID_0, CLIENT_ID_1, schedule.time)
    unknown_payload = ClientPayload(CLIENT_ID_1, CLIENT_ID_0, schedule.time)
    expired_payload = ClientPayload(CLIENT_ID_0, CLIENT_ID_1, schedule.time - ClientPayload.EXPIRATION_LIFESPAN - 1)
    router_handler.handshake_6([known_payload, unknown_payload, expired_payload])

    # assert that the three payloads are in the router_handler.
    assert known_payload in router_handler.outgoing_payloads_to_send
    assert unknown_payload in router_handler.outgoing_payloads_to_send
    assert expired_payload in router_handler.outgoing_payloads_to_send

    # refresh the router_handler, triggering an attempt to send out the stored outgoing payloads.
    router_handler.refresh()

    # verify that known_payload was sent out.
    # due to issues with mockito, we need to use a custom function here to match the Bundle fed to the DTN call.
    def bundle_match(other_bundle: Bundle):
        if other_bundle.dest_id == ROUTER_ID_1 \
                and other_bundle.payload == known_payload \
                and other_bundle.bundle_id == known_payload.get_identifier():
            return True
        else:
            return False
    verify(dtn, times=1).handle_bundle(arg_that(lambda bundle: bundle_match(bundle)))

    # assert that unknown_payload was _not_ sent out.
    assert unknown_payload in router_handler.outgoing_payloads_to_send

    # assert that expired_payload was deleted.
    assert expired_payload not in router_handler.outgoing_payloads_to_send

"""
Tests that handle_mapping_dict successfully merges in ClientMappingDictPayloads as expected.

This means two particular cases:
- Adding new entries from the map in the received payload.
- Updating expiration timestamps on-hand if the one stored in the received map is higher.
"""
def test_handle_mapping_dict():
    # create the router_handler
    router_handler = RouterClientPayloadHandler(ROUTER_ID_0, mock(), mock())

    # add two entries to the dict:
    # - c1: r0: timestamp = 1
    # - c1: r1: timestamp = -1
    router_handler.client_router_mapping_dict = {CLIENT_ID_1: {ROUTER_ID_0: 1, ROUTER_ID_1: -1}}

    # create a dict as follows:
    # - c0: r0: timestamp = 0  <--- should make the handler store a new entry for c0, r0 in the dict.
    # - c1: r0: timestamp = 0  <--- should not affect the handler's stored timestamp for c1, r0
    # - c1: r1: timestamp = 1  <--- should make the handler update stored timestamp for c1, r1 to 1.
    mapping_dict_payload_dict = {CLIENT_ID_0: {ROUTER_ID_0: 0},
                                 CLIENT_ID_1: {ROUTER_ID_0: 0,
                                               ROUTER_ID_1: 1}}

    # create the payload.
    mapping_dict_payload = ClientMappingDictPayload(mapping_dict_payload_dict)

    # provide the handler with the payload, initiating the mapping dict update.
    router_handler.handle_mapping_dict(mapping_dict_payload)

    # assert that the mapping changes were processed correctly by the handler.  the dict should look as follows:
    # - c0: r0: timestamp = 0
    # - c1: r0: timestamp = 1
    # - c1: r1: timestamp = 1
    expected_mapping_dict_payload_dict = {CLIENT_ID_0: {ROUTER_ID_0: 0},
                                          CLIENT_ID_1: {ROUTER_ID_0: 1,
                                                        ROUTER_ID_1: 1}}
    assert expected_mapping_dict_payload_dict == router_handler.client_router_mapping_dict