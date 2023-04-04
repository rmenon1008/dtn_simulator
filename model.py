import mesa
from agent import RoverAgent

def merge(source, destination):
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value
    return destination

class LunarModel(mesa.Model):
    """A lunar model with a number of rovers."""

    def __init__(self, model_params, initial_state):
        super().__init__()
        self.space = mesa.space.ContinuousSpace(
            model_params["size"][0], model_params["size"][1], False)
        self.schedule = mesa.time.RandomActivation(self)
        self.running = True

        for agent_options in initial_state["agents"]:

            # Merge the node defaults with the individual node options
            # Important to copy() to avoid mutating the original
            options = (merge(initial_state["agent_defaults"], agent_options)).copy()

            if "pos" not in options:
                options["pos"] = (self.random.uniform(0, self.space.width),
                                  self.random.uniform(0, self.space.height))
            if "id" not in options:
                options["id"] = self.next_id()

            # Create the agent
            # Add it to the schedule to get stepped each model tick
            # Place it on the space
            a = RoverAgent(self, options)
            self.schedule.add(a)
            self.space.place_agent(a, options["pos"])

    def step(self):
        self.schedule.step()
