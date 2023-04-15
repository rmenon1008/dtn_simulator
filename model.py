import math
import logging
import json
import mesa

from agent import RoverAgent
from peripherals.movement import generate_pattern


def merge(source, destination):
    """
    Recursively merges source dict into destination dict.
    Used for merging node defaults with individual node options.
    """
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value
    return destination


class LunarModel(mesa.Model):
    """
    A model that rover agents exist within.
    Also provides methods for accessing neighbors.
    """

    def __init__(self, size, model_params, initial_state):
        super().__init__()
        self.model_params = model_params

        # Set up the space and schedule
        self.space = mesa.space.ContinuousSpace(
            size[0], size[1], False)
        self.schedule = mesa.time.RandomActivation(self)

        # Used by mesa to know when the simulation is over
        self.running = True

        # Stores references to the agents as mappings of "id"->agent
        self.agents = {}

        for agent_options in initial_state["agents"]:

            # Merge the node defaults with the individual node options
            # Important to copy() to avoid mutating the original
            options = agent_options.copy()
            merge(initial_state["agent_defaults"], options)

            if "pos" not in options:
                if "movement" in options and "pattern" in options["movement"]:
                    options["pos"] = generate_pattern(options["movement"]).starting_pos
                else:
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

            # Stash the agent in a map for easy lookup later.
            self.agents[options["id"]] = a

    def step(self):
        self.schedule.step()
        if "max_steps" in self.model_params and self.model_params["max_steps"] is not None:
            if self.schedule.steps >= self.model_params["max_steps"] - 1:
                self.running = False

    def get_rssi(self, agent, other):
        """Returns the RSSI of the agent to the other agent in dBm"""
        distance = self.space.get_distance(agent.pos, other.pos)
        if distance == 0:
            return 0
        clean_rssi = 10 * 2.5 * math.log10(1/distance)
        noise = self.random.gauss(0, self.model_params["rssi_noise_stdev"])
        return clean_rssi + noise

    def get_distance(self, rssi):
        """
        Returns the distance of the agent using an RSSI in dbm.
        Right now, only used to draw the 'fuzzy' range around agents.
        """
        distance = math.exp(-0.0921034 * rssi)
        return distance

    def get_neighbors(self, agent):
        """
        Returns a list of all agents within the detection range of the agent
        Each entry includes the agent's unique id, RSSI, and whether or not
        the agent is connected.
        If the agent is connected, the entry also includes a function that
        can be called to send a bundle to the agent.
        """

        det_thresh = agent.radio.detection_thresh
        con_thresh = agent.radio.connection_thresh

        neighbors = []
        for other in self.schedule.agents:
            if other is not agent:
                rssi = self.get_rssi(agent, other)
                if rssi >= det_thresh:
                    connected = rssi >= con_thresh
                    neighbors.append({
                        "id": other.unique_id,
                        "rssi": rssi,
                        "connected": connected,
                        "send_bundle": other.dtn.handle_bundle if connected else None
                    })

        return neighbors

    def move_agent(self, agent, dx, dy):
        """Moves the agent by the given delta x and delta y"""
        mag = (dx**2 + dy**2)**0.5

        # Give it a little bit of leeway to avoid floating point errors
        if mag > self.model_params["model_speed_limit"] + 0.0005:
            logging.warning(
                "Agent {} tried to move faster than model speed limit".format(agent.unique_id))
            return

        new_pos = (agent.pos[0] + dx, agent.pos[1] + dy)

        if self.space.out_of_bounds(new_pos):
            logging.warning(
                "Agent {} tried to move out of bounds".format(agent.unique_id))
            return

        self.space.move_agent(agent, (agent.pos[0] + dx, agent.pos[1] + dy))

    """
    Used to easily obtain references to other DTN objects.
    """

    def get_dtn_object(self, node_id):
        return self.agents[node_id].dtn
