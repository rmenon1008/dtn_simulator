import mesa
import logging
import numpy as np
from scipy.optimize import leastsq
from agent_peripherals import *

MAX_SPEED = 5

class RoverAgent(mesa.Agent):
    def __init__(self, unique_id, model, type="mobile", radio_noise=0.1, radio_detection_range=200, radio_connection_range=40):
        super().__init__(unique_id, model)
        self.type = type
        self.history = []
        self.target_location = None

        # Peripherals
        self.hdtn = HDTN(self, model)
        self.radio = Radio(self, model, radio_noise, radio_detection_range, radio_connection_range)

    def update_history(self):
        self.history.append({
            "pos": self.pos,
            "hdtn": self.hdtn.get_state(),
            "radio": self.radio.get_state()
        })

    def move(self, dx, dy):
        if self.type == "fixed":
            logging.warning("Fixed agent {} tried to move".format(self.unique_id))
            return

        mag = (dx**2 + dy**2)**0.5
        if mag > MAX_SPEED:
            dx = dx / mag * MAX_SPEED
            dy = dy / mag * MAX_SPEED
        
        new_pos = (self.pos[0] + dx, self.pos[1] + dy)
        
        if self.model.space.out_of_bounds(new_pos):
            logging.warning("Agent {} tried to move out of bounds".format(self.unique_id))
            return
            
        self.model.space.move_agent(self, new_pos)

    def refresh_and_log(self):
        self.radio.refresh()
        self.hdtn.refresh()
        self.update_history()

    def step(self):
        self.main_logic()
        self.refresh_and_log()

    def get_state(self):
        return {
            "id": self.unique_id,
            "pos": self.pos,
            "type": self.type,
            "history": self.history,
            "hdtn": self.hdtn.get_state(),
            "radio": self.radio.get_state(),
            "target_location": self.target_location
        }
    
    def main_logic(self):
        def move_random():
            # Move randomly
            dx = self.random.randrange(-MAX_SPEED, MAX_SPEED)
            dy = self.random.randrange(-MAX_SPEED, MAX_SPEED)
            self.move(dx, dy)

        def find_best_location():
            # 1. Create a matrix with rows of of positions
            positions = []
            rssis = []
            for h in self.history:
                if "neighborhood" in h["radio"]:
                    if self.hdtn.current_target == "all":
                        rssis.append(h["radio"]["best_rssi"])
                        positions.append(h["pos"])
                    else:
                        for n in h["radio"]["neighborhood"]:
                            if n["id"] == self.hdtn.current_target:
                                if n["rssi"] < -900:
                                    continue
                                rssis.append(n["rssi"])
                                positions.append(h["pos"])
                                break

            positions = np.array(positions)
            rssis = np.array(rssis)

            # Cap the number of positions to 100
            positions = positions[-100:]
            rssis = rssis[-100:]

            if (positions.shape[0] < 3):
                move_random()
                return
            
            # 2. Assume RSSI is approximately of the form
            #    best_rssi = 10 * 2.5 * log10(1/((x-a)^2 + (y-b)^2)**0.5)
            #    where (a, b) is the position of the target
            def rssi_model(x, y, a, b, c):
                return 10 * c * np.log10(1/((a-x)**2 + (b-y)**2)**0.5)
            
            # 3. Use a least squares regression to find the best values for a and b
            def rssi_error(params):
                a, b, c = params
                return rssis - rssi_model(positions[:, 0], positions[:, 1], a, b, c)
            
            a, b, c = leastsq(rssi_error, (0, 0, 0))[0]

            if self.model.space.out_of_bounds((a, b)):
                move_random()
                return

            # 4. Move towards (a, b)
            dx = a - self.pos[0]
            dy = b - self.pos[1]
            self.target_location = (a, b)
            self.move(dx, dy)
            
        if self.type == "fixed":
            # Fixed agents don't move
            return
        elif self.type == "mobile":
            if self.hdtn.has_data:
                find_best_location()