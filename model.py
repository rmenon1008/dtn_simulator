import mesa
from agent import RoverAgent

class LunarModel(mesa.Model):
    """A lunar model with a number of rovers."""

    def __init__(self, N, width, height):
        self.num_agents = N
        self.space = mesa.space.ContinuousSpace(width, height, False)
        self.schedule = mesa.time.RandomActivation(self)

        # Create agents at random positions.
        for i in range(self.num_agents):
            a = RoverAgent(i, self)
            a.hdtn.create_data()
            a.hdtn.schedule_transfer(99)
            self.schedule.add(a)
            # Add the agent to a random spot in the space.
            x = self.random.uniform(0, 1) * self.space.width
            y = self.random.uniform(0, 1) * self.space.height
            self.space.place_agent(a, (x, y))
            

        # Create a fixed agent at the center of the space.
        a = RoverAgent(99, self, "fixed")
        self.schedule.add(a)
        self.space.place_agent(a, (width/2, height/2))        

    def step(self):
        self.schedule.step()
