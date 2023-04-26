"""
Contains the Schrouter class, which handles all contact plan-related content for CGR.
"""
import string
import sys

from peripherals.routing_protocol.external_dependencies.cp_file_tools import read_contact_plan_from_json
from peripherals.routing_protocol.external_dependencies.py_cgr_lib import Contact, cgr_dijkstra, Route


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
                self.add_contact(
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
    Returns if a contact between the two specified nodes exists in the contact plan. 
    """
    def check_contact_availability(self, source_id, dest_id) -> bool:
        return len(list(filter(
            lambda contact: contact.frm == source_id and contact.to == dest_id,
            self.contact_plan))) > 0

    """
    Returns if a contact between the two specified nodes at the _exact_ specified time window exists 
    in the contact plan. 
    """
    def check_contact_availability_specific_time_window(self, source_id, dest_id, start_time, end_time) -> bool:
        return len(list(filter(
            lambda contact: contact.frm == source_id and contact.to == dest_id and contact.start == start_time and contact.end == end_time,
            self.contact_plan))) > 0

    """
    Adds a contact to the contact plan.
    """
    def add_contact(self,
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
    Removes all contacts associated with the passed contact_id from the contact plan.
    """
    def remove_all_contacts_for_node(self, node_id):
        self.contact_plan = [contact for contact in self.contact_plan if contact.to != node_id and contact.frm != node_id]


    """
    Removes all contacts associated with the passed contact_id from the contact plan.
    """
    def remove_contact_by_contact_id(self, contact_id):
        self.contact_plan = [contact for contact in self.contact_plan if contact.id != contact_id]

    """
    Removes all contacts associated with the passed node ids within the specified window from the contact plan.
    """
    def remove_contacts_in_time_window(self, node_1_id, node_2_id, start_time, end_time):
        # 0-5 exists.  We say "remove 4-8".  The 0-5 window is modified to be 0-3.
        new_contact_plan = []
        for contact in self.contact_plan:
            if (contact.frm == node_1_id and contact.to == node_2_id) \
                    or (contact.frm == node_2_id and contact.to == node_1_id):
                # if we have found a contact for the contact_id, compute one which does not overlap with the window (if possible)

                # check to see if the contact lies entirely within the time window.
                if contact.start >= start_time and contact.end <= end_time:
                    # skip to the next contact if so.  (this effectively throws out this contact)
                    continue
                elif contact.start < start_time and end_time < contact.end:
                    # if the removal window is entirely within the contact, create + store two new contacts:
                    # - one which is from contact.start -> start_time - 1
                    # - one which is from end_time + 1 -> contact.end
                    contact1 = Contact(
                        contact.frm,
                        contact.to,
                        contact.start,
                        start_time - 1,
                        contact.rate,
                        contact.id,
                        contact.confidence,
                        contact.owlt
                    )
                    contact2 = Contact(
                        contact.frm,
                        contact.to,
                        end_time + 1,
                        contact.end,
                        contact.rate,
                        contact.id,
                        contact.confidence,
                        contact.owlt
                    )
                    new_contact_plan.append(contact1)
                    new_contact_plan.append(contact2)

                elif contact.start < start_time <= end_time <= end_time:
                    # if the end falls within the window, store an identical contact where the end is start_time - 1.
                    contact = Contact(
                        contact.frm,
                        contact.to,
                        contact.start,
                        start_time - 1,
                        contact.rate,
                        contact.id,
                        contact.confidence,
                        contact.owlt
                    )
                    new_contact_plan.append(contact)

                elif start_time <= contact.start <= contact.end < end_time:
                    # if the end falls within the window, store an identical contact where the start is end_time + 1.
                    contact = Contact(
                        contact.frm,
                        contact.to,
                        end_time + 1,
                        contact.end,
                        contact.rate,
                        contact.id,
                        contact.confidence,
                        contact.owlt
                    )
                    new_contact_plan.append(contact)

            else:
                # otherwise, just add the contact to the new contact plan.
                new_contact_plan.append(contact)


        # update the stored contact plan to be the newly-computed new_contact_plan
        self.contact_plan = new_contact_plan

    """
    Returns the best route for the specified contact_id in the stored contact plan as calculated via Dijkstra's.
    
    curr_timestamp = the timestamp at which we're computing the route.
    """
    def get_best_route_dijkstra(self, root_node_id, destination_node_id, curr_timestamp) -> Route:
        # create root_contact object to use for dijkstra's.
        root_contact = Contact(start=0,
                    end=sys.maxsize,
                    frm=root_node_id,
                    to=root_node_id,
                    rate=100,
                    id=-1)
        root_contact.arrival_time = curr_timestamp

        # run dijkstra's, return the best route.  if any errors are generated, just return `None`
        try:
            return cgr_dijkstra(root_contact, destination_node_id, self.contact_plan)
        except:
            return None

    """
    Returns the best route for the specified contact_id in the stored contact plan as calculated via OCGR.
    """
    def get_best_route_ocgr(self, root_contact_id, destination_contact_id):
        # TODO Implement OCGR here later!
        return