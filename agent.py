import mesa
import logging
import numpy as np
from scipy.optimize import leastsq
from agent_peripherals import *

class RoverAgent(mesa.Agent):
    def __init__(self, model, node_options):
        super().__init__(node_options["id"], model)
        self.history = []
        self.behavior = node_options["behavior"]

        # Peripherals
        self.movement = Movement(self, model, node_options["movement"])
        self.hdtn = HDTN(self, model, node_options["hdtn"])
        self.radio = Radio(self, model, node_options["radio"])

    def update_history(self):
        self.history.append({
            "pos": self.pos,
            "hdtn": self.hdtn.get_state(),
            "radio": self.radio.get_state()
        })

    def refresh_and_log(self):
        self.radio.refresh()
        self.hdtn.refresh()
        self.update_history()

    def step(self):
        self.refresh_and_log()

        if self.behavior["type"] == "random":
            self.movement.step_random()
        elif self.behavior["type"] == "spiral":
            self.movement.step_spiral()
        elif self.behavior["type"] == "circle":
            self.movement.step_circle()
        elif self.behavior["type"] == "rssi_find_target":
            target = "all"
            if hasattr(self.behavior, "options"):
                if hasattr(self.behavior["options"], "target"):
                    target = self.behavior["options"]["target"]

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
            "hdtn": self.hdtn.get_state(),
            "radio": self.radio.get_state(),
        }
    
    # def main_logic(self):
    #     # def move_spiral():
    #     #     # Move in a spiral
    #     #     if (self.move_spiral):
    #     #         def p2c(r, phi):
    #     #             return (r * math.cos(phi), r * math.sin(phi))

    #     #         a, b = p2c(self.spiral_r, self.spiral_phi)
    #     #         self.move(a, b)
    #     #         self.spiral_phi += SPIRAL_ARC / self.spiral_r
    #     #         self.spiral_r = SPIRAL_CONST_B * self.spiral_phi
    #     #     else:
    #     #         self.move(self.random.random() * 2 * MAX_SPEED - MAX_SPEED, self.random.random() * 2 * MAX_SPEED - MAX_SPEED)


    #     def find_best_location():
    #         # 1. Create a matrix with rows of of positions
    #         positions = []
    #         rssis = []
    #         for h in self.history:
    #             if "neighborhood" in h["radio"]:
    #                 if self.hdtn.current_target == "all":
    #                     rssis.append(h["radio"]["best_rssi"])
    #                     positions.append(h["pos"])
    #                 else:
    #                     for n in h["radio"]["neighborhood"]:
    #                         if n["id"] == self.hdtn.current_target:
    #                             if n["rssi"] < -900:
    #                                 continue
    #                             rssis.append(n["rssi"])
    #                             positions.append(h["pos"])
    #                             break

    #         positions = np.array(positions)
    #         rssis = np.array(rssis)

    #         # Cap the number of positions to 100
    #         positions = positions[-100:]
    #         rssis = rssis[-100:]

    #         if (positions.shape[0] < 8):
    #             move_spiral()
    #             return
            
    #         # 2. Assume RSSI is approximately of the form
    #         #    best_rssi = 10 * 2.5 * log10(1/((x-a)^2 + (y-b)^2)**0.5)
    #         #    where (a, b) is the position of the target
    #         def rssi_model(x, y, a, b, c):
    #             return 10 * c * np.log10(1/((a-x)**2 + (b-y)**2)**0.5)
            
    #         # 3. Use a least squares regression to find the best values for a and b
    #         def rssi_error(params):
    #             a, b, c = params
    #             return rssis - rssi_model(positions[:, 0], positions[:, 1], a, b, c)
            
    #         a, b, c = leastsq(rssi_error, (0, 0, 0))[0]

    #         if self.model.space.out_of_bounds((a, b)):
    #             move_spiral()
    #             return

    #         # 4. Move towards (a, b)
    #         dx = a - self.pos[0]
    #         dy = b - self.pos[1]
    #         self.move(dx, dy)
            
    #     if self.behavior == "fixed":
    #         # Fixed agents don't move
    #         return
    #     elif self.behavior == "mobile":
    #         # if self.hdtn.has_data:
    #             # find_best_location()
    #         self.move(5,5)
    #         return