import math
import logging
import re
import os
import json
import mesa
import numpy as np
import cv2
from copy import deepcopy
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
        :param size:        Tuple of x and y lengths of the agent model space.
        :param grid_step:   Integer value determining the size of each grid-square.
        :param obs_size:    Tuple determining the min and max size range for obstacle generation.
        :param obs_density: Integer value between one and ten that determines amount of obstacles in the space.
        """

        self.x = size[0]
        self.y = size[1]
        self.grid_step = grid_step
        self.obs_density = obs_density
        self.obs_size = obs_size

        self.grid = [[0] * int(self.x / self.grid_step) for i in range(int(self.y / self.grid_step))]
    
    
    def place_obstacles(self) -> None:
        """
        Randomly generates and places polygon obstacles throughout grid-world environment
        layer
        """
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
        

    def get_grid(self) -> list:
        """
        Returns grid for this ObsGrid object.
        """
        return self.grid
    

    def save_grid(self, filepath:str) -> None:
        """
        Save the current ObsGrid object.
        :param filepath: A string representing the path to save this obstacle grid layer to. Default appends 
        ".layer" to the file name.
        """

        # Extract directory by regex matching to split string until last '/'
        dir = list(filter(None, re.split("^(.+)\/([^\/]+)$", filepath)))[0]

        if not os.path.exists(dir):
            logging.error("The directory specified for saving obstacle grid file does not exist")
            raise FileNotFoundError
        
        if os.path.exists(filepath):
            logging.error("An obstacle grid layer file with this path already exists!")
            raise FileExistsError

        with open(filepath + ".layer", "w") as f:
            for i in range(int(np.shape(self.grid)[0])):
                for j in range(int(np.shape(self.grid)[1])):
                    f.write(str(self.grid[i][j]))
                f.write('\n')
        

    def load_grid(self, filepath:str):
        """
        Load a saved ObsGrid object.
        """
        if not os.path.exists(filepath):
            logging.error("The directory specified for saving obstacle grid file does not exist")
            raise FileNotFoundError

        temp_grid = []

        with open(filepath, "r") as f:
            idx = 0
            for line in f:
                int_line = [int(val) for val in line if val != '\n']
                temp_grid.append(int_line)
                idx += 1
        
        self.grid = deepcopy(temp_grid)
        self.y = len(self.grid) * self.grid_step
        self.x = len(self.grid[0]) * self.grid_step


    def convert_plan(self, floor_plan_path:str, dilatation_size:int=3, downsmpl:int=4) -> None:
        """
        Converts an image of a building floor-plan into a scaled occupancy grid,
        with 1's representing walls and 0's representing free-space.
        :param floor_plan_path: The path to the floor-plan image to be loaded in.
        """

        # Load the image
        image = cv2.imread(floor_plan_path)

        dilation_shape = cv2.MORPH_RECT
        element = cv2.getStructuringElement(dilation_shape, (2 * dilatation_size + 1, 2 * dilatation_size + 1),
                                        (dilatation_size, dilatation_size))
        dil_im = cv2.dilate(image, element)

        gray = cv2.cvtColor(dil_im, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Down sample the image to make grid more workable.
        for i in range(downsmpl):
            binary = cv2.pyrDown(binary)

        print("Rows: " + str(np.shape(binary)[0]) + "\tCols: " + str(np.shape(binary)[1]))
        
        new_grid = [[0] * np.shape(binary)[0]] * np.shape(binary)[0]

        _, binary = cv2.threshold(binary, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        new_grid = [[int(binary[i][j] / 255) for j in range(np.shape(binary)[1])] for i in range(np.shape(binary)[0])]

        self.grid = deepcopy(np.array(new_grid))
        print(np.array(new_grid))
        cv2.imwrite("./boop.png", binary)


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
        self.grid_layer.load_grid("./grid_layers/basement6.layer")
        self.grid_step = GRID_STEP
        self.grid = self.grid_layer.get_grid()
        # self.grid_layer.save_grid("./grid_layers/urmum")
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
