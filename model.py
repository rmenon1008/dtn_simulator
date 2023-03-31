import mesa
from agent import RoverAgent

class LunarModel(mesa.Model):
    """A lunar model with a number of rovers."""

    def __init__(self, N, width, height, radio_noise, radio_detection_range, radio_connection_range, center_static, finish_on_transfer, move_spiral, move_towards_target):
        self.num_agents = N
        self.space = mesa.space.ContinuousSpace(width, height, False)
        self.schedule = mesa.time.RandomActivation(self)
        self.running = True
        self.finish_on_transfer = finish_on_transfer
        
        self.finished_nodes = 0

        if move_towards_target:
            if center_static:
                hdtn_target = 99
            else:
                hdtn_target = "all"
        else:
            hdtn_target = None

        # Create agents at random positions.
        for i in range(self.num_agents):
            a = RoverAgent(i, self, "mobile", radio_noise, radio_detection_range, radio_connection_range, move_spiral)
            a.hdtn.create_data()
            a.hdtn.schedule_transfer(hdtn_target, cb=self.transfer_cb)
            self.schedule.add(a)
            # Add the agent to a random spot in the space.
            x = self.random.uniform(0, 1) * self.space.width
            y = self.random.uniform(0, 1) * self.space.height
            self.space.place_agent(a, (x, y))
            
        if center_static:
            # Create a fixed agent at the center of the space.
            a = RoverAgent(99, self, "fixed", radio_noise, radio_detection_range, radio_connection_range)
            self.schedule.add(a)
            self.space.place_agent(a, (width/2, height/2))
        
    def transfer_cb(self, other_agent):
        if self.finish_on_transfer:
            self.finished_nodes += 1
            if self.finished_nodes == self.num_agents:
                self.running = False
        
    def step(self):
        self.schedule.step()
