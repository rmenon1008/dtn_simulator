"""
Contains the FauxHdtn class, which is a simplified implementation of HDTN.
"""
from peripherals.hdtn.storage import Storage
from peripherals.hdtn.schrouter import Schrouter


class FauxHdtn:

    def __init__(self):
        self.storage = Storage()
        self.schrouter = Schrouter()
