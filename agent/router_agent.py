import mesa

from agent.agent_common import try_getting, rssi_find_router_target
from agent.client_agent import ClientAgent
from payload import ClientMappingDictPayload
from peripherals.routing_protocol.dtn.dtn import Dtn

from peripherals.radio import Radio
from peripherals.movement import Movement
from peripherals.roaming_client_payload_handlers.router_payload_handler import RouterClientPayloadHandler


class RouterAgent(mesa.Agent):
    def __init__(self, model, node_options):
        super().__init__(node_options["id"], model)
        self.history = []
        self.behavior = node_options["behavior"]

        # Peripherals
        self.movement = Movement(self, model, node_options["movement"])
        self.routing_protocol = Dtn(self.unique_id, model)
        self.radio = Radio(self, model, node_options["radio"])
        self.payload_handler = RouterClientPayloadHandler(self.unique_id, model, self.routing_protocol)

    def update_history(self):
        self.history.append({
            "pos": self.pos,
            "routing_protocol": self.routing_protocol.get_state(),
            "radio": self.radio.get_state(),
            "payloads_awaiting_dtn_transmission": len(self.payload_handler.outgoing_payloads_to_send),
            "payloads_received_for_client": len(self.payload_handler.payloads_received_for_client.values()),
            "router_client_mappings": self.payload_handler.client_router_mapping_dict
        })

    def step(self):
        # update our peripherals.
        self.radio.refresh()
        self.routing_protocol.refresh()
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
            rssi_find_router_target(self)

    def get_state(self):
        return {
            "id": self.unique_id,
            "pos": self.pos,
            "behavior": self.behavior,
            "history": self.history,
            "routing_protocol": self.routing_protocol.get_state(),
            "radio": self.radio.get_state(),
        }
