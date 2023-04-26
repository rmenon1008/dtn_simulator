import math
import logging
import mesa
import itertools
import json

from metrics_parser import summary_statistics
from peripherals.movement import generate_pattern
from payload import ClientPayload
from agent.client_agent import ClientAgent
from agent.router_agent import RouterAgent, RoutingProtocol

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

        # To track contact plan generation
        if "make_contact_plan" in model_params:
            self.contacts = dict()
            """
            self.contacts is a dictionary that contains mappings of pairs to timestamps in which a contact exists
                - The dict keys are stored as python frozensets for efficiency reasons.
                    For example (2,1) and (1,2) will map to equivalent frozensets
                    This are the same because we always have bidirectional contacts in our simulation
                - The dict values are lists of step numbers
            Example:
                [(1,2)] -> [step1,step2,step3,step4,step92,step93,step94] # node 1 & 2 are in contact at steps...
                [(1,3)] -> [step1,step2,step3,step4,step92,step93,step94] # node 1 & 3 are in contact at steps...
                [(2,3)] -> [step1,step2,step3,step4,step92,step93,step94] # node 2 & 3 are in contact at steps...
            How it is used:
            - self.__track_contacts() updates this dictionary on every step to add new contacts
            - self.__generate_contact_plan() is called when the simulation is over to convert this data into a contact plan json file
            """

        # Set up an array of data drops
        self.data_drops = []

        # Set up the space and schedule
        self.space = mesa.space.ContinuousSpace(
            size[0], size[1], False)
        self.schedule = mesa.time.BaseScheduler(self)

        # Used by mesa to know when the simulation is over
        self.running = True

        # Stores references to the agents as mappings of "id"->agent
        self.agents = {}
        self.router_agents = {}
        self.client_agents = {}

        # A dictionary of metrics useful for tracking data that is cumulative throughout a simulation
        self.metrics = {"num_steps": self.model_params["max_steps"], "total_bundles_stored_so_far": 0}

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
            if "type" not in options or options["type"] == "router":
                a = RouterAgent(self, options, model_params["routing_protocol"])
                self.router_agents[options["id"]] = a
            elif options["type"] == "client":
                a = ClientAgent(self, options)
                self.client_agents[options["id"]] = a

            print(a)
            self.schedule.add(a)
            self.space.place_agent(a, options["pos"])

            # Stash the agent in a map for easy lookup later.
            self.agents[options["id"]] = a

    def step(self):
        # Check if there are any data drops
        if "data_drop_schedule" in self.model_params:
            self.update_data_drops()
        if "make_contact_plan" in self.model_params:
            self.__track_contacts()

        self.schedule.step()
        
        if "log_metrics" in self.model_params:
            self.__update_metrics()

        if "max_steps" in self.model_params and self.model_params["max_steps"] is not None:
            if self.schedule.steps >= self.model_params["max_steps"]:
                self.__finish_simulation()

    def __finish_simulation(self):
        self.running = False
        if "make_contact_plan" in self.model_params:
            self.__generate_contact_plan()
        
        if "log_metrics" in self.model_params:
            # Log metrics for the last step
            agent_list = []
            for agent in self.schedule.agents:
                metrics = agent.get_state()
                if metrics["type"] == "router":
                    continue
                del metrics["pos"]
                del metrics["radio"]
                del metrics["history"]
                agent_list.append(metrics)
            final_metric_entry = {
                "step": self.schedule.steps,
                "agents": agent_list,
            }
            # Plug in the final metrics + the cumulative metrics
            title = self.model_params["title"] + "\n"
            title += "\tRouting Protocol: {}\n".format(str(RoutingProtocol(self.model_params["routing_protocol"])))
            title += "\tMax Steps: {} steps \n".format(self.model_params["max_steps"])
            title += "\tRSSI Noise STDEV: {} \n".format(self.model_params["rssi_noise_stdev"])
            title += "\tModel Speed Limit: {} m/s \n".format(self.model_params["model_speed_limit"])
            title += "\tHost Router Timeout: {} steps \n".format(self.model_params["host_router_mapping_timeout"])
            title += "\tPayload Lifespan: {} steps \n".format(self.model_params["payload_lifespan"])
            title += "\tBundle Lifespan: {} steps \n".format(self.model_params["bundle_lifespan"])
            summary_statistics(title, final_metric_entry, self.metrics, self.model_params["correctness"])

    def __track_contacts(self):
        curr_step = self.schedule.steps
        # Loop through all routers
        for curr_router_id in self.router_agents:
            curr_router_agent = self.router_agents[curr_router_id]
            neighbor_data = self.get_neighbors(curr_router_agent)
            # Loop through all neighbors of this router
            for neighbor in neighbor_data:
                if neighbor["connected"] and neighbor["id"] in self.router_agents:
                    # Found a connected pair of router agents
                    pair = frozenset((curr_router_id, neighbor["id"]))
                    # Add the current step number for this pair
                    if pair not in self.contacts:
                        self.contacts[pair] = [curr_step]
                    elif self.contacts[pair][-1] != curr_step:
                        # avoid adding duplicate step numbers
                        self.contacts[pair].append(curr_step)

    def __generate_contact_plan(self):
        def ranges(i):
            # helper function from: https://stackoverflow.com/a/43091576
            # condenses [0,1,2,3,4,5,6,9,10,11,12] into [(0,6),(9,12)]
            for a, b in itertools.groupby(enumerate(i), lambda pair: pair[1] - pair[0]):
                b = list(b)
                yield b[0][1], b[-1][1]
        contact_list = []
        curr_contact_id = 0
        for pair in self.contacts:
            node1, node2 = pair
            contact_times = list(ranges(self.contacts[pair]))
            for time_range in contact_times:
                start, end = time_range
                contact_list.append({
                    "contact": curr_contact_id,
                    "source": node1,
                    "dest": node2,
                    "startTime": start,
                    "endTime": end,
                    "rate": 1000,
                    "owlt": 0,
                    "confidence": 1.,
                    })
                curr_contact_id += 1
                contact_list.append({
                    "contact": curr_contact_id,
                    "source": node2, # switch the source & dest
                    "dest": node1,
                    "startTime": start,
                    "endTime": end,
                    "rate": 1000,
                    "owlt": 0,
                    "confidence": 1.,
                    })
                curr_contact_id += 1
    
        final_cp = {"contacts": contact_list}
        with open("./cp.json", "w") as outfile:
            outfile.write(json.dumps(final_cp, indent=4))
    
    def update_data_drops(self):
        DROP_PICKUP_RANGE = 5
        
        # Check if there are any new data drops
        for drop in self.model_params["data_drop_schedule"]:
            if drop["time"] == self.schedule.steps:
                self.data_drops.append(drop)
            elif "repeat_every" in drop:
                # TODO: Have an option to stop repeating after a certain amount of time
                if "until" in drop and self.schedule.steps > drop["until"]:
                    continue
                if (self.schedule.steps - drop["time"]) % drop["repeat_every"] == 0 and self.schedule.steps > drop["time"]:
                    self.data_drops.append(drop)

        # Check if any agents are in range of a data drop
        for drop in self.data_drops:
            for agent in self.schedule.agents:
                if self.space.get_distance(agent.pos, drop["pos"]) < DROP_PICKUP_RANGE:
                    # Make sure the agent is a client
                    if isinstance(agent, ClientAgent):
                        # TODO: Maybe we need to add a field to drops so that only specific clients can pick up the drop
                        #       This would help for reasoning about the simulation scenarios being made
                        # If the drop's target is the nearby client agent, the client will ignore it
                        # Someone else will pick it up eventually
                        # Added this condition check bc I witnessed a client taking 2000 steps to get a bundle delivered to itself.
                        if drop["target_id"] != agent.unique_id:
                            agent.payload_handler.store_payload(ClientPayload(drop["drop_id"], agent.unique_id, drop["target_id"], self.schedule.steps, self.model_params["payload_lifespan"]))
                            self.data_drops.remove(drop)

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

    def teleport_agent(self, agent, pos):
        """Teleports the agent to the given position"""
        if self.space.out_of_bounds(pos):
            logging.warning(
                "Agent {} tried to teleport out of bounds".format(agent.unique_id))
            return

        self.space.move_agent(agent, pos)

    def __update_metrics(self):
        """Logs the metrics for the current step"""
        for agent in self.schedule.agents:
            metrics = agent.get_state()
            if "routing_protocol" not in metrics:
                continue # ignore clients
            # can assume agent is a router
            if self.model_params["correctness"]:
                # check if the router is holding any duplicate bundles
                seen_bundles = set()
                for bundle in metrics["routing_protocol"]["curr_stored_bundles"]:
                    if str(bundle) in seen_bundles:
                        print("INVARIANT VIOLATION: model found a dupe bundle {}".format(str(bundle)))
                    else:
                        seen_bundles.add(str(bundle))
            # Currently tracking only 1 cumulative metric for router agents only
            self.metrics["total_bundles_stored_so_far"] += metrics["routing_protocol"]["curr_num_stored_bundles"]

    """
    Used to easily obtain references to routing_protocol objects belonging to RouterAgents on the network.
    """
    def get_routing_protocol_object(self, node_id):
        return self.router_agents[node_id].routing_protocol

    """
    Used to easily obtain references to RouterClientPayloadHandler and ClientPayloadHandler objects 
    from RouterAgents and ClientAgents.
    """
    def get_client_payload_handler_object(self, node_id):
        return self.agents[node_id].payload_handler
