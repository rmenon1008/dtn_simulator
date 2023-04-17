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
    dummy_model = mock({"schedule": schedule})

    # setup the 5 nodes (0, 1, 2, 3, 4) + save them in the dtn_dict for easy access.
    # we set them up wrapped in a "spy" so we can easily peek into method call stats.
    dtn_dict = {}
    dtn_dict[0] = spy(Dtn(0, dummy_model))
    dtn_dict[1] = spy(Dtn(1, dummy_model))
    dtn_dict[2] = spy(Dtn(2, dummy_model))
    dtn_dict[3] = spy(Dtn(3, dummy_model))
    dtn_dict[4] = spy(Dtn(4, dummy_model))

    # wire-up the dummy_model to use the dtn_dict for lookups.
    when(dummy_model).get_routing_protocol_object(0).thenReturn(dtn_dict[0])
    when(dummy_model).get_routing_protocol_object(1).thenReturn(dtn_dict[1])
    when(dummy_model).get_routing_protocol_object(2).thenReturn(dtn_dict[2])
    when(dummy_model).get_routing_protocol_object(3).thenReturn(dtn_dict[3])
    when(dummy_model).get_routing_protocol_object(4).thenReturn(dtn_dict[4])

    # link-up the nodes as follows with the respective timestamps...
    # 0 -> 1:  @3-5
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

    # assert that the bundle was only sent to node 1.
    verify(dtn_dict[0], times=1).handle_bundle(...)
    verify(dtn_dict[1], times=1).handle_bundle(...)
    verify(dtn_dict[2], times=0).handle_bundle(...)

"""
Tests sending a Bundle when the best route is indirect.

(@timestamp = 0, the best route is 0->2->1)
"""
def test_handle_bundle_stores_bundle_sends_once_linked(setup):
    schedule, dtn_dict = setup

    # create the Bundle to send.
    bundle = Bundle(0, 4, Payload(), schedule.time)

    # have node 0 handle the Bundle.
    dtn_dict[0].handle_bundle(bundle)

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
    dtn_dict[3].add_contact(
        source=3,
        dest=4,
        start_time=0,
        end_time=sys.maxsize,
        rate=100
    )

    # assert that the new contact caused 4 to receive the bundle.
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
    dummy_model = mock({"schedule": schedule})

    # construct dtns w/ the Schrouter being configured from a file.
    dtn_dict = {}
    dtn_dict[10] = spy(Dtn(10, dummy_model, "peripherals/routing_protocol/test/dtn/test_contact_plans/contactPlan.json"))
    dtn_dict[1] = spy(Dtn(1, dummy_model, "peripherals/routing_protocol/test/dtn/test_contact_plans/contactPlan.json"))
    dtn_dict[2] = spy(Dtn(2, dummy_model, "peripherals/routing_protocol/test/dtn/test_contact_plans/contactPlan.json"))

    # wire-up the dummy_model to use the dtn_dict for lookups.
    when(dummy_model).get_routing_protocol_object(10).thenReturn(dtn_dict[10])
    when(dummy_model).get_routing_protocol_object(1).thenReturn(dtn_dict[1])
    when(dummy_model).get_routing_protocol_object(2).thenReturn(dtn_dict[2])

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

    # assert that the bundle was sent directly from node 10 to node 1.
    verify(dtn_dict[10], times=1).handle_bundle(...)
    verify(dtn_dict[1], times=1).handle_bundle(...)
    verify(dtn_dict[2], times=0).handle_bundle(...)
