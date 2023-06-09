import mesa

from agent.agent_common import try_getting

from peripherals.radio import Radio
from peripherals.movement import Movement
from peripherals.routing_protocol.alt_algos.spray_and_wait import SprayAndWait
from peripherals.spray_and_wait_payload_handler import SprayAndWaitPayloadHandler

"""
An EpidemicAgent for a simulator where all nodes are epidemic agents 
(i.e. there is no differentiation between clients and routers)
"""

class SprayAndWaitAgent(mesa.Agent):
    # Maximum length of the history to keep. Prevents the simulation from slowing down.
    MAX_HISTORY_LENGTH = 150

    def __init__(self, model, node_options):
        super().__init__(node_options["id"], model)
        self.name = try_getting(node_options, "name", default=None)
        self.history = []
        self.special_behavior = try_getting(node_options, "special_behavior", default=None)

        # Peripherals
        self.movement = Movement(self, model, node_options["movement"])
        self.radio = Radio(self, model, node_options["radio"])
        self.routing_protocol = SprayAndWait(self.unique_id, self.model, self)
        self.payload_handler = SprayAndWaitPayloadHandler(self.unique_id, model, self.routing_protocol)

    def update_history(self):
        self.history.append({
            "pos": self.pos,
            "routing_protocol": self.routing_protocol.get_state(),
            "radio": self.radio.get_state()
        })
        self.history = self.history[-self.MAX_HISTORY_LENGTH:]

    def step(self):
        # update our peripherals.
        self.radio.refresh()
        self.routing_protocol.refresh()
        self.payload_handler.refresh()
        self.update_history()
        self.__step_movement()

    def __step_movement(self):
        self.movement.step()

    def get_state(self):
        state = {
            "id": self.unique_id,
            "pos": self.pos,
            "history": self.history,
            "routing_protocol": self.routing_protocol.get_state(),
            "curr_num_outgoing_payloads_to_send": 0, # spray-and-wait only stores bundles, not payloads. must be 0 for metrics
            "curr_outgoing_payloads_to_send": [],
            "curr_num_payloads_received_for_client": 0, # spray-and-wait only stores bundles, not payloads. must be 0 for metrics
            "curr_payloads_received_for_client": [],
            "total_pay_recv":  self.payload_handler.num_payloads_received,
            "pay_recv_latencies":  self.payload_handler.received_payload_latencies,
            "received_payloads": self.payload_handler.received_payloads,
            "total_drops_picked_up_from_ground":  self.payload_handler.num_drops_picked_up,
            "radio": self.radio.get_state(),
            "type": "router"
        }
        if self.name:
            state["name"] = self.name
        return state