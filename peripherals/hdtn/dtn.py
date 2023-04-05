"""
Contains the Dtn class, which is a simplified implementation of HDTN.
"""
import string

from peripherals.hdtn.hdtn_bundle import Bundle
from peripherals.hdtn.storage import Storage
from peripherals.hdtn.schrouter import Schrouter


class Dtn:

    def __init__(self, node_id, dtn_dict: dict):
        self.node_id = node_id

        # dtn_dict = reference to a Dict which contains mappings of DTN node IDs -> DTN nodes.
        #           since this is a sim, we can allow all nodes to be able to easily contact
        #           each other using this.  This is the easiest way to "interconnect" the nodes.
        #
        #           We can then "manage" the availability of the connections + compute them in
        #           the Schrouter.
        self.dtn_dict = dtn_dict

        self.storage = Storage()
        self.schrouter = Schrouter()
        self.timestamp = 0

    """
    Receives + handles bundles of data.
    
    This effectively behaves akin to the `ingress` + `egress` modules in HDTN.
    """
    def receive_bundle(self, bundle: Bundle):
        # Ingress
        # Process received bundle.

        # if this is the intended destination for the bundle, "receive" it and exit.
        if bundle.dest_id == self.node_id:
            return

        # if there exists a link by which we can route the Bundle to its destination, pass it on to the next link.
        if self.schrouter.check_any_availability(bundle.dest_id):
            # compute the route.
            route = self.schrouter.get_best_route_dijkstra(self.node_id, bundle.dest_id, self.timestamp)

            # get the ID of the next node on the route.
            next_hop_dest_id = route.hops[0].to

            # send the bundle onto the next node on the route.
            self.__send_bundle(bundle, next_hop_dest_id)

        # if no such link exists, store the bundle in storage.
        else:
            self.storage.store_bundle(bundle.dest_id, bundle)

    """
    Increments the timestamp.
     
    This value is directly used by the dtn to calculate routes, so incrementing it does affect route computation.
    """
    def refresh(self):
        self.timestamp += 1

    """
    Adds a link to contact plan used by the Schrouter.
    """
    def add_link(self,
                 source: string,
                 dest: string,
                 start_time: int,
                 end_time: int,
                 rate: string,
                 owlt=0,
                 confidence=1.):
        self.schrouter.add_link(source, dest, start_time, end_time, rate, owlt, confidence)

        # check to see if the contact plan containing this new link now has a route between this node + dest.
        if self.schrouter.get_best_route_dijkstra(self.node_id, dest, self.timestamp) is not None:
            # if there is a valid route between this node + dest, flush all bundles stored for dest from storage.
            # NOTE:  if this method is called while no bundles are currently stored, nothing will happen.
            self.__flush_bundles(dest)

    """
    Removes all links for the given node from the Schrouter.
    """
    def remove_link(self, node_id):
        self.schrouter.remove_all_links_for_node(node_id)

    """
    Private function used to flush-out stored Bundles for the specified destination node in the network.
    
    NOTE:  This method ignores the connection status with the destination node in the Schrouter, so it should only be 
           used when we've verified that the connection is valid in the Schrouter beforehand.
    """
    def __flush_bundles(self, dest_id):
        # get the route to the dest_id from the Schrouter.
        # compute the route.
        route = self.schrouter.get_best_route_dijkstra(self.node_id, dest_id, self.timestamp)

        # get the ID of the next node on the route.
        next_hop_dest_id = route.hops[0].to

        # iteratively go thru the stored bundles for the dest_id and send them out.
        bundle_to_send = self.storage.get_next_bundle_for_id(dest_id)
        while bundle_to_send is not None:
            # send the bundle onto the next node on the route.
            self.__send_bundle(bundle_to_send, next_hop_dest_id)

            # get the next bundle to send.
            bundle_to_send = self.storage.get_next_bundle_for_id(dest_id, bundle_to_send)

    """
    Private function used to send the passed Bundle to the specified node in the network.
    """
    def __send_bundle(self, bundle: Bundle, dest_id):
        dest_dtn_node = self.dtn_dict[dest_id]
        dest_dtn_node.receive_bundle(bundle)
