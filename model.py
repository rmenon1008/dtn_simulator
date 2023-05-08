import math
import logging
import mesa

from peripherals.movement import generate_pattern
from agent.simple_agent import SimpleAgent

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
            destination.setdefault(key, value)
    return destination


class LunarModel(mesa.Model):
    """
    A model that RouterAgents and ClientAgents exist within.
    Also provides methods for accessing neighbors.
    """

    def __init__(self, size, model_params, initial_state):
        super().__init__()
        self.model_params = model_params

        # Set up the space and schedule
        self.space = mesa.space.ContinuousSpace(size[0], size[1], False)
        self.schedule = mesa.time.BaseScheduler(self)
        self.running = True

        # Initialize agents
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
            a = None
            if options["type"] == "simple":
                a = SimpleAgent(self, options)
            else:
                logging.error("Unknown agent type: " + options["type"])
                logging.error("Only simple agents are supported. Use movement to modify how they move")
                exit(1)
            
            # Add the agent to the model schedule and space
            self.schedule.add(a)
            self.space.place_agent(a, options["pos"])

    def step(self):
        # This calls step() on all the agents
        self.schedule.step()

        # Check if we should stop the simulation
        if "max_steps" in self.model_params and self.model_params["max_steps"] is not None:
            if self.schedule.steps >= self.model_params["max_steps"]:
                self.__finish_simulation()

    def __finish_simulation(self):
        print("Simulation finished at step " + str(self.schedule.steps))
        self.running = False

    def get_rssi(self, agent, other):
        """Returns the RSSI of the agent to the other agent in dBm"""

        # @Lyla, @Andrew: This function is what you could replace to bring in 
        #                 interpolated RSSI values.

        distance = self.space.get_distance(agent.pos, other.pos)
        if distance == 0:
            return 0
        clean_rssi = 10 * 2.5 * math.log10(1/distance)
        noise = self.random.gauss(0, self.model_params["rssi_noise_stdev"])
        return clean_rssi + noise

    def estimate_distance_from_rssi(self, rssi):
        """
        Returns the distance of the agent using an RSSI in dbm.
        Right now, used to draw the 'fuzzy' range around agents.
        """
        distance = math.exp(-0.0921034 * rssi)
        return distance

    def get_neighbors(self, agent):
        """
        Returns a list of all agents within the detection range of the agent
        Each entry includes the agent's unique id, RSSI, and whether or not
        the agent is connected. It's supposed to be analogous to a WiFi scan
        of nearby networks and their signal strengths.
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
                    })

        return neighbors
    
    def pos_invalid(self, pos):
        """Returns whether or not the given position is a valid location in the model"""

        # @Isaac: Not sure how you check if an agent is running into
        #         walls in your version, but this is probably a good
        #         place to put it.

        return self.space.out_of_bounds(pos)

    def move_agent(self, agent, dx, dy):
        """Moves the agent by the given delta x and delta y"""
        # Find out how fast the agent is trying to move
        mag = (dx**2 + dy**2)**0.5

        # Don't allow the agent to move faster than the model speed limit
        # Give a little wiggle room for floating point errors
        if mag > self.model_params["model_speed_limit"] + 0.0005:
            logging.warning(
                "Agent {} tried to move faster than model speed limit".format(agent.unique_id))
            return
        new_pos = (agent.pos[0] + dx, agent.pos[1] + dy)

        # Check if the agent is trying to move to an invalid position
        if self.pos_invalid(new_pos):
            logging.warning(
                "Agent {} tried to move to an invalid position".format(agent.unique_id))
            return

        self.space.move_agent(agent, (agent.pos[0] + dx, agent.pos[1] + dy))

    def teleport_agent(self, agent, pos):
        """Teleports the agent to the given position. Should be used to model satellites, not ground rovers"""

        # Warn in case it's not obvious that this is happening
        logging.warning("Agent {} teleported to {}".format(agent.unique_id, pos))
        
        if self.pos_invalid(pos):
            logging.warning(
                "Agent {} tried to teleport to an invalid position".format(agent.unique_id))
            return

        self.space.move_agent(agent, pos)
