import mesa
from agent import RoverAgent

class LunarModel(mesa.Model):
    """A lunar model with a number of rovers."""

    def __init__(self, N, width, height, radio_noise, radio_detection_range, radio_connection_range, center_static):
        self.num_agents = N
        self.space = mesa.space.ContinuousSpace(width, height, False)
        self.schedule = mesa.time.RandomActivation(self)

        if center_static:
            hdtn_target = 99
        else:
            hdtn_target = "all"

        # Create agents at random positions.
        for i in range(self.num_agents):
            a = RoverAgent(i, self, "mobile", radio_noise, radio_detection_range, radio_connection_range)
            a.hdtn.create_data()
            a.hdtn.schedule_transfer(hdtn_target)
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

        # for i in range(self.num_agents):
        #     a = RoverAgent(i, self)
        #     self.schedule.add(a)
        #     a.hdtn.create_data()
        #     a.hdtn.schedule_transfer(i+1)
        #     # Add the agent to a random spot in the space.
        #     x = self.random.uniform(0, 1) * self.space.width
        #     y = self.random.uniform(0, 1) * self.space.height
        #     self.space.place_agent(a, (x, y))

        

    def step(self):
        self.schedule.step()
