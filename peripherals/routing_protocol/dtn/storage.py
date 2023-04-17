"""
Contains the Storage class, which is a simplified version of HDTN Storage.
"""


class Storage:

    def __init__(self, model):
        # initialize dictionary to store bundles.
        self.model = model

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
    Returns if we already have the passed Bundle in storage.
    """
    def bundle_is_in_storage(self, bundle):

        # check if we've ever stored any bundles for the dest node.
        if bundle.dest_id not in self.stored_message_dict:
            return False

        # check if the bundle is stored
        return bundle in self.stored_message_dict[bundle.dest_id]

    """
    Retrieves a bundle for us to send from storage.
    
    If `last_bundle` is provided + it matches the front of the stored list of bundles, we remove
    it from the list of bundles.  We want to provide this parameter once we've successfully sent
    out a bundle to ensure we don't retrieve + send that same bundle again.
    
    If no bundle exists to send, we return `None`.
    """
    def get_next_bundle_for_id(self, dest_id, last_bundle=None):

        # if we have no list of bundles on-hand for the specified ID, return "None".
        if dest_id not in self.stored_message_dict or len(self.stored_message_dict[dest_id]) == 0:
            return None

        # if last_bundle was provided and last_bundle == front of the list,
        # remove the front of the list.
        if self.stored_message_dict[dest_id][0] == last_bundle:
            self.stored_message_dict[dest_id].pop(0)

        # if no bundles exist in the list, return None.
        if not self.stored_message_dict[dest_id]:
            return None

        # return the bundle at the front of the list.
        return self.stored_message_dict[dest_id][0]

    """
    Refreshes the storage to delete any expired Bundles.
    """
    def refresh(self):
        for bundle_list in self.stored_message_dict.values():
            for bundle in bundle_list:
                if bundle.expiration_timestamp <= self.model.schedule.time:
                    bundle_list.remove(bundle)
