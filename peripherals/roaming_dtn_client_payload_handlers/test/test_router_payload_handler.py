"""
Used to test router-specific functions in the RouterClientPayloadHandler.
"""
from mockito import ANY, when, mock

import mesa

from payload import ClientPayload, ClientBeaconPayload
from peripherals.dtn.dtn import Dtn
from peripherals.roaming_dtn_client_payload_handlers.router_payload_handler import RouterClientPayloadHandler

ROUTER_ID = "r0"
CLIENT_ID_0 = "c0"
CLIENT_ID_1 = "c1"

"""
Tests that payloads stored-to-be-sent-to-a-client can expire.
"""
def test_handle_payload_refresh_payload_expires():
    # set up a dummy model object used by the RouterClientPayloadHandler object.
    schedule = mesa.time.RandomActivation(mesa.Model())
    dummy_model = mock({"schedule": schedule})

    # create the client_handler
    router_handler = RouterClientPayloadHandler(ROUTER_ID, dummy_model, Dtn(0, dummy_model))

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

    # create the client_handler
    router_handler = RouterClientPayloadHandler(ROUTER_ID, dummy_model, Dtn(0, dummy_model))

    # create a ClientBeaconPayload object.
    beacon_payload = ClientBeaconPayload(CLIENT_ID_0)

    # make the router handle the ClientBeaconPayload.
    router_handler.update_client_mapping(beacon_payload)

    # assert that the router stored a record connecting this handler to the client.
    assert ROUTER_ID in router_handler.client_router_mapping_dict.get(CLIENT_ID_0).keys()

    # move the schedule forward such that the entry expires.
    expire_timestamp = RouterClientPayloadHandler.CLIENT_MAPPING_TIMEOUT + 1
    for i in range(0, expire_timestamp):
        schedule.step()

    # refresh the router_handler.
    router_handler.refresh()

    # assert that the router stored a record connecting this handler to the client.
    assert ROUTER_ID not in router_handler.client_router_mapping_dict.get(CLIENT_ID_0)

# TODO:  Add test for sending stored outgoing payloads.

# TODO:  Add test for merging in mapping_dict_payload.