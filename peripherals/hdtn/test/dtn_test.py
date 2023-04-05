
def setup():
    # setup the 5 nodes (0, 1, 2, 3, 4).

    # timestamps...
    # 0 -> 1:  @3-5
    # 0 -> 2:  @0->inf
    # 2 -> 1:  @0->inf
    # 0 -> 3:  @0->inf


# test cases we'll want:
# - send @0 from 0->1.  sends 0->2->1
# - send @3 from 0->1.  sends 0->1
# - send @0 from 0->3.  fails to send, bundle is stored.  then connect 3 & 4.  autosends from 0->3->4 upon connection.

# find a way to verify that receive_bundle is being called.  use this verification in tests.