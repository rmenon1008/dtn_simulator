import mesa
import logging
import numpy as np
from scipy.optimize import leastsq

from agent.agent_common import try_getting
from peripherals.dtn.dtn import Dtn

# The old HDTN class. Remove when replaced with Dtn
from peripherals.dummy_hdtn import DummyHDTN

from peripherals.radio import Radio
from peripherals.movement import Movement


class RouterAgent(mesa.Agent):
    def __init__(self, model, node_options):
        super().__init__(node_options["id"], model)
        self.history = []
        self.behavior = node_options["behavior"]

        # Peripherals
        self.movement = Movement(self, model, node_options["movement"])
        self.dtn = Dtn(self.unique_id, model)  # HDTN(self, model, node_options["dtn"])
        self.radio = Radio(self, model, node_options["radio"])

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
            target = try_getting(self.behavior, "options",
                                 "target_id", default="all")
            # Check if connected to target
            if self.radio.is_connected(target):
                self.behavior["type"] = "fixed"

            # 1. Create a matrix with previous data
            positions = []
            rssis = []
            for h in self.history:
                if "neighborhood" in h["radio"]:
                    for n in h["radio"]["neighborhood"]:
                        if n["id"] == target or target == "all":
                            positions.append(h["pos"])
                            rssis.append(n["rssi"])

            positions = np.array(positions[-100:])
            rssis = np.array(rssis[-100:])

            if len(positions) < 10:
                self.movement.step_spiral()
                return

            # 2. Assume RSSI is approximately of the form
            #    best_rssi = 10 * 2.5 * log10(1/((x-a)^2 + (y-b)^2)**0.5)
            #    where (a, b) is the position of the target
            def rssi_model(x, y, a, b, c):
                return 10 * c * np.log10(1/((a-x)**2 + (b-y)**2)**0.5)

            def rssi_error(params):
                a, b, c = params
                return rssis - rssi_model(positions[:, 0], positions[:, 1], a, b, c)

            # 3. Find the best fit for a potential target
            a, b, c = leastsq(rssi_error, (0, 0, 0))[0]

            if self.model.space.out_of_bounds((a, b)):
                self.movement.step_spiral()
                return

            self.movement.move_towards((a, b))

    def get_state(self):
        return {
            "id": self.unique_id,
            "pos": self.pos,
            "behavior": self.behavior,
            "history": self.history,
            "dtn": self.dtn.get_state(),
            "radio": self.radio.get_state(),
        }
