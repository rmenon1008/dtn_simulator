"""
Tests for the "spray-and-wait" algorithm.
"""
import mesa
import pytest
from mockito import mock, when

from agent.router_agent import RouterAgent
from payload import Payload
from peripherals.routing_protocol.alt_algos.spray_and_wait import SprayAndWait
from peripherals.routing_protocol.routing_protocol_common import Bundle

@pytest.fixture()
def setup():
    # create the mocked model object.
    schedule = mesa.time.RandomActivation(mesa.Model())
    mocked_model = mock({"schedule": schedule, "agents": {}, "model_params": {"model_speed_limit": 10}})

    # create five nodes + their routing agents.
    s_dict = {}  # stores SprayAndWait objects.  k = node_id = "#".  v = SprayAndWait obj.
    r_dict = {}  # stores mocked RouterAgent objects.  k = node_id = "#".  v = mocked RouterAgent obj.
    for i in range(0, SprayAndWait.NUM_NODES_TO_SPRAY + 1):
        r = mock(spec=RouterAgent)
        s = SprayAndWait(i, mocked_model, r)
        r.routing_protocol = s
        s_dict[i] = s
        r_dict[i] = r

    # update the agents dict inside the model to be using the SprayAndWait objects.
    mocked_model.agents = r_dict

    # mock the neighbor calls such that r0 is connected to all RouterAgents EXCEPT the last one.
    r0_neighbor_data = []
    for i in range(0, SprayAndWait.NUM_NODES_TO_SPRAY):
        r0_neighbor_data.append(
            {
                "id": i,
                "connected": True
            }
        )

    # store in the model the neighbors for each node.
    #
    # NOTE:  All RouterAgents should have no neighbors except r0.
    when(mocked_model).get_neighbors(r_dict[0]).thenReturn(r0_neighbor_data)
    for i in range(1, SprayAndWait.NUM_NODES_TO_SPRAY + 1):
        when(mocked_model).get_neighbors(r_dict[i]).thenReturn([])

    yield schedule, mocked_model, r_dict, s_dict

def test_spray_and_wait_propagation(setup):
    schedule, mocked_model, r_dict, s_dict = setup

    # feed a Bundle to s0.
    # NOTE:  The Bundle has the last RouterAgent as its destination + r0 is not connected to the last RouterAgent,
    # so the Bundle will be held by all other nodes before reaching its destination.
    bundle = Bundle(0, SprayAndWait.NUM_NODES_TO_SPRAY, Payload(), schedule.time)
    s_dict[0].handle_bundle(bundle)

    # assert that the Bundle is in s0 and ready to be sprayed.
    assert bundle in s_dict[0].bundle_sprays_map.keys()

    # refresh s0.
    s_dict[0].refresh()

    # assert that the Bundle is no longer present in s0 (since it was sprayed out the max number of times) and is
    # now sprayed to all other nodes EXCEPT the destination.
    assert bundle not in s_dict[0].bundle_sprays_map.keys()
    for i in range(1, SprayAndWait.NUM_NODES_TO_SPRAY - 1):
        assert bundle in s_dict[i].waiting_bundles

    # connect r1 to the destination via modifying the get_neighbor call to the mocked_model.
    r1_neighbor_data = [
        {
            "id": SprayAndWait.NUM_NODES_TO_SPRAY,
            "connected": True
        }
    ]
    when(mocked_model).get_neighbors(r_dict[1]).thenReturn(r1_neighbor_data)

    # refresh s1.
    s_dict[1].refresh()

    # assert that the bundle reached the destination via s1.
    assert bundle not in s_dict[1].waiting_bundles  # the bundle should no longer be present in s1.
    assert 1 == s_dict[SprayAndWait.NUM_NODES_TO_SPRAY].num_bundle_reached_destination  # the bundle should have
                                                                                        # registered as successfully
                                                                                        # reaching the destination.

def test_spray_and_wait_expiration(setup):
    schedule, mocked_model, r_dict, s_dict = setup

    # feed a Bundle to s0.
    # NOTE:  The Bundle has the last RouterAgent as its destination + r0 is not connected to the last RouterAgent,
    # so the Bundle will be held by all other nodes before reaching its destination.
    bundle_1 = Bundle(0, SprayAndWait.NUM_NODES_TO_SPRAY, Payload(), schedule.time)
    s_dict[0].handle_bundle(bundle_1)

    # assert that the Bundle is in s0 and ready to be sprayed.
    assert bundle_1 in s_dict[0].bundle_sprays_map.keys()

    # refresh s0.
    s_dict[0].refresh()

    # assert that the Bundle is no longer present in s0 (since it was sprayed out the max number of times) and is
    # now sprayed to all other nodes EXCEPT the destination.
    assert bundle_1 not in s_dict[0].bundle_sprays_map.keys()
    for i in range(1, SprayAndWait.NUM_NODES_TO_SPRAY - 1):
        assert bundle_1 in s_dict[i].waiting_bundles

    # disconnect r0 from all other routers via modifying the get_neighbor call to the mocked_model.
    when(mocked_model).get_neighbors(r_dict[0]).thenReturn([])

    # feed a new second Bundle to s0.
    # NOTE:  The Bundle has the last RouterAgent as its destination.  r0 is no longer connected to any RouterAgent,
    #        so the Bundle will be held by s0 until it expires.
    bundle_2 = Bundle(0, SprayAndWait.NUM_NODES_TO_SPRAY, Payload(), schedule.time)
    s_dict[0].handle_bundle(bundle_2)

    # assert that the second Bundle is in s0 and ready to be sprayed.
    assert bundle_2 in s_dict[0].bundle_sprays_map.keys()

    # advance the clock so that the bundle_1 and bundle_2 expire.
    for i in range(0, Bundle.EXPIRATION_LIFESPAN):
        schedule.step()

    # refresh all s# objects.
    for i in range(0, SprayAndWait.NUM_NODES_TO_SPRAY):
        s_dict[i].refresh()

    # assert that bundle_2 is no longer present in s0's bundle_sprays_map (since it expired).
    assert bundle_2 not in s_dict[0].bundle_sprays_map.keys()

    # assert that bundle_1 is not present in any s#'s waiting_bundles list (since it expired).
    for i in range(1, SprayAndWait.NUM_NODES_TO_SPRAY - 1):
        assert bundle_1 not in s_dict[i].waiting_bundles
