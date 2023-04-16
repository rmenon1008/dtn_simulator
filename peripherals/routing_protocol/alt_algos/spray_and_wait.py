"""
Contains the SprayAndWait class, which implements SprayAndWait with expiration.

This algorithm has two parts:
- spray:  the node creates the bundle + sends it out to a random set of N nearby nodes.
- wait:  the N nodes which receive the bundle store it.  they then wait to actually run into the recipient node.
         once they run into the intended recipient node, they pass it on.
"""
from random import random

from agent.client_agent import ClientAgent
from peripherals.routing_protocol.routing_protocol_common import Bundle, handle_payload
from peripherals.routing_protocol.dtn.storage import Storage


class SprayAndWait:
    NUM_NODES_TO_SPRAY = 4

    def __init__(self, node_id, model):
        self.node_id = node_id
        self.model = model
        self.storage = Storage()
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
    Refreshes the state of the DTN object.  Called by the simulation at each timestamp.
    """
    def refresh(self):
        # remove any expired Bundles from the list of known_bundles which we wish to propagate.
        self.waiting_bundles = [bundle for bundle in self.waiting_bundles
                                if bundle.expiration_timestamp > self.model.schedule.time]

        # find all nearby agents, shuffle their ordering and iterate thru them...
        for neighbor_data in random.shuffle(self.model.get_neighbors(self)):
            # obtain the agent associated with the neighbor
            neighbor_agent = self.model.agents[neighbor_data["id"]]

            # ignore exchanging data with ClientAgents or RouterAgents we're not connected to.
            if isinstance(neighbor_agent, ClientAgent) or not neighbor_data["connected"]:
                continue

            # if we've reached this point, the neighbor is a connected RouterAgent.

            # spray this neighbor with whatever Bundles we have on-hand to spray.
            for bundle in self.bundle_sprays_map.keys():
                # if we already sprayed this neighbor with this bundle, move on to the next spray Bundle.
                if neighbor_agent in self.bundle_sprays_map[bundle]:
                    continue

                # otherwise, spray the neighbor w/ the bundle + record the spraying
                neighbor_agent.routing_protocol.handle_bundle_wait(bundle)
                self.bundle_sprays_map[bundle].append(neighbor_agent)
                self.num_bundle_sends += 1

                # if we've sprayed the max number of neighbors, delete the bundle from the map.
                if len(self.bundle_sprays_map[bundle]) == self.NUM_NODES_TO_SPRAY:
                    del(self.bundle_sprays_map[bundle])

            # iterate thru your waiting bundles and see if the connected neighbor is the intended recipient of any of
            # them.
            for bundle in self.waiting_bundles:
                if bundle.dest_id == neighbor_data["id"]:
                    neighbor_agent.routing_protocol.handle_bundle_destination(bundle)
                    self.num_bundle_sends += 1
                    del(self.waiting_bundles[bundle])


    """
    Called by the agent and sent to the visualization for simulation history log.
    """
    def get_state(self):
        return {
            "num_repeated_bundle_receives": self.num_repeated_bundle_receives,
            "num_bundle_sends": self.num_bundle_sends,
            "num_bundle_reached_destination": self.num_bundle_reached_destination
        }


    """
    Private function used to send the passed Bundle to the specified node in the network.
    """
    def __send_bundle(self, bundle: Bundle, dest_id):
        dest_dtn_node = self.model.get_dtn_object(dest_id)
        dest_dtn_node.handle_bundle(bundle)
