import sys

from peripherals.hdtn.schrouter import Schrouter


"""
Tests that the Schrouter can load contact plans from JSONs + successfully compute routes from them.
"""
def test_simple_contact_plan_routing():
    # NOTE:  This test will fail to find the JSON files if not run from the root directory using the `pytest` command.

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
    route = schrouter.get_best_route_dijkstra(10, 1, 0)

    # assert that the route is a simple one-hop route
    assert len(route.hops) == 1
    assert route.hops[0].frm == 10
    assert route.hops[0].to == 1
    assert route.from_time == 10
    assert route.to_time == 20


"""
Tests that contacts can be successfully added to the Schrouter.
"""
def test_add_contact_routing():
    # construct a Schrouter.
    schrouter = Schrouter()

    # add one contact to the Schrouter.
    schrouter.add_contact(source=0,
                          dest=1,
                          start_time=0,
                          end_time=sys.maxsize,
                          rate=100)

    # verify that the contact to node 1 exists
    schrouter.check_contact_availability(0, 1)


"""
Tests that contacts can be successfully removed from the Schrouter + that removing contacts can adjust
path computation.
"""
def test_remove_contact_routing():
    # construct a Schrouter.
    schrouter = Schrouter()

    # add three contacts to the Schrouter:
    # - 0->1 w/ extremely late start_time.
    # - 0->2 w/ start_time of 0.
    # - 2->1 w/ start_time of 0.
    schrouter.add_contact(source=0,
                          dest=1,
                          start_time=sys.maxsize - 1,
                          end_time=sys.maxsize,
                          rate=100)
    schrouter.add_contact(source=0,
                          dest=2,
                          start_time=0,
                          end_time=sys.maxsize,
                          rate=100)
    schrouter.add_contact(source=2,
                          dest=1,
                          start_time=0,
                          end_time=sys.maxsize,
                          rate=100)

    # verify that the contacts were successfully added to the Schrouter.
    assert schrouter.check_contact_availability(0, 1)
    assert schrouter.check_contact_availability(0, 2)
    assert schrouter.check_contact_availability(2, 1)

    # obtain a route for 0->1.  it should route through 2 due to the early start_times.
    route_1 = schrouter.get_best_route_dijkstra(0, 1, 0)
    assert len(route_1.hops) == 2
    assert route_1.hops[1].frm == 2
    assert route_1.hops[1].to == 1

    # remove the contacts from 0->2 and 2->1.
    schrouter.remove_all_contacts_for_node(2)

    # verify that the contact was successfully removed.
    assert not schrouter.check_any_availability(2)

    # recompute the route from 0->1.  Since the 0->2 contact was removed, the fastest
    # route should now be 0->1 instead of 0->2->1.
    route_2 = schrouter.get_best_route_dijkstra(0, 1, 0)
    assert len(route_2.hops) == 1
    assert route_2.hops[0].frm == 0
    assert route_2.hops[0].to == 1


"""
Tests that contacts can be successfully removed from the Schrouter via using a window of timestamps.
"""
def test_remove_contacts_in_time_window():
    # construct a Schrouter.
    schrouter = Schrouter()

    # add a contact to the Schrouter
    schrouter.add_contact(source=0,
                          dest=1,
                          start_time=0,
                          end_time=6,
                          rate=100)

    # verify that the contacts were successfully added to the Schrouter.
    assert schrouter.check_contact_availability_specific_time_window(0, 1, 0, 6)

    # adjust the Schrouter such that there is no contact between 0 and 1 from timestamps 3->4.
    # (this should result in two new contacts for 0-1:  one from timestamps 0->2 and one from timestamps 5->6
    schrouter.remove_contacts_in_time_window(0, 1, 3, 4)

    # verify that the original contact between 0 and 1 from timestamps 0->6 is now gone.
    assert not schrouter.check_contact_availability_specific_time_window(0, 1, 0, 6)

    # verify that there are now two contacts between 0 and 1:  one from 0->2 and another from 5->6.
    assert schrouter.check_contact_availability_specific_time_window(0, 1, 0, 2)
    assert schrouter.check_contact_availability_specific_time_window(0, 1, 5, 6)


"""
Tests that the router adjusts route computation based upon the provided starting timestamp.
"""
def test_routing_with_later_timestamp_use_faster_route():
    # construct a Schrouter.
    schrouter = Schrouter()

    # add three contacts to the Schrouter:
    # - 0->1 w/ start_time of 3.
    # - 0->2 w/ start_time of 0.
    # - 2->1 w/ start_time of 0.
    schrouter.add_contact(source=0,
                          dest=1,
                          start_time=3,
                          end_time=sys.maxsize,
                          rate=100)
    schrouter.add_contact(source=0,
                          dest=2,
                          start_time=0,
                          end_time=sys.maxsize,
                          rate=100)
    schrouter.add_contact(source=2,
                          dest=1,
                          start_time=0,
                          end_time=sys.maxsize,
                          rate=100)

    # verify that the contacts were successfully added to the Schrouter.
    assert schrouter.check_contact_availability(0, 1)
    assert schrouter.check_contact_availability(0, 2)
    assert schrouter.check_contact_availability(2, 1)

    # obtain a route for 0->1 w/ timestamp == 0.  It should route through 2 due to the early start_times.
    route_1 = schrouter.get_best_route_dijkstra(0, 1, 0)
    assert len(route_1.hops) == 2
    assert route_1.hops[1].frm == 2
    assert route_1.hops[1].to == 1

    # recompute the route from 0->1 w/ timestamp == 3.  Since we're computing with a later timestamp, the fastest
    # route should now be 0->1 instead of 0->2->1.
    route_2 = schrouter.get_best_route_dijkstra(0, 1, 3)
    assert len(route_2.hops) == 1
    assert route_2.hops[0].frm == 0
    assert route_2.hops[0].to == 1
