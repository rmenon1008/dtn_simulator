"""
Contains the Storage class, for holding bundles to be transmitted.
"""


class Storage:

    def __init__(self, model):
        # initialize dictionary to store bundles.
        self.model = model

        self.seen_bundle_ids = set() # for deduping

        # key = destination
        # value = list containing bundles which need to be sent to that destination.
        # implementation invariant: there are no empty lists. if there are no bundles, there should be no key
        self.stored_message_dict = dict()

    def seen_before(self, bundle):
        return bundle.bundle_id in self.seen_bundle_ids

    """
    Adds a bundle to the storage.
    If this bundle was seen before, return true and don't do anything.
    """
    def store_bundle(self, dest_id, bundle):
        if self.seen_before(bundle):
            return True
        else:
            self.seen_bundle_ids.add(bundle.bundle_id)
            if dest_id not in self.stored_message_dict:
                self.stored_message_dict[dest_id] = []
            self.stored_message_dict[dest_id].append(bundle)
            return False

    """
    Returns list of all destination IDs for the bundles in storage
    Returns an empty list if there are no bundles
    """
    def get_all_bundle_dest_ids(self):
        return list(self.stored_message_dict.keys())

    """
    Returns a list of all bundles in storage.

    Returns an empty list if there are no bundles
    """
    def get_all_bundles(self):
        all_bundles = []
        for bundle_list in self.stored_message_dict.values():
            all_bundles += bundle_list
        return all_bundles
    
    """
    Returns list of bundles destined to the given dest_id

    Returns None if no bundles are available
    """
    def get_all_bundles_for_dest(self, dest_id):
        if dest_id not in self.stored_message_dict:
            return None
        return self.stored_message_dict[dest_id]
    
    """
    Returns list of bundles that we should send to the given next hop,
    and removes them from storage.

    Returns None if no bundles are available
    """
    def remove_all_bundles_for_dest(self, dest_id):
        if dest_id not in self.stored_message_dict:
            return None

        return self.stored_message_dict.pop(dest_id)

    """
    Retrieves a bundle for us to send from storage.
    
    If `last_bundle` is provided + it matches the front of the stored list of bundles, we remove
    it from the list of bundles.  We want to provide this parameter once we've successfully sent
    out a bundle to ensure we don't retrieve + send that same bundle again.
    
    If no bundle exists to send, we return `None`.
    """
    def get_next_bundle_for_id(self, dest_id, last_bundle=None):

        # if we have no list of bundles on-hand for the specified ID, return "None".
        if dest_id not in self.stored_message_dict:
            return None

        # if last_bundle was provided and last_bundle == front of the list,
        # remove the front of the list.
        if self.stored_message_dict[dest_id][0] == last_bundle:
            self.stored_message_dict[dest_id].pop(0)

        # if no bundles exist in the list, return None.
        if not self.stored_message_dict[dest_id]:
            # Get rid of this key because it's empty
            self.stored_message_dict.pop(dest_id)
            return None

        # return the bundle at the front of the list.
        return self.stored_message_dict[dest_id][0]

    """
    Refreshes the storage to delete any expired Bundles.
    """
    def refresh(self):
        dest_ids_to_remove = []
        for dest_id in self.stored_message_dict:
            bundle_list = self.stored_message_dict[dest_id]
            for bundle in bundle_list:
                if bundle.expiration_timestamp <= self.model.schedule.time:
                    bundle_list.remove(bundle)
            if len(bundle_list) == 0:
                dest_ids_to_remove.append(dest_id)
        
        for id in dest_ids_to_remove:
            self.stored_message_dict.pop(id)