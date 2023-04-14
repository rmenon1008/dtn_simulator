import math
import logging
import json
import mesa
import numpy as np
from agent import RoverAgent
import random

# Would prefer for this to be selected by
# the user instead.
GRID_STEP = 10

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


class ObsGrid():
    """
    The ObsGrid class creates and stores a occupancy grid layer for the agent
    model to keep track of the presence of obstacles.
    """
    def __init__(self, size:tuple, grid_step:int=50, obs_size:tuple=(1, 13), obs_density:tuple=(1,15)) -> None:
        """
        :param size: Tuple of x and y lengths of the agent model space.
        :param grid_step: Integer value determining the size of each grid-square.
        :param obs_size: Tuple determining the min and max size range for obstacle generation.
        :param obs_density: Integer value between one and ten that determines amount of obstacles in the space.
        """
        self.x = size[0]
        self.y = size[1]
        self.grid_step = grid_step
        self.obs_density = obs_density
        self.obs_size = obs_size

        self.grid = [[0] * int(self.x / self.grid_step) for i in range(int(self.y / self.grid_step))]
    
    
    def place_obstacles(self):
        def generate_polygon(min_sides, max_sides, min_size, max_size):
            # Set the number of sides for the polygon
            num_sides = random.randint(min_sides, max_sides)

            # Set the length of each side of the polygon
            side_length = random.randint(min_size, max_size)

            # Set the starting position for the polygon
            start_x = random.randint(0, int(self.x / GRID_STEP))
            start_y = random.randint(0, int(self.y / GRID_STEP))

            # Generate the vertices of the polygon
            vertices = []
            angle = 360 / num_sides
            current_angle = random.randint(0, 360)
            for i in range(num_sides):
                x = start_x + side_length * math.cos(math.radians(current_angle))
                y = start_y + side_length * math.sin(math.radians(current_angle))
                vertices.append((x, y))
                current_angle += angle

            # Close the polygon
            vertices.append(vertices[0])

            return vertices

        # Generate a list of random polygons
        polygons = []
        for i in range(random.randint(self.obs_density[0], self.obs_density[1])):
            # TODO: the min/max sizes should be related
            vertices = generate_polygon(3, 10, self.obs_size[0], self.obs_size[1])
            polygons.append(vertices)

        def point_in_polygon(point, polygon):
            """
            Determines if a point is inside a polygon.
            """
            x, y = point
            inside = False
            j = len(polygon) - 1
            for i in range(len(polygon)):
                if ((polygon[i][1] > y) != (polygon[j][1] > y)) and \
                        (x < (polygon[j][0] - polygon[i][0]) * (y - polygon[i][1]) / (polygon[j][1] - polygon[i][1]) + polygon[i][0]):
                    inside = not inside
                j = i
            return inside
        
        # Check each grid cell for occupancy
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                x = j + 0.5
                y = i + 0.5
                point = (x, y)
                for polygon in polygons:
                    if point_in_polygon(point, polygon):
                        self.grid[i][j] = 1
        
        # print(np.array(self.grid))

    def get_grid(self):
        """
        Returns grid for this ObsGrid object.
        """
        return self.grid
    
    def save_grid(self):
        """
        Save the current ObsGrid object.
        """
        pass

    def load_grid(self):
        """
        Load a saved ObsGrid object.
        """
        pass


class LunarModel(mesa.Model):
    """
    A model that rover agents exist within.
    Also provides methods for accessing neighbors.
    """

    def __init__(self, size, model_params, initial_state):
        super().__init__()

        # Check that the the grid step is a factor of the length/width of the screen size.
        assert(size[0] % GRID_STEP == 0 and size[1] % GRID_STEP == 0)

        self.model_params = model_params
        
        # Set up the space and schedule
        self.space = mesa.space.ContinuousSpace(
            size[0], size[1], False)
        self.schedule = mesa.time.RandomActivation(self)

        # Used by mesa to know when the simulation is over
        self.running = True

        # Stores references to the agents as mappings of "id"->agent
        self.agents = {}
        
        self.grid_layer = ObsGrid(size, grid_step=GRID_STEP)
        self.grid_layer.place_obstacles()
        self.grid_step = GRID_STEP
        self.grid = self.grid_layer.get_grid()
        # print(np.array(self.grid_layer.get_grid()))

        for agent_options in initial_state["agents"]:

            # Merge the node defaults with the individual node options
            # Important to copy() to avoid mutating the original
            options = agent_options.copy()
            merge(initial_state["agent_defaults"], options)

            if "pos" not in options:
                options["pos"] = (self.random.uniform(0, self.space.width),
                                  self.random.uniform(0, self.space.height))
                
                while self.grid[math.floor(options["pos"][1] / GRID_STEP)][math.floor(options["pos"][0] / GRID_STEP)] == 1:
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
        
        # print(np.array(self.grid_layer.get_grid()))

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

        if self.space.out_of_bounds(new_pos) or self.grid[math.floor(new_pos[1] / GRID_STEP)][math.floor(new_pos[0] / GRID_STEP)] == 1:
            logging.warning(
                "Agent {} tried to move out of bounds".format(agent.unique_id))
            return

        self.space.move_agent(agent, (agent.pos[0] + dx, agent.pos[1] + dy))

    """
    Used to easily obtain references to other DTN objects.
    """
    def get_dtn_object(self, node_id):
        return self.agents[node_id].dtn
