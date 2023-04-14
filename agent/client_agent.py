"""
Represents a client connected to the routers of the DTN network.

Critically, these agents are supposed to represent nodes which have inconsistent behavior patterns.  For nodes with
consistent behavior patterns (ex:  orbital satellites), they should be represented by RouterAgents.

In reality, this would be something mobile like a lunar rover.
"""
from enum import Enum

import mesa

from agent.agent_common import try_getting, rssi_find_target
from peripherals.movement import Movement
from peripherals.radio import Radio
from peripherals.roaming_dtn_client_payload_handlers.cilent_payload_handler import ClientClientPayloadHandler

"""
Used to represent the current state of the client.
"""
class ClientState(Enum):
    WORKING = 0  # this represents the node doing its work + not caring about network access.
    CONNECTION_ESTABLISHMENT = 1  # this represents the client looking for a connection.
    CONNECTED = 2  # this represents the mode in which the client is connected to a router + is sending and receiving data.



# TODO:  The below code is currently copy-pasted from router_agent.  Replace it with code to do basic client operations.

class ClientAgent(mesa.Agent):
    def __init__(self, model, node_options):
        super().__init__(node_options["id"], model)
        self.state = ClientState.WORKING
        self.history = []
        self.behavior = node_options["behavior"]

        # Peripherals
        self.movement = Movement(self, model, node_options["movement"])
        self.radio = Radio(self, model, node_options["radio"])
        self.payload_handler = ClientClientPayloadHandler(self.unique_id, model)

    def update_history(self):
        self.history.append({
            "pos": self.pos,
            "radio": self.radio.get_state()
        })

    def step(self):
        self.radio.refresh()

        if self.behavior["type"] == "random":
            self.movement.step_random()
        elif self.behavior["type"] == "spiral":
            separation = try_getting(
                self.behavior, "options", "separation", default=50)
            self.movement.step_spiral(separation)
        elif self.behavior["type"] == "circle":
            radius = try_getting(self.behavior, "options",
                                 "radius", default=100)
            self.movement.step_circle(radius)
        elif self.behavior["type"] == "rssi_find_target":

            # find the nearest DTN node.
            self.state = ClientState.CONNECTION_ESTABLISHMENT
            rssi_find_target(self)

            # TODO:  figure out how to determine if we finally connected to a router + the router's ID.
            if False:
                # set state to CONNECTED.
                self.state = ClientState.CONNECTED

                # make the

    def get_state(self):
        return {
            "id": self.unique_id,
            "pos": self.pos,
            "behavior": self.behavior,
            "history": self.history,
            "dtn": self.dtn.get_state(),
            "radio": self.radio.get_state(),
        }