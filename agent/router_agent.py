from enum import Enum

import mesa

from agent.agent_common import try_getting, rssi_find_router_target
from agent.client_agent import ClientAgent
from payload import ClientMappingDictPayload
from peripherals.routing_protocol.alt_algos.epidemic import Epidemic
from peripherals.routing_protocol.alt_algos.spray_and_wait import SprayAndWait
from peripherals.routing_protocol.dtn.dtn import Dtn

from peripherals.radio import Radio
from peripherals.movement import Movement
from peripherals.roaming_client_payload_handlers.router_payload_handler import RouterClientPayloadHandler

"""
Used to communicate which routing protocol we want this RouterAgent to use.

All RouterAgent on the network _must_ use the same protocol, or nothing will work.
"""
class RoutingProtocol(Enum):
    DTN = 0
    EPIDEMIC = 1
    SPRAY_AND_WAIT = 2

class RouterAgent(mesa.Agent):

    # Maximum length of the history to keep. Prevents the simulation from slowing down.
    MAX_HISTORY_LENGTH = 150

    def __init__(self, model, node_options, protocol_type):
        super().__init__(node_options["id"], model)
        self.routing_protocol_type = RoutingProtocol(protocol_type) # protocol_type is an int corresponding to enum
        print("routing protocol type is", self.routing_protocol_type)
        self.name = try_getting(node_options, "name", default=None)
        self.history = []
        self.special_behavior = try_getting(node_options, "special_behavior", default=None)
        self.contact_plan_filepath = try_getting(node_options, "cp_file", default=None)

        # Peripherals
        self.movement = Movement(self, model, node_options["movement"])
        self.routing_protocol = self.__get_routing_protocol_object()
        self.radio = Radio(self, model, node_options["radio"])
        self.payload_handler = RouterClientPayloadHandler(self.unique_id, model, self.routing_protocol)

    def update_history(self):
        self.history.append({
            "pos": self.pos,
            "routing_protocol": self.routing_protocol.get_state(),
            "radio": self.radio.get_state(),
            "payloads_awaiting_dtn_transmission": len(self.payload_handler.outgoing_payloads_to_send),
            "curr_payloads_received_for_client": self.__get_curr_num_payloads_received_for_client(),
            "router_client_mappings": self.payload_handler.client_router_mapping_dict
        })
        self.history = self.history[-self.MAX_HISTORY_LENGTH:]

    def step(self):
        # update our peripherals.
        self.radio.refresh()
        self.routing_protocol.refresh()
        self.payload_handler.refresh()
        self.update_history()

        self.__attempt_router_connection_and_exchange_client_mappings()

        self.__step_movement()

    """
    Connects to any RouterAgent neighbors (if any are nearby in connection range) and exchanges Client->Router mappings.
    """
    def __attempt_router_connection_and_exchange_client_mappings(self):
        # iterate over the neighbors (if there are any)
        for neighbor_data in self.model.get_neighbors(self):
            # obtain the agent associated with the neighbor
            neighbor_agent = self.model.agents[neighbor_data["id"]]

            # ignore exchanging data with ClientAgents or RouterAgents we're not connected to.
            if isinstance(neighbor_agent, ClientAgent) or not neighbor_data["connected"]:
                continue

            # if we've reached this point, the neighbor is a connected RouterAgent.
            #
            # send out client mapping data to the other RouterAgent.
            # (the other RouterAgent should send their client mapping data to us as well.)
            neighbor_agent.payload_handler\
                .handle_mapping_dict(ClientMappingDictPayload(self.payload_handler.client_router_mapping_dict))

    def __step_movement(self):
        if self.special_behavior is not None:
            if self.special_behavior["type"] == "find_node_rssi":
                rssi_find_router_target(self)
            # TODO:  Add other cases for `special_behavior` here.
        else:
            self.movement.step()

    def __get_routing_protocol_object(self):
        if self.routing_protocol_type == RoutingProtocol.DTN:
            return Dtn(self.unique_id, self.model, self.contact_plan_filepath)
        elif self.routing_protocol_type == RoutingProtocol.EPIDEMIC:
            return Epidemic(self.unique_id, self.model, self)
        elif self.routing_protocol_type == RoutingProtocol.SPRAY_AND_WAIT:
            return SprayAndWait(self.unique_id, self.model, self)

    def get_state(self):
        state = {
            "id": self.unique_id,
            "pos": self.pos,
            "history": self.history,
            "routing_protocol": self.routing_protocol.get_state(),
            "outgoing_payloads_to_send": len(self.payload_handler.outgoing_payloads_to_send),
            "curr_payloads_received_for_client": self.__get_curr_num_payloads_received_for_client(),
            "radio": self.radio.get_state(),
            "type": "router"
        }
        if self.name:
            state["name"] = self.name
        return state
    
    def __get_curr_num_payloads_received_for_client(self):
        curr_payloads_received_for_client = 0
        for client_id in self.payload_handler.payloads_received_for_client:
            curr_payloads_received_for_client += len(self.payload_handler.payloads_received_for_client[client_id])
        return curr_payloads_received_for_client