"""
Tests for the "epidemic" algorithm.
"""
import mesa
from mockito import mock, when

from agent.router_agent import RouterAgent
from payload import Payload
from peripherals.routing_protocol.alt_algos.epidemic import Epidemic
from peripherals.routing_protocol.routing_protocol_common import Bundle

# Test constants.
ROUTER_ID_0 = 0
ROUTER_ID_1 = 1
ROUTER_ID_2 = 2
NONEXISTENT_ROUTER_ID = 3

def test_epidemic_propagation():
    # create the mocked model object.
    schedule = mesa.time.RandomActivation(mesa.Model())
    mocked_model = mock({"schedule": schedule, "agents": {}, "model_params": {"model_speed_limit": 10}})

    # create three nodes + their routing agents.
    r0 = mock(spec=RouterAgent)
    r1 = mock(spec=RouterAgent)
    r2 = mock(spec=RouterAgent)
    e0 = Epidemic(ROUTER_ID_0, mocked_model, r0)
    e1 = Epidemic(ROUTER_ID_1, mocked_model, r1)
    e2 = Epidemic(ROUTER_ID_2, mocked_model, r2)
    r0.routing_protocol = e0
    r1.routing_protocol = e1
    r2.routing_protocol = e2

    # update the agents inside the model to be using the Epidemic objects.
    agents = {
        ROUTER_ID_0: r0,
        ROUTER_ID_1: r1,
        ROUTER_ID_2: r2
    }

    mocked_model.agents = agents

    # mock the neighbor calls such that e0 is connected to e1, and e1 is connected to e2.
    r0_neighbor_data = [
        {
            "id": ROUTER_ID_1,
            "connected": True
        }
    ]
    r1_neighbor_data = [
        {
            "id": ROUTER_ID_2,
            "connected": True
        }
    ]
    when(mocked_model).get_neighbors(r0).thenReturn(r0_neighbor_data)
    when(mocked_model).get_neighbors(r1).thenReturn(r1_neighbor_data)
    when(mocked_model).get_neighbors(r2).thenReturn([])

    # feed a Bundle to e0.
    # NOTE:  The Bundle has a nonexistent router as its destination, ensuring that it will bounce around the network
    # until it expires.
    bundle = Bundle(0, NONEXISTENT_ROUTER_ID, Payload(), schedule.time)
    e0.handle_bundle(bundle)

    # verify that the Bundle is only at e0 (and not at e1 or e2).
    assert bundle in e0.known_bundles
    assert bundle not in e1.known_bundles
    assert bundle not in e2.known_bundles

    # refresh e0.
    e0.refresh()

    # verify that the Bundle is now at e1 (and not at e2).
    assert bundle in e0.known_bundles
    assert bundle in e1.known_bundles
    assert bundle not in e2.known_bundles

    # refresh e1.
    e1.refresh()

    # verify that the Bundle is now at e2.
    assert bundle in e0.known_bundles
    assert bundle in e1.known_bundles
    assert bundle in e2.known_bundles

    # move forward the time + refresh the Epidemics so that the bundle expires.
    for i in range(0, Bundle.EXPIRATION_LIFESPAN):
        schedule.step()
    e0.refresh()
    e1.refresh()
    e2.refresh()

    # verify that the Bundle is no longer stored in any of the Epidemics.
    assert bundle not in e0.known_bundles
    assert bundle not in e1.known_bundles
    assert bundle not in e2.known_bundles
