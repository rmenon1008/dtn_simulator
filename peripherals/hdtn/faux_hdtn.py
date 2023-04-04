"""
Contains the FauxHdtn class, which is a simplified implementation of HDTN.
"""
from peripherals.hdtn.faux_storage import FauxStorage
from peripherals.hdtn.schrouter import Schrouter


class FauxHdtn:

    def __init__(self):
        self.storage = FauxStorage()
        self.schrouter = Schrouter()
