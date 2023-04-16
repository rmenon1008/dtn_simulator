import mesa

from agent.agent_common import try_getting, rssi_find_target
from peripherals.dtn.dtn import Dtn

from peripherals.radio import Radio
from peripherals.movement import Movement
from peripherals.roaming_dtn_client_payload_handlers.router_payload_handler import RouterClientPayloadHandler


class RouterAgent(mesa.Agent):
    def __init__(self, model, node_options):
        super().__init__(node_options["id"], model)
        self.history = []
        self.behavior = node_options["behavior"]

        # Peripherals
        self.movement = Movement(self, model, node_options["movement"])
        self.dtn = Dtn(self.unique_id, model)
        self.radio = Radio(self, model, node_options["radio"])
        self.payload_handler = RouterClientPayloadHandler(self.unique_id, model, self.dtn)

    def update_history(self):
        self.history.append({
            "pos": self.pos,
            "dtn": self.dtn.get_state(),
            "radio": self.radio.get_state()
        })

    def refresh_and_log(self):
        self.radio.refresh()
        self.dtn.refresh()
        self.update_history()

    def step(self):
        self.refresh_and_log()

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
            rssi_find_target(self, RouterAgent)

    def get_state(self):
        return {
            "id": self.unique_id,
            "pos": self.pos,
            "behavior": self.behavior,
            "history": self.history,
            "dtn": self.dtn.get_state(),
            "radio": self.radio.get_state(),
        }
