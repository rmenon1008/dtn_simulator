"""
Tests the ClientAgent communications-focused backend code.

(This does not involve UI-focused content like movement or behavior.)
"""
from agent.client_agent import ClientAgent, ClientAgentMode
import mesa, pytest
from mockito import mock, verify, when

from agent.router_agent import RouterAgent

# test constants.
ROUTER_ID_0 = "r0"
ROUTER_ID_1 = "r1"
CLIENT_ID_0 = "c0"
CLIENT_ID_1 = "c1"

@pytest.fixture()
def setup():
    # create the mocked model object.
    schedule = mesa.time.RandomActivation(mesa.Model())
    mocked_router_0_payload_handler = mock()
    mocked_router_1_payload_handler = mock()
    mocked_client_0_payload_handler = mock()
    mocked_client_1_payload_handler = mock()
    agents = {ROUTER_ID_0: mock({"payload_handler": mocked_router_0_payload_handler}, spec=RouterAgent),
              ROUTER_ID_1: mock({"payload_handler": mocked_router_1_payload_handler}, spec=RouterAgent),
              CLIENT_ID_1: mock({"payload_handler": mocked_client_1_payload_handler}, spec=ClientAgent)}
    mocked_model = mock({"schedule": schedule, "agents": agents, "model_params": {"model_speed_limit": 10}})

    # set up the ClientAgent.
    client_agent = ClientAgent(mocked_model, {"id": CLIENT_ID_0,
                                              "behavior": {
                                                  "type": "random"
                                              },
                                              "movement": {
                                                  "pattern": "fixed",
                                                  "speed": 0,
                                                  "options": {
                                                      "pos": (0, 0)
                                                  }
                                              },
                                              "radio": {
                                                  "detection_thresh": 20,
                                                  "connection_thresh": 10}
                                              }
                               )

    # mock the peripherals in the ClientAgent
    client_agent.movement = mock()
    client_agent.radio = mock()
    client_agent.payload_handler = mocked_client_0_payload_handler

    yield mocked_model, \
          client_agent, \
          mocked_router_0_payload_handler, \
          mocked_router_1_payload_handler, \
          mocked_client_0_payload_handler, \
          mocked_client_1_payload_handler


def test_step_emits_beacon(setup):
    mocked_model, \
    client_agent, \
    mocked_router_0_payload_handler, \
    mocked_router_1_payload_handler, \
    mocked_client_0_payload_handler, \
    mocked_client_1_payload_handler = setup

    # set up the mocked model to return...
    # - Router 0 ID as nearby, but not connected.
    # - Router 1 ID as nearby, but connected.
    # - Client 1 ID as nearby, but not connected.
    neighbor_data = [
        {
            "id": ROUTER_ID_0,
            "connected": False
        },
        {
            "id": ROUTER_ID_1,
            "connected": True
        },
        {
            "id": CLIENT_ID_1,
            "connected": False
        }
    ]
    when(mocked_model).get_neighbors(client_agent).thenReturn(neighbor_data)

    # make the client_agent advance to the next step (triggering the beacon emission code).
    client_agent.step()

    # verify that...
    # - Router 0 was sent a ClientBeacon.
    # - Router 1 was not sent a ClientBeacon (since it was connected).
    # - Client 1 was not sent a ClientBeacon (since it is not a router).
    verify(mocked_router_0_payload_handler, times=1).update_client_mapping(...)
    verify(mocked_router_1_payload_handler, times=0).update_client_mapping(...)
    verify(mocked_client_1_payload_handler, times=0).update_client_mapping(...)

def test_step_payload_lifecycle(setup):
    mocked_model, \
    client_agent, \
    mocked_router_0_payload_handler, \
    mocked_router_1_payload_handler, \
    mocked_client_0_payload_handler, \
    mocked_client_1_payload_handler = setup

    # set up the mocked_model to return that the client_agent has no neighbors.
    when(mocked_model).get_neighbors(client_agent).thenReturn([])

    # assert that the client_agent is in WORKING mode.
    assert client_agent.mode == ClientAgentMode.WORKING

    # transition from WORKING -> CONNECTION_ESTABLISHMENT
    for i in range(0, ClientAgent.RECONNECTION_INTERVAL):
        client_agent.step()
    assert client_agent.mode == ClientAgentMode.CONNECTION_ESTABLISHMENT

    # set up the mocked model to return...
    # - Router 0 ID as nearby, but not connected.
    # - Router 1 ID as nearby, but connected.
    # - Client 1 ID as nearby, but not connected.
    neighbor_data = [
        {
            "id": ROUTER_ID_0,
            "connected": False
        },
        {
            "id": ROUTER_ID_1,
            "connected": True
        },
        {
            "id": CLIENT_ID_1,
            "connected": False
        }
    ]
    when(mocked_model).get_neighbors(client_agent).thenReturn(neighbor_data)

    # transition from CONNECTION_ESTABLISHMENT -> CONNECTED + complete data transfer.
    client_agent.step()
    assert client_agent.mode == ClientAgentMode.CONNECTED

    # verify that...
    # - Router 0 was not interacted with (since it was not connected).
    # - Router 1 did a handshake (since it was connected).
    # - Client 1 was not interacted with (since it is not a router).
    verify(mocked_client_0_payload_handler, times=0).handshake_1(mocked_router_0_payload_handler)
    verify(mocked_client_0_payload_handler, times=1).handshake_1(mocked_router_1_payload_handler)
    verify(mocked_client_0_payload_handler, times=0).handshake_1(mocked_client_1_payload_handler)

    # transition from CONNECTED -> WORKING
    client_agent.step()
    assert client_agent.mode == ClientAgentMode.WORKING
