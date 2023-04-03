from random import randint

from peripherals.hdtn.faux_hdtn_bundle import Bundle
from peripherals.hdtn.faux_storage import FauxStorage


def test_bundle_lifecycle():
    # create a FauxStorage object.
    faux_storage = FauxStorage()

    # store a bundle in the FauxStorage.
    dest_id = randint
    bundle_1 = Bundle(randint)
    faux_storage.store_bundle(dest_id, bundle_1)

    # successfully get the bundle from FauxStorage + assert it looks as expected.
    retrieved_bundle_1 = faux_storage.get_next_bundle_for_id(dest_id)
    assert bundle_1 == retrieved_bundle_1

    # store a second bundle in the FauxStorage.
    bundle_2 = Bundle(randint)
    faux_storage.store_bundle(dest_id, bundle_2)

    # successfully get the second bundle from FauxStorage + assert it looks as expected.
    # (we provide the `last_bundle` param when doing this to remove the first bundle.
    # this makes us get the second bundle.)
    retrieved_bundle_2 = faux_storage.get_next_bundle_for_id(dest_id, retrieved_bundle_1)
    assert bundle_2 == retrieved_bundle_2
