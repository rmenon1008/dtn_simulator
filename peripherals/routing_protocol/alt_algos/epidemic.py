"""
Contains the Epidemic class, which implements the "Epidemic" algorithm with Bundle expiration.
"""
from agent.client_agent import ClientAgent
from peripherals.routing_protocol.routing_protocol_common import Bundle, handle_payload


class Epidemic:

    def __init__(self, node_id, model, agent):
        self.node_id = node_id
        self.model = model
        self.agent = agent
        self.seen_bundle_ids = set()    # Contains bundle_id, used for deduping bundles
        self.curr_bundles = list()       # Bundles currently known by the Epidemic node + being sent out to other nodes.
                                        # Bundles can expire.
        self.num_bundle_sends = 0
        self.num_repeated_bundle_receives = 0
        self.num_bundle_reached_destination = 0

    """
    Receives + stores bundles of data for future propagation.
    """
    def handle_bundle(self, bundle: Bundle):
        if bundle.bundle_id in self.seen_bundle_ids:
            self.num_repeated_bundle_receives += 1
        else:
            self.seen_bundle_ids.add(bundle.bundle_id)
            # If this is for us, unpack the bundle and handle the payload accordingly
            if self.node_id == bundle.dest_id:
                handle_payload(self.model, self.node_id, bundle.payload)
                self.num_bundle_reached_destination += 1
            else: # else, store it so we can flood it to others
                self.curr_bundles.append(bundle)

    """
    Refreshes the state of the Epidemic object.  Called by the simulation at each timestamp.
    """
    def refresh(self):
        # remove any expired Bundles from the list of curr_bundles which we wish to propagate.
        self.curr_bundles = [bundle for bundle in self.curr_bundles
                              if bundle.expiration_timestamp > self.model.schedule.time]

        # find all nearby agents, spam them with your Bundles.
        for neighbor_data in self.model.get_neighbors(self.agent):
            # obtain the agent associated with the neighbor
            neighbor_agent = self.model.agents[neighbor_data["id"]]

            # ignore exchanging data with ClientAgents or RouterAgents we're not connected to.
            if isinstance(neighbor_agent, ClientAgent) or not neighbor_data["connected"]:
                continue

            # if we've reached this point, the neighbor is a connected RouterAgent.
            # send them all your Bundles.
            for bundle in self.curr_bundles:
                neighbor_agent.routing_protocol.handle_bundle(bundle)
                self.num_bundle_sends += 1


    """
    Called by the agent and sent to the visualization for simulation history log.
    """
    def get_state(self):
        curr_bundles_serialized = []
        for bundle in self.curr_bundles:
            curr_bundles_serialized.append(bundle.serialize())

        return {
            "total_repeated_bundle_recv": self.num_repeated_bundle_receives,
            "total_bundle_sends": self.num_bundle_sends,
            "total_bundle_reached_dest_router": self.num_bundle_reached_destination,
            "curr_num_stored_bundles": len(self.curr_bundles),
            "curr_stored_bundles": curr_bundles_serialized,
        }