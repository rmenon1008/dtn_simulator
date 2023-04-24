from random import randint

from payload import Payload
from peripherals.routing_protocol.routing_protocol_common import Bundle
from peripherals.routing_protocol.dtn.storage import Storage

import mesa
from mockito import mock

BUNDLE_LIFESPAN = 2500

def test_bundle_lifecycle():
    # setup a dummy model object used by the DTN objects.
    schedule = mesa.time.RandomActivation(mesa.Model())
    dummy_model = mock({"schedule": schedule})

    # create a Storage object.
    storage = Storage(dummy_model)

    # store a bundle in the Storage.
    dest_id = randint
    bundle_1 = Bundle(randint, dest_id, Payload(), 0, BUNDLE_LIFESPAN)
    storage.store_bundle(dest_id, bundle_1)

    # successfully get the bundle from Storage + assert it looks as expected.
    retrieved_bundle_1 = storage.get_next_bundle_for_id(dest_id)
    assert bundle_1 == retrieved_bundle_1

    # store a second bundle in the Storage.
    bundle_2 = Bundle(randint, dest_id, Payload(), 0, BUNDLE_LIFESPAN)
    storage.store_bundle(dest_id, bundle_2)

    # successfully get the second bundle from Storage + assert it looks as expected.
    # (we provide the `last_bundle` param when doing this to remove the first bundle.
    # this makes us get the second bundle.)
    retrieved_bundle_2 = storage.get_next_bundle_for_id(dest_id, retrieved_bundle_1)
    assert bundle_2 == retrieved_bundle_2


def test_bundle_expiration():
    # setup a dummy model object used by the DTN objects.
    schedule = mesa.time.RandomActivation(mesa.Model())
    dummy_model = mock({"schedule": schedule})

    # create a Storage object.
    storage = Storage(dummy_model)

    # store an expired bundle in the Storage.
    dest_id = randint
    expired_bundle = Bundle(randint, dest_id, Payload(), schedule.time - BUNDLE_LIFESPAN - 1, BUNDLE_LIFESPAN)
    storage.store_bundle(dest_id, expired_bundle)

    # verify that the expired_bundle is in Storage.
    retrieved_bundle = storage.get_next_bundle_for_id(dest_id)
    assert retrieved_bundle == expired_bundle

    # refresh the storage, deleting the Bundle.
    storage.refresh()

    # verify that the expired_bundle is no longer in Storage.
    retrieved_bundle = storage.get_next_bundle_for_id(dest_id)
    assert retrieved_bundle is None
