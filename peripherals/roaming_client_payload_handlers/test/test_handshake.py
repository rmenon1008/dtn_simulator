"""
Used to test the handshake process between the RouterClientPayloadHandler and ClientClientPayloadHandler
"""
from payload import ClientPayload
from peripherals.roaming_client_payload_handlers.client_payload_handler import ClientClientPayloadHandler
from peripherals.roaming_client_payload_handlers.router_payload_handler import RouterClientPayloadHandler
from mockito import mock, spy2, verify

"""
Test constants.
"""
CLIENT_0_ID = 'c0'
CLIENT_1_ID = 'c1'
ROUTER_ID = 'r0'

"""
Tests the handshake process between the client and router.

This test case is setup such that the client already has one of the payloads that the router advertises,
and asserts that only the never-seen-before payloads are transferred.
"""
def test_handshake():
    # set up the router_handler and client_handler such that we can spy upon their handshake method calls.
    router_handler = RouterClientPayloadHandler(ROUTER_ID, mock(), mock())
    client_handler = ClientClientPayloadHandler(CLIENT_0_ID, mock())
    spy2(router_handler.handshake_2)
    spy2(router_handler.handshake_4)
    spy2(router_handler.handshake_6)
    spy2(client_handler.handshake_1)
    spy2(client_handler.handshake_3)
    spy2(client_handler.handshake_5)

    # set up the payloads used for testing.
    # c0 = the test client_handler
    # c1 = some other client_handler (we won't be initializing it though)
    c0_to_c1_payload_0 = ClientPayload(CLIENT_0_ID, CLIENT_1_ID, 0)
    c0_to_c1_payload_1 = ClientPayload(CLIENT_0_ID, CLIENT_1_ID, 1)
    c1_to_c0_payload_0 = ClientPayload(CLIENT_1_ID, CLIENT_0_ID, 0)
    c1_to_c0_payload_1 = ClientPayload(CLIENT_1_ID, CLIENT_0_ID, 1)

    # store the payloads stored in the router_handler which are meant for the client.
    router_handler.handle_payload(c1_to_c0_payload_0)
    router_handler.handle_payload(c1_to_c0_payload_1)

    # set up the list of payloads stored in the client_handler as already seen.
    client_already_received_payload_ids = [(c1_to_c0_payload_0.get_identifier(), c1_to_c0_payload_0.expiration_timestamp)]
    client_handler.already_received_payload_ids = client_already_received_payload_ids

    # set up the payloads_to_send field in the client_handler.
    client_payloads_to_send = [c0_to_c1_payload_0, c0_to_c1_payload_1]
    client_handler.payloads_to_send = client_payloads_to_send

    # initiate the handshake process.
    client_handler.handshake_1(router_handler)

    # verify that the handshake calls went as expected...

    # verify that handshake_2 was successfully called w/ the client_handler as the param.
    verify(router_handler, times=1).handshake_2(client_handler)

    # verify that handshake_3 was successfully called w/ the router_handler and a list of metadata as params.
    metadata_list = [(c1_to_c0_payload_0.get_identifier(), c1_to_c0_payload_0.expiration_timestamp),
                     (c1_to_c0_payload_1.get_identifier(), c1_to_c0_payload_1.expiration_timestamp)]
    verify(client_handler, times=1).handshake_3(router_handler, metadata_list)

    # verify that handshake_4 was successfully called w/ the client_handler and a list of desired payload IDs as params.
    # NOTE:  The list should only contain c1_to_c0_payload_1 since c1_to_c0_payload_0 is already in client_handler.
    verify(router_handler, times=1).handshake_4(client_handler, [c1_to_c0_payload_1.get_identifier()])

    # verify that handshake_5 was successfully called w/ the router_handler and a list of payloads as params.
    # NOTE:  The list should only contain c1_to_c0_payload_1 since c1_to_c0_payload_0 is already in client_handler.
    verify(client_handler, times=1).handshake_5(router_handler, [c1_to_c0_payload_1])

    # verify that handshake_6 was successfully called w/ the client_handler and a list of payloads to send as params.
    # NOTE:  The list should be [c0_to_c1_payload_0, c0_to_c1_payload_1]
    verify(router_handler, times=1).handshake_6([c0_to_c1_payload_0, c0_to_c1_payload_1])

    # verify that the payloads were successfully handled on both ends...

    # assert that router_handler's outgoing payload map stores the payloads received from client_handler.
    assert c0_to_c1_payload_0 in router_handler.outgoing_payloads_to_send
    assert c0_to_c1_payload_1 in router_handler.outgoing_payloads_to_send

    # assert that client_handler's received payload map stores the one new payload received from router_handler.
    assert (c1_to_c0_payload_1.get_identifier(), c1_to_c0_payload_1.expiration_timestamp) \
           in client_handler.already_received_payload_ids
