import numpy as np
from scipy.optimize import leastsq

class Convergence:
    def __init__(self, agent, model, target):
        self.agent = agent
        self.history = []
        self.target = target

    def refresh(self):
        # Update history
        self.history.append(
            {
                'radio': self.agent.radio.get_state(),
                'pos': self.agent.pos,
            }
        )
    
    def step(self):
        # 1. Create a matrix with previous data
        positions = []
        rssis = []
        for h in self.history:
            if "radio" in h:
                for n in h["radio"]["neighborhood"]:
                    if n["id"] == self.target or self.target == "all":
                        positions.append(h["pos"])
                        rssis.append(n["rssi"])

                        if n["connected"]:
                            self.agent.special_behavior["type"] = None
                            self.agent.movement.stop()

                        # if self.agent.model.space.get_distance(self.agent.pos, h["pos"]) < 10:
                        #     self.agent.special_behavior["type"] = None
                        #     self.agent.movement.stop()

        positions = np.array(positions[-1000:]) 
        rssis = np.array(rssis[-1000:])

        if len(positions) < 10:
            self.agent.movement.step()
            return

        # 2. Assume RSSI is approximately of the form
        #    best_rssi = 10 * 2.5 * log10(1/((x-a)^2 + (y-b)^2)**0.5)
        #    where (a, b) is the position of the target
        def rssi_model(x, y, a, b, c):
            distance = ((a - x) ** 2 + (b - y) ** 2) ** 0.5
            return 10 * c * np.log10(1 / distance)

        def rssi_error(params):
            a, b, c = params
            return rssis - rssi_model(positions[:, 0], positions[:, 1], a, b, c)

        # 3. Find the best fit for a potential target
        a, b, c = leastsq(rssi_error, (0, 0, 0))[0]

        # if self.agent.model.space.out_of_bounds((a, b)):
        #     self.agent.movement.move_towards(self.agent.movement.target_pos)
        #     return
        int_pos = (int(self.agent.pos[0]), int(self.agent.pos[1]))
        int_target = (int(a), int(b))

        # if self.agent.model.space.out_of_bounds((a, b)):
        #     # self.agent.movement.move_towards(self.agent.movement.target_pos)
        #     # self.agent.movement.step()

        #     # Move randomly
        #     target_pos = (np.random.randint(-self.agent.movement.max_speed, self.agent.movement.max_speed), np.random.randint(-self.agent.movement.max_speed, self.agent.movement.max_speed))
        #     self.agent.movement.move(*target_pos)
        #     return
        
        self.agent.movement.target_pos = (a, b)
        self.agent.movement.move_towards((a, b))
        print("Moving towards", (a, b))
