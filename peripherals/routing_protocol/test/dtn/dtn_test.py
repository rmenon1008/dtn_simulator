import sys
from mockito import mock, spy, verify, when

import pytest
import mesa

from payload import Payload
from peripherals.routing_protocol.dtn.dtn import Dtn
from peripherals.routing_protocol.routing_protocol_common import Bundle

"""
Method used to setup DTN objects for this file's unit tests.
"""
@pytest.fixture()
def setup():
    # setup a dummy model object used by the DTN objects.
    schedule = mesa.time.RandomActivation(mesa.Model())
    agents_dict = dict()
    dummy_model = mock({"schedule": schedule, "agents": agents_dict})

    # setup the 5 nodes (0, 1, 2, 3, 4) + save them in the dtn_dict for easy access.
    # we set them up wrapped in a "spy" so we can easily peek into method call stats.
    dtn_dict = {}
    dtn_dict[0] = spy(Dtn(0, dummy_model))
    dtn_dict[1] = spy(Dtn(1, dummy_model))
    dtn_dict[2] = spy(Dtn(2, dummy_model))
    dtn_dict[3] = spy(Dtn(3, dummy_model))
    dtn_dict[4] = spy(Dtn(4, dummy_model))

    dummy_agent0 = mock({"routing_protocol": dtn_dict[0]})
    dummy_agent1 = mock({"routing_protocol": dtn_dict[1]})
    dummy_agent2 = mock({"routing_protocol": dtn_dict[2]})
    dummy_agent3 = mock({"routing_protocol": dtn_dict[3]})
    dummy_agent4 = mock({"routing_protocol": dtn_dict[4]})
    agents_dict[0] = dummy_agent0
    agents_dict[1] = dummy_agent1
    agents_dict[2] = dummy_agent2
    agents_dict[3] = dummy_agent3
    agents_dict[4] = dummy_agent4

    neighbors_for_0 = [{"id": 1, "connected": True}, 
                       {"id": 2, "connected": True}, 
                       {"id": 3, "connected": True}, 
                       {"id": 4, "connected": True}]
    neighbors_for_1 = [{"id": 0, "connected": True}, 
                       {"id": 2, "connected": True}, 
                       {"id": 3, "connected": True}, 
                       {"id": 4, "connected": True}]
    neighbors_for_2 = [{"id": 0, "connected": True}, 
                       {"id": 1, "connected": True}, 
                       {"id": 3, "connected": True}, 
                       {"id": 4, "connected": True}]
    neighbors_for_3 = [{"id": 0, "connected": True}, 
                       {"id": 1, "connected": True}, 
                       {"id": 2, "connected": True}, 
                       {"id": 4, "connected": True}]
    neighbors_for_4 = [{"id": 0, "connected": True}, 
                       {"id": 1, "connected": True}, 
                       {"id": 2, "connected": True}, 
                       {"id": 3, "connected": True}]

    when(dummy_model).get_neighbors(dummy_agent0).thenReturn(neighbors_for_0)
    when(dummy_model).get_neighbors(dummy_agent1).thenReturn(neighbors_for_1)
    when(dummy_model).get_neighbors(dummy_agent2).thenReturn(neighbors_for_2)
    when(dummy_model).get_neighbors(dummy_agent3).thenReturn(neighbors_for_3)
    when(dummy_model).get_neighbors(dummy_agent4).thenReturn(neighbors_for_4)

    # link-up the nodes as follows with the respective timestamps...
    # 0 -> 1:  @3-inf
    # 0 -> 2:  @0->inf
    # 2 -> 1:  @0->inf
    # 0 -> 3:  @0->inf
    for node in dtn_dict.values():
        node.add_contact(0, 1, 3, sys.maxsize, 100)
        node.add_contact(0, 2, 0, sys.maxsize, 100)
        node.add_contact(2, 1, 0, sys.maxsize, 100)
        node.add_contact(0, 3, 0, sys.maxsize, 100)

    yield schedule, dtn_dict


"""
Tests sending a Bundle when the best route is an indirect one with more hops.

(@timestamp = 0, the best route is 0->2->1)
"""
def test_handle_bundle_best_route_indirect(setup):
    schedule, dtn_dict = setup

    # create the Bundle to send.
    bundle = Bundle(0, 1, Payload(), schedule.time)

    # have node 0 handle the Bundle.
    dtn_dict[0].handle_bundle(bundle)
    dtn_dict[0].refresh() # forward to 2
    dtn_dict[2].refresh() # forward to 1

    # assert that the bundle was sent to node 2 and node 1.
    verify(dtn_dict[0], times=1).handle_bundle(...)
    verify(dtn_dict[2], times=1).handle_bundle(...)
    verify(dtn_dict[1], times=1).handle_bundle(...)

