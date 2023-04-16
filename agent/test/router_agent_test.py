"""
Tests the RouterAgent communications-focused backend code.

(This does not involve UI-focused content like movement or behavior.)
"""
from agent.client_agent import ClientAgent
import mesa, pytest
from mockito import mock, arg_that, verify, when

from agent.router_agent import RouterAgent
from payload import ClientMappingDictPayload

# test constants.
ROUTER_ID_0 = "r0"
ROUTER_ID_1 = "r1"
ROUTER_ID_2 = "r2"
CLIENT_ID_0 = "c0"
CLIENT_ID_1 = "c1"

@pytest.fixture()
def setup():
    # create the mocked model object.
    schedule = mesa.time.RandomActivation(mesa.Model())
    mocked_router_0_payload_handler = mock({"outgoing_payloads_to_send": {}, "payloads_received_for_client": {}, "client_router_mapping_dict": {}})
    mocked_router_1_payload_handler = mock()
    mocked_router_2_payload_handler = mock()
    mocked_client_0_payload_handler = mock()
    agents = {ROUTER_ID_1: mock({"payload_handler": mocked_router_1_payload_handler}, spec=RouterAgent),
              ROUTER_ID_2: mock({"payload_handler": mocked_router_2_payload_handler}, spec=RouterAgent),
              CLIENT_ID_0: mock({"payload_handler": mocked_client_0_payload_handler}, spec=ClientAgent)}
    mocked_model = mock({"schedule": schedule, "agents": agents, "model_params": {"model_speed_limit": 10}})

    # set up the RouterAgent.
    router_agent = RouterAgent(mocked_model, {"id": ROUTER_ID_0,
                                              "behavior": {
                                                  "type": "random"
                                              },
                                              "movement": "",
                                              "radio": {
                                                  "detection_thresh": 20,
                                                  "connection_thresh": 10}
                                              }
                               )

    # mock the peripherals in the ClientAgent
    router_agent.movement = mock()
    router_agent.dtn = mock()
    router_agent.radio = mock()
    router_agent.payload_handler = mocked_router_0_payload_handler

    yield mocked_model, \
          router_agent, \
          mocked_router_1_payload_handler, \
          mocked_router_2_payload_handler, \
          mocked_client_0_payload_handler

def test_step_exchanges_router_client_mappings(setup):
    mocked_model, \
    router_agent, \
    mocked_router_1_payload_handler, \
    mocked_router_2_payload_handler, \
    mocked_client_0_payload_handler = setup

    # set up the mocked model to return...
    # - Router 1 ID as nearby, but not connected.
    # - Router 2 ID as nearby and connected.
    # - Client 0 ID as nearby and connected.
    neighbor_data = [
        {
            "id": ROUTER_ID_1,
            "connected": False
        },
        {
            "id": ROUTER_ID_2,
            "connected": True
        },
        {
            "id": CLIENT_ID_0,
            "connected": True
        }
    ]
    when(mocked_model).get_neighbors(router_agent).thenReturn(neighbor_data)

    # move the router_agent forward one step, causing
    router_agent.step()

    # verify that...
    # - Router 0 was not interacted with (since it was not connected).
    # - Router 1 did a handshake (since it was connected).
    # - Client 1 was not interacted with (since it is not a router).
    # due to issues with mockito, we need to use a custom function here to match the ClientMappingDictPayload fed to the
    # handle_mapping_dict() call.
    def payload_match(other_payload: ClientMappingDictPayload):
        if other_payload.client_mappings == router_agent.payload_handler.client_router_mapping_dict:
            return True
        else:
            return False

    expected_payload = ClientMappingDictPayload(router_agent.payload_handler.client_router_mapping_dict)
    verify(mocked_router_1_payload_handler, times=0).handle_mapping_dict(...)
    verify(mocked_router_2_payload_handler, times=1).handle_mapping_dict(arg_that(lambda payload: payload_match(payload)))
    verify(mocked_client_0_payload_handler, times=0).handle_mapping_dict(...)
