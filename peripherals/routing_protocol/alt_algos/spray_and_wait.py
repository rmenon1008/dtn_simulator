"""
Contains the SprayAndWait class, which implements the "Spray-and-Wait" algorithm with Bundle expiration.

This algorithm has two parts:
- spray:  the node creates the bundle + sends it out to a random set of N nearby nodes.
- wait:  the N nodes which receive the bundle store it.  they then wait to actually run into the recipient node.
         once they run into the intended recipient node, they pass it on.
"""
import numpy as np

from agent.client_agent import ClientAgent
from peripherals.routing_protocol.routing_protocol_common import Bundle, handle_payload

class SprayAndWait:
    NUM_NODES_TO_SPRAY = 4  # To adjust how many nodes get "sprayed" with the message, modify this value.

    def __init__(self, node_id, model, agent):
        self.node_id = node_id
        self.model = model
        self.agent = agent
        self.bundle_sprays_map = {}  # key = bundle, val = list of nodes we already sprayed with the bundle.
        self.waiting_bundles = []
        self.num_bundle_sends = 0
        self.num_repeated_bundle_receives = 0
        self.num_bundle_reached_destination = 0

    """
    Receives bundles of data + holds on to them for spraying during `refresh()`.
    """
    def handle_bundle(self, bundle: Bundle):
        self.bundle_sprays_map[bundle] = []

    """
    Receives bundles and stores them for the "wait" part of the algorithm.
    """
    def handle_bundle_wait(self, bundle: Bundle):
        self.waiting_bundles.append(bundle)

    def handle_bundle_destination(self, bundle: Bundle):
        handle_payload(self.model, self.node_id, bundle.payload)
        self.num_bundle_reached_destination += 1

    """
    Refreshes the state of the SprayAndWait object.  Called by the simulation at each timestamp.  This means:
    - Checking if any stored Bundles have expired.
    - Spraying any Bundles which haven't hit their spray limits yet.
    - Checking to see if any "waiting" Bundles can be sent to their destination + sending them onto their dest if so.
    """
    def refresh(self):
        # remove any expired Bundles from the map of Bundles which we wish to spray.
        expired_spraying_list = []  # stores Bundles marked-for-spraying which have expired and need to delete after
                                    # iteration completes.
        for bundle in self.bundle_sprays_map.keys():
            if bundle.expiration_timestamp <= self.model.schedule.time:
                expired_spraying_list.append(bundle)
        # delete the expired Bundles from the map of Bundles which we wish to spray.
        for bundle in expired_spraying_list:
            del(self.bundle_sprays_map[bundle])

        # remove any expired Bundles from the list of waiting_bundles which we wish to propagate.
        self.waiting_bundles = [bundle for bundle in self.waiting_bundles
                                if bundle.expiration_timestamp > self.model.schedule.time]

        # find all nearby agents, shuffle their ordering (to ensure randomized spraying) and iterate thru them...
        neighbor_list = self.model.get_neighbors(self.agent)
        np.random.shuffle(neighbor_list)
        for neighbor_data in neighbor_list:
            # obtain the agent associated with the neighbor
            neighbor_agent = self.model.agents[neighbor_data["id"]]

            # ignore exchanging data with ClientAgents or RouterAgents we're not connected to.
            if isinstance(neighbor_agent, ClientAgent) or not neighbor_data["connected"]:
                continue

            # if we've reached this point, the neighbor is a connected RouterAgent.

            # spray this neighbor with whatever Bundles we have on-hand to spray.
            finished_spraying_list = []  # stores Bundles for which we have finished spraying and need to delete after
                                         # iteration completes.
            for bundle in self.bundle_sprays_map.keys():
                # if we already sprayed this neighbor with this bundle, move on to the next neighbor.
                if neighbor_agent in self.bundle_sprays_map[bundle]:
                    continue

                # otherwise, spray the neighbor w/ the bundle + record the spraying
                neighbor_agent.routing_protocol.handle_bundle_wait(bundle)
                self.bundle_sprays_map[bundle].append(neighbor_agent)
                self.num_bundle_sends += 1

                # if we've sprayed the max number of neighbors, delete the bundle from the map.
                if len(self.bundle_sprays_map[bundle]) == self.NUM_NODES_TO_SPRAY:
                    finished_spraying_list.append(bundle)
            # delete the Bundles we've finished spraying.
            for bundle in finished_spraying_list:
                del(self.bundle_sprays_map[bundle])

            # iterate thru your waiting bundles and see if the connected neighbor is the intended recipient of any of
            # them.
            finished_waiting_list = []  # stores Bundles which we have successfully transmitted to the dest and need to
                                        # delete from local storage after iteration completes.
            for bundle in self.waiting_bundles:
                if bundle.dest_id == neighbor_data["id"]:
                    neighbor_agent.routing_protocol.handle_bundle_destination(bundle)
                    finished_waiting_list.append(bundle)
                    self.num_bundle_sends += 1
            # delete the Bundles we've successfully transmitted from the waiting list.
            for bundle in finished_waiting_list:
                self.waiting_bundles.remove(bundle)


    """
    Called by the agent and sent to the visualization for simulation history log.
    """
    def get_state(self):
        return {
            "num_repeated_bundle_receives": self.num_repeated_bundle_receives,
            "num_bundle_sends": self.num_bundle_sends,
            "num_bundle_reached_destination": self.num_bundle_reached_destination,
            "num_stored_bundles": len(self.waiting_bundles),
        }
