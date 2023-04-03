"""
Contains the FauxStorage class, which is a simplified version of HDTN Storage.
"""


class FauxStorage:

    def __init__(self):
        # initialize dictionary to store bundles.

        # key = destination
        # value = list containing bundles which need to be sent to that destination.
        self.stored_message_dict = {}

    """
    Adds a bundle to the storage.
    """
    def store_bundle(self, dest_id, bundle):

        # if we've never stored a bundle for this dest_id, add an empty list to the dict.
        if dest_id not in self.stored_message_dict:
            self.stored_message_dict[dest_id] = []

        # store the bundle in the dict.
        self.stored_message_dict[dest_id].append(bundle)

    """
    Retrieves a bundle for us to send from storage.
    
    If `last_bundle` is provided + it matches the front of the stored list of bundles, we remove
    it from the list of bundles.  We want to provide this parameter once we've successfully sent
    out a bundle to ensure we don't retrieve + send that same bundle again.
    
    If no bundle exists to send, we return `None`.
    """
    def get_next_bundle_for_id(self, dest_id, last_bundle=None):

        # if we have no bundle on-hand for the specified ID, return "None".
        # (this is if there is no list on-hand for the specified key _or_ the stored list is empty)
        if dest_id not in self.stored_message_dict or not self.stored_message_dict[dest_id]:
            return None

        # if last_bundle was provided and last_bundle == front of the list,
        # remove the front of the list.
        if self.stored_message_dict[dest_id][0] == last_bundle:
            self.stored_message_dict[dest_id].pop(0)

        # return the bundle at the front of the list.
        return self.stored_message_dict[dest_id][0]