"""
Tests sending a Bundle when the best route switches from an indirect one to a direct one.

@timestamp = 0, the best route is 0->2->1
@timestamp = 3, the best route is 0->1
"""
def test_handle_bundle_best_route_direct(setup):
    schedule, dtn_dict = setup


    # create the Bundle to send.
    bundle = Bundle(0, 1, Payload(), schedule.time)

    # move all Dtn objects forward to timestamp=3
    schedule.step()
    schedule.step()
    schedule.step()

    # have node 0 handle the Bundle.
    dtn_dict[0].handle_bundle(bundle)
    dtn_dict[0].refresh() # forward to 1, calls 1.handle_bundle()
    dtn_dict[1].refresh() # does nothing, assert times=1
    dtn_dict[2].refresh() # does nothing, assert times=0

    # assert that the bundle was only sent to node 1.
    verify(dtn_dict[0], times=1).handle_bundle(...)
    verify(dtn_dict[1], times=1).handle_bundle(...)
    verify(dtn_dict[2], times=0).handle_bundle(...)

"""
Tests sending a Bundle when the best route is indirect.

(@timestamp = 0, in default contact plan there is no route to 4)
after adding contact...
(@timestamp = 0, best route is 0->3->4)
"""
def test_handle_bundle_stores_bundle_sends_once_linked(setup):
    schedule, dtn_dict = setup

    # create the Bundle to send.
    bundle = Bundle(0, 4, Payload(), schedule.time)

    # have node 0 handle the Bundle.
    dtn_dict[0].handle_bundle(bundle)
    dtn_dict[0].refresh() # attempt to forward, but there's not a route

    # assert that the bundle was not sent to node 4.
    verify(dtn_dict[0], times=1).handle_bundle(...)
    verify(dtn_dict[4], times=0).handle_bundle(...)

    # link-up node 3 and node 4 in node 0 and node 3's contact plans.
    dtn_dict[0].add_contact(
        source=3,
        dest=4,
        start_time=0,
        end_time=sys.maxsize,
        rate=100
    )
    dtn_dict[0].refresh() # successfully forward to 3
    dtn_dict[3].add_contact(
        source=3,
        dest=4,
        start_time=0,
        end_time=sys.maxsize,
        rate=100
    )
    dtn_dict[3].refresh() # successfully forward to 4

    # assert that the new contact caused 4 to receive the bundle.
    verify(dtn_dict[0], times=1).handle_bundle(...)
    verify(dtn_dict[3], times=1).handle_bundle(...)
    verify(dtn_dict[4], times=1).handle_bundle(...)


"""
Tests that the Dtn object can successfully use the Schrouter to load contact plans from JSONs + successfully compute 
routes from them.
"""
def test_construct_dtn_from_json():
    # NOTE:  This test will fail to find the JSON files if not run from the root directory using the `pytest` command.

    # setup a dummy model object used by the DTN objects.
    schedule = mesa.time.RandomActivation(mesa.Model())
    agents_dict = dict()
    dummy_model = mock({"schedule": schedule, "agents": agents_dict})


    # construct dtns w/ the Schrouter being configured from a file.
    dtn_dict = {}
    dtn_dict[10] = spy(Dtn(10, dummy_model, "peripherals/routing_protocol/test/dtn/test_contact_plans/contactPlan.json"))
    dtn_dict[1] = spy(Dtn(1, dummy_model, "peripherals/routing_protocol/test/dtn/test_contact_plans/contactPlan.json"))
    dtn_dict[2] = spy(Dtn(2, dummy_model, "peripherals/routing_protocol/test/dtn/test_contact_plans/contactPlan.json"))

    dummy_agent10 = mock({"routing_protocol": dtn_dict[10]})
    dummy_agent1 = mock({"routing_protocol": dtn_dict[1]})
    dummy_agent2 = mock({"routing_protocol": dtn_dict[2]})
    agents_dict[10] = dummy_agent10
    agents_dict[1] = dummy_agent1
    agents_dict[2] = dummy_agent2
    neighbors_for_10 = [{"id": 1, "connected": True}, {"id": 2, "connected": True}]

    when(dummy_model).get_neighbors(dummy_agent10).thenReturn(neighbors_for_10)

    # topology loaded from file:
    #      1
    #    /
    # 10
    #    \
    #      2

    # create a Bundle to send from 10 to 1.
    bundle = Bundle(10, 1, Payload(), schedule.time)

    # have node 10 handle the Bundle.
    dtn_dict[10].handle_bundle(bundle)
    dtn_dict[10].refresh() # forward to 1

    # assert that the bundle was sent directly from node 10 to node 1.
    verify(dtn_dict[10], times=1).handle_bundle(...)
    verify(dtn_dict[1], times=1).handle_bundle(...)
    verify(dtn_dict[2], times=0).handle_bundle(...)
