"""
Represents a client connected to the routers of the DTN network.

Critically, these agents are supposed to represent nodes which have inconsistent behavior patterns.  Nodes with
consistent behavior patterns (ex:  orbital satellites) should be represented by RouterAgents.

In reality, this would be something mobile like a lunar rover.
"""
from enum import Enum

import mesa

from agent.agent_common import try_getting, rssi_find_target
from agent.router_agent import RouterAgent
from payload import ClientBeaconPayload
from peripherals.movement import Movement
from peripherals.radio import Radio
from peripherals.roaming_dtn_client_payload_handlers.cilent_payload_handler import ClientClientPayloadHandler

"""
Used to represent the current mode of the ClientAgent.
"""
class ClientAgentMode(Enum):
    WORKING = 0  # this represents the node doing its work + not caring about network access.
    CONNECTION_ESTABLISHMENT = 1  # this represents the client looking for a connection.
    CONNECTED = 2  # this represents the mode in which the client is connected to a router + is sending
                   # and receiving data.


class ClientAgent(mesa.Agent):
    # represents the number of steps a ClientAgent is allowed to be independent of the DTN network.
    # after RECONNECTION_INTERVAL steps, the ClientAgent must work towards reconnecting to the DTN network.
    RECONNECTION_INTERVAL = 100

    def __init__(self, model, node_options):
        super().__init__(node_options["id"], model)
        self.state = ClientAgentMode.WORKING
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
        # refresh the radio.
        self.radio.refresh()

        # emit the beacon.
        self.__emit_beacon()

        # we should update the current mode of the ClientAgent to match the ClientAgent's current state + the current
        # step timestamp.
        self.__step_mode()

        # if we're in the CONNECTION_ESTABLISHMENT mode, attempt to establish a connection with any nearby node and
        # transfer data.
        if self.mode == ClientAgentMode.CONNECTION_ESTABLISHMENT:
            self.__attempt_router_connection_and_payload_transfer()

        # refresh movement.
        self.__step_movement()

    """
    Sends a Bundle containing a ClientBeaconPayload to all RouterAgents in the detection range.
    """
    def __emit_beacon(self):
        # iterate over the neighbors (if there are any)
        for neighbor_data in self.model.get_neighbors(self):
            # obtain the agent associated with the neighbor
            neighbor_agent = self.model.agents[neighbor_data["id"]]

            # ignore sending a beacon to ClientAgents and RouterAgents we're connected to.
            if isinstance(neighbor_agent, ClientAgent) or neighbor_data["connected"]:
                continue

            # if we've reached this point, the neighbor is an unconnected RouterAgent.
            #
            # send a beacon to the RouterAgent's RouterClientPayloadHandler.
            neighbor_agent.payload_handler.update_client_mapping(ClientBeaconPayload(self.unique_id))

    """
    Attempts to connect to any RouterAgent neighbors (if any are nearby) and exchange payloads.
    
    NOTE:  This exchanges with ALL connected RouterAgents in one step.  If multiple RouterAgents are connected, data
    transfers will be initiated with each one.  This should not cause duplication issues since the payloads are deleted
    after being sent once by the client's payload_handler.  This also should allow the client to receive as much data
    as possible since some routers may have content which others do not.
    """
    def __attempt_router_connection_and_payload_transfer(self):

        # iterate over the neighbors (if there are any)
        for neighbor_data in self.model.get_neighbors(self):
            # obtain the agent associated with the neighbor
            neighbor_agent = self.model.agents[neighbor_data["id"]]

            # ignore exchanging data with ClientAgents or RouterAgents we're not connected to.
            if isinstance(neighbor_agent, ClientAgent) or not neighbor_data["connected"]:
                continue

            # if we've reached this point, the neighbor is a connected RouterAgent.

            # set state to CONNECTED.
            self.mode = ClientAgentMode.CONNECTED

            # do the ClientPayload exchange handshake with the RouterAgent's RouterClientPayloadHandler.
            router_payload_handler = neighbor_agent.payload_handler
            self.payload_handler.handshake_1(router_payload_handler)


    """
    Updates the stored mode of the ClientAgent based upon its state at the current step.
    """
    def __step_mode(self):
        # if we were connected to the router in the last step, set the state to "WORKING" and reset the "working steps"
        # counter to RECONNECTION_INTERVAL.
        if self.mode == ClientAgentMode.CONNECTED:
            self.mode = ClientAgentMode.WORKING
            self.working_steps_remaining = self.RECONNECTION_INTERVAL

        # if we're in WORKING mode, decrement the "working steps" counter.  if the counter runs out, transition into
        # CONNECTION_ESTABLISHMENT mode.
        elif self.mode == ClientAgentMode.WORKING:
            self.working_steps_remaining -= 1
            if self.working_steps_remaining == 0:
                self.mode = ClientAgentMode.CONNECTION_ESTABLISHMENT

    def __step_movement(self):
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
            # move towards the nearest RouterAgent.
            rssi_find_target(self, RouterAgent)

    def get_state(self):
        return {
            "id": self.unique_id,
            "pos": self.pos,
            "behavior": self.behavior,
            "history": self.history,
            "radio": self.radio.get_state(),
            "num_client_payloads_sent":  self.payload_handler.num_payloads_sent,
            "num_client_payloads_received":  self.payload_handler.num_payloads_received
        }