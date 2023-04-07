from random import randint

from peripherals.hdtn.hdtn_bundle import Bundle
from peripherals.hdtn.storage import Storage


def test_bundle_lifecycle():
    # create a Storage object.
    storage = Storage()

    # store a bundle in the Storage.
    dest_id = randint
    bundle_1 = Bundle(randint, dest_id)
    storage.store_bundle(dest_id, bundle_1)

    # successfully get the bundle from Storage + assert it looks as expected.
    retrieved_bundle_1 = storage.get_next_bundle_for_id(dest_id)
    assert bundle_1 == retrieved_bundle_1

    # store a second bundle in the Storage.
    bundle_2 = Bundle(randint, dest_id)
    storage.store_bundle(dest_id, bundle_2)

    # successfully get the second bundle from Storage + assert it looks as expected.
    # (we provide the `last_bundle` param when doing this to remove the first bundle.
    # this makes us get the second bundle.)
    retrieved_bundle_2 = storage.get_next_bundle_for_id(dest_id, retrieved_bundle_1)
    assert bundle_2 == retrieved_bundle_2
