import sys

from peripherals.hdtn.schrouter import Schrouter


def test_simple_contact_plan_routing():
    # construct the Schrouter from a file.
    schrouter = Schrouter("peripherals/hdtn/test/test_contact_plans/contactPlan.json")

    # topology loaded from file:
    #      1
    #    /
    # 10
    #    \
    #      2

    # verify that both destinations were successfully added to the Schrouter.
    assert schrouter.check_any_availability(1)
    assert schrouter.check_any_availability(2)

    # get a dijkstra-computed route from source=10 to dest=1
    route = schrouter.get_best_route_dijkstra(10, 1)

    # assert that the route is a simple one-hop route
    assert len(route.hops) == 1
    assert route.hops[0].frm == 10
    assert route.hops[0].to == 1
    assert route.from_time == 10
    assert route.to_time == 20


def test_add_link_routing():
    # construct a Schrouter.
    schrouter = Schrouter()

    # add one link to the Schrouter.
    schrouter.add_link(source=0,
                       dest=1,
                       start_time=0,
                       end_time=sys.maxsize,
                       rate=100)

    # verify that the link to node 1 exists
    schrouter.check_link_availability(0, 1)


def test_remove_link_routing():
    # construct a Schrouter.
    schrouter = Schrouter()

    # add three links to the Schrouter:
    # - 0->1 w/ extremely late start_time.
    # - 0->2 w/ start_time of 0.
    # - 2->1 w/ start_time of 0.
    schrouter.add_link(source=0,
                       dest=1,
                       start_time=sys.maxsize - 1,
                       end_time=sys.maxsize,
                       rate=1)
    schrouter.add_link(source=0,
                       dest=2,
                       start_time=0,
                       end_time=sys.maxsize,
                       rate=100)
    schrouter.add_link(source=2,
                       dest=1,
                       start_time=0,
                       end_time=sys.maxsize,
                       rate=100)

    # verify that the links were successfully added to the Schrouter.
    assert schrouter.check_link_availability(0, 1)
    assert schrouter.check_link_availability(0, 2)
    assert schrouter.check_link_availability(2, 1)

    # obtain a route for 0->1.  it should route through 2 due to the early start_times.
    route_1 = schrouter.get_best_route_dijkstra(0, 1)
    assert len(route_1.hops) == 2
    assert route_1.hops[1].frm == 2
    assert route_1.hops[1].to == 1

    # remove the links from 0->2 and 2->1.
    schrouter.remove_all_links_for_node(2)

    # verify that the link was successfully removed.
    assert not schrouter.check_any_availability(2)

    # recompute the route from 0->1.  Since the 0->2 link was removed, the fastest
    # route should now be 0->1 instead of 0->2->1.
    route_2 = schrouter.get_best_route_dijkstra(0, 1)
    assert len(route_2.hops) == 1
    assert route_2.hops[0].frm == 0
    assert route_2.hops[0].to == 1
