"""
Contains the Schrouter class, which handles all contact plan-related content that HDTN puts in Router and Scheduler.
"""
import string
import sys

from peripherals.hdtn.external_dependencies.cp_file_tools import read_contact_plan_from_json
from peripherals.hdtn.external_dependencies.py_cgr_lib import Contact, cgr_dijkstra, Route


class Schrouter:

    """
    Declare contact_plan_json_filename when loading a precreated contact plan from a JSON.
    """
    def __init__(self, contact_plan_json_filename: string = None):
        self.contact_plan = []
        self.next_contact_id = 0  # stores the next "connection ID" we should assign.  these IDs are used to
                                     # internally identify connections.

        # if the contact_plan_json_filename is defined, load the file.
        if contact_plan_json_filename is not None:
            # read in the contact plan JSON data from the JSON file.
            contact_jsons = read_contact_plan_from_json(contact_plan_json_filename)

            # convert the contact plan JSON data into Contact objects
            for contact in contact_jsons:
                self.add_link(
                        source=contact["source"],
                        dest=contact["dest"],
                        start_time=contact["startTime"],
                        end_time=contact["endTime"],
                        rate=contact["rate"],
                        owlt=contact["owlt"],
                        confidence=contact["confidence"])

    """
    Returns if any path to the specified node exists in the contact plan. 
    """
    def check_any_availability(self, node_id) -> bool:
        return len(list(filter(
            lambda contact: contact.to == node_id,
            self.contact_plan))) > 0

    """
    Returns if any path between the two specified nodes exists in the contact plan. 
    """
    def check_link_availability(self, source_id, dest_id) -> bool:
        return len(list(filter(
            lambda contact: contact.frm == source_id and contact.to == dest_id,
            self.contact_plan))) > 0

    """
    Adds a link to the contact plan.
    """
    def add_link(self,
                 source: string,
                 dest: string,
                 start_time: int,
                 end_time: int,
                 rate: string,
                 owlt=0,
                 confidence=1.):
        # get the next contact ID.
        contact_id = self.next_contact_id
        self.next_contact_id += 1

        # create the new contact.
        new_contact = Contact(
                    start=start_time,
                    end=end_time,
                    frm=source,
                    to=dest,
                    rate=rate,
                    id=contact_id,
                    owlt=owlt,
                    confidence=confidence,
                )
        self.contact_plan.append(new_contact)

    """
    Removes all links associated with the passed contact_id from the contact plan.
    """
    def remove_all_links_for_node(self, node_id):
        self.contact_plan = [contact for contact in self.contact_plan if contact.to != node_id and contact.frm != node_id]


    """
    Removes all links associated with the passed contact_id from the contact plan.
    """
    def remove_link_by_contact_id(self, contact_id):
        self.contact_plan = [contact for contact in self.contact_plan if contact.id != contact_id]

    """
    Returns the best route for the specified contact_id in the stored contact plan as calculated via Dijkstra's.
    """
    def get_best_route_dijkstra(self, root_node_id, destination_node_id, curr_timestamp) -> Route:
        # create root_contact object to use for dijkstra's.
        root_contact = Contact(start=curr_timestamp,
                    end=sys.maxsize,
                    frm=root_node_id,
                    to=root_node_id,
                    rate=100,
                    id=-1)
        root_contact.arrival_time = 0

        # run dijkstra's, return the best route.
        return cgr_dijkstra(root_contact, destination_node_id, self.contact_plan)

    """
    Returns the best route for the specified contact_id in the stored contact plan as calculated via OCGR.
    """
    def get_best_route_ocgr(self, root_contact_id, destination_contact_id):
        # TODO Implement OCGR here later!
        return