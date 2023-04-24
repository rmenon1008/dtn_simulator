"""
Contains the Dtn class, which is a simplified implementation of HDTN.
"""
import string

from peripherals.routing_protocol.routing_protocol_common import Bundle, handle_payload
from peripherals.routing_protocol.dtn.storage import Storage
from peripherals.routing_protocol.dtn.schrouter import Schrouter
from agent.client_agent import ClientAgent


class Dtn:

    def __init__(self, node_id, model, contact_plan_json_filename: string = None):
        self.node_id = node_id

        self.model = model

        self.storage = Storage(self.model)

        # if no filename is provided, "None" will be supplied to the Schrouter and an empty Schrouter will be created.
        self.schrouter = Schrouter(contact_plan_json_filename)

        # metrics used for easy algo performance comparison
        self.num_bundle_sends = 0
        self.num_repeated_bundle_receives = 0
        self.num_bundle_reached_destination = 0

    """
    Receives + handles bundles of data.
    
    This effectively behaves akin to the `ingress` + `egress` modules in HDTN.
    """
    def handle_bundle(self, bundle: Bundle):
        print("Agent {} received bundle {}".format(
            self.node_id, bundle))

        # Ingress
        # Process received bundle.

        # if this is the intended destination for the bundle, "receive" it and exit.
        if bundle.dest_id == self.node_id:
            print("this bundle was for me, router", self.node_id)
            handle_payload(self.model, self.node_id, bundle.payload)
            self.num_bundle_reached_destination += 1 
            return
        else:
            print("wasn't for me", self.node_id, ", so I'll just store it and forward it later...")
        
        # On every refresh, this bundle will be considered for forwarding if theres a suitable next hop
        has_already = self.storage.store_bundle(bundle.dest_id, bundle)
        if has_already:
            self.num_repeated_bundle_receives += 1

    """
    Refreshes the state of the DTN object.  Called by the simulation at each timestamp.
    """
    def refresh(self):
        # 1. Get the destination ids for all bundles
        all_dest_ids = self.storage.get_all_bundle_dest_ids()        
        next_hop_to_dest = dict()
        # 2. Calculate the best next hop for all these destination IDs
        # Must do this on refresh because best route is dependent on current time
        for dest_id in all_dest_ids:
            route = self.schrouter.get_best_route_dijkstra(self.node_id, dest_id, self.model.schedule.time)
            if route is None:
                continue
            next_hop_id = route.hops[0].to
            if next_hop_id not in next_hop_to_dest:
                next_hop_to_dest[next_hop_id] = []
            # print("\t(",self.node_id,") best next hop for", dest_id, "is", next_hop_id)
            next_hop_to_dest[next_hop_id].append(dest_id)

        # 3. Get rid of any expired bundles
        self.storage.refresh()  # refresh the storage so that any expired Bundles are deleted.
        
        # 4. Iterate over the currently connnected neighbors
        my_agent = self.model.agents[self.node_id]
        for neighbor_data in self.model.get_neighbors(my_agent):
            neighbor_id = neighbor_data["id"]
            neighbor_agent = self.model.agents[neighbor_id]
            # ignore exchanging data with ClientAgents or RouterAgents we're not connected to.
            if isinstance(neighbor_agent, ClientAgent) or not neighbor_data["connected"]:
                continue
        
            # If we've reached this point, the neighbor is a connected RouterAgent.
            # 5. Send the relevant bundles to this next hop
            bundles_to_send_thru_this_neighbor = []
            if neighbor_id in next_hop_to_dest:
                for dest_id in next_hop_to_dest[neighbor_id]:
                    print("neighbor", neighbor_id, "is the next hop for bundles destined to", dest_id)
                    bundles_to_send_thru_this_neighbor += self.storage.remove_all_bundles_for_dest(dest_id)
                self.__send_bundles_to_neighbor(neighbor_agent, bundles_to_send_thru_this_neighbor)
    
    """
    Given a node that we are currently connected to, sends a bunch of bundles to them
    Must make sure that you are actually "connected" to the next hop, before calling this
    Does nothing if there are no bundles to send
    """
    def __send_bundles_to_neighbor(self, neighbor_agent, bundles_to_send):
        for bundle in bundles_to_send:
            neighbor_agent.routing_protocol.handle_bundle(bundle)
            self.num_bundle_sends += 1

    """
    Called by the agent and sent to the visualization for simulation history log.
    """
    def get_state(self):
        curr_bundles = []
        for bundle in self.storage.get_all_bundles():
            curr_bundles.append(bundle.serialize())
        num_bundles = len(curr_bundles)

        return {
            "total_repeated_bundle_recv": self.num_repeated_bundle_receives,
            "total_bundle_sends": self.num_bundle_sends,
            "total_bundle_reached_dest_router": self.num_bundle_reached_destination,
            "curr_num_stored_bundles": num_bundles,
            "curr_stored_bundles": curr_bundles,
        }

    """
    Adds a contact to contact plan used by the Schrouter.
    """
    def add_contact(self,
                    source: string,
                    dest: string,
                    start_time: int,
                    end_time: int,
                    rate: string,
                    owlt=0,
                    confidence=1.):
        self.schrouter.add_contact(source, dest, start_time, end_time, rate, owlt, confidence)

    """
    Removes all contacts for the given node from the Schrouter.
    """
    def remove_all_contacts_for_node(self, node_id):
        self.schrouter.remove_all_contacts_for_node(node_id)

    """
    Removes all contacts between the given nodes from the Schrouter which intersect the given time window.
    """
    def remove_contacts_in_time_window(self, node_1_id, node_2_id, start_time, end_time):
        self.schrouter.remove_contacts_in_time_window(node_1_id, node_2_id, start_time, end_time)