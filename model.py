import math
import logging
import mesa
import os
import cv2
import numpy as np
import re
from copy import deepcopy
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

def bresenham(x0, y0, x1, y1):
    """Yield integer coordinates on the line from (x0, y0) to (x1, y1).

    Input coordinates should be integers.

    The result will contain both the start and the end point.
    """
    dx = x1 - x0
    dy = y1 - y0

    xsign = 1 if dx > 0 else -1
    ysign = 1 if dy > 0 else -1

    dx = abs(dx)
    dy = abs(dy)

    if dx > dy:
        xx, xy, yx, yy = xsign, 0, 0, ysign
    else:
        dx, dy = dy, dx
        xx, xy, yx, yy = 0, ysign, xsign, 0

    D = 2*dy - dx
    y = 0

    points = []

    for x in range(dx + 1):
        # yield x0 + x*xx + y*yx, y0 + x*xy + y*yy
        points.append((x0 + x*xx + y*yx, y0 + x*xy + y*yy))
        if D >= 0:
            y += 1
            D -= 2*dx
        D += 2*dy

    return points


class LoadLayers():
    def __init__(self, floorplan_path:str) -> None:
        if not os.path.exists(floorplan_path):
            logging.error("The specified saved floorplan file does not exist")
            raise FileNotFoundError

        # if not os.path.exists(rssi_data_path):
        #     logging.error("The specified saved floorplan file does not exist")
        #     raise FileNotFoundError
        
        self.floorplan_path = floorplan_path
        # self.rssi_data_path = rssi_data_path
    

    def convert_plan(self, dilatation_size:int=3, downsmpl:int=4) -> list:
        """
		Converts an image of a building floor-plan into a scaled occupancy grid,
		with 1's representing walls and 0's representing free-space.
		:param floor_plan_path: The path to the floor-plan image to be loaded in.
		:param dilatation_size: How much to dilate the image passed in for the grid. Larger value means less fine-detail.
		:param downsmpl:				How much to downsample the resolution of the image. Every increment downsamples image by a factor of 2. Default is 4, so the
		image's resolution is reduced by 2^4 times.
		"""

		# Check that the floor-plan image file path is valid.
        if not os.path.exists(self.floorplan_path):
            os.error("The specified floor plan image does not exist!")
            raise FileNotFoundError

		# Load the image
        image = cv2.imread(self.floorplan_path)

		# Dilate the image to remove clutter.
        dilation_shape = cv2.MORPH_RECT
        element = cv2.getStructuringElement(dilation_shape, (2 * dilatation_size + 1, 2 * dilatation_size + 1),
																		(dilatation_size, dilatation_size))
        dil_im = cv2.dilate(image, element)

		# Convert image to gray-scale
        gray = cv2.cvtColor(dil_im, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
		
		# Downsample the image for compression purposes.
        for i in range(downsmpl):
            binary = cv2.pyrDown(binary)

		# Just to check the shape of the binary grid.
        print("Rows: " + str(np.shape(binary)[0]) + "\tCols: " + str(np.shape(binary)[1]))
		
		# Set values to 1 or 0 based on the grey-scaled pixel value
        _, binary = cv2.threshold(binary, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        grid = [[int(binary[i][j] / 255) for j in range(np.shape(binary)[1])] for i in range(np.shape(binary)[0])]

		# Convert grid to a numpy array, write it to a new image (for debugging), and return the new grid.
        # grid = np.array(grid)
        cv2.imwrite("./thrshold_dwnsmpl.png", binary)
        return grid


    def save_plan(self, filepath:str, grid:list) -> None:
        """
        Saves the given plan into a .layer txt file, which represents an obstacle grid.
        :param filepath:    The file path to save the .layer file to.
        :param grid:        The binary obstacle grid representing a floor-plan.     
        """

        # Extract directory by regex matching to split string until last '/'
        dir = list(filter(None, re.split("^(.+)\/([^\/]+)$", filepath)))[0]

        # Check that the specified directory is valid.
        if not os.path.exists(dir):
            os.error("The directory specified for saving obstacle grid file does not exist")
            raise FileNotFoundError
        
        # Check that there is no file with filepath's name already.
        if os.path.exists(filepath):
            os.error("An obstacle grid layer file with this path already exists!")
            raise FileExistsError
        
        # Write the grid to the .layer file.
        with open(filepath, "w") as f:
            for i in range(int(np.shape(grid)[0])):
                for j in range(int(np.shape(grid)[1])):
                    f.write(str(grid[i][j]))
                f.write('\n')

    def load_grid(self, filepath:str, delimiter=""):
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
                # num = 
                split_line = line.split(" ")
                int_line = [float(val) for val in split_line if val != '\n']
                temp_grid.append(int_line)
                idx += 1
        
        grid = deepcopy(temp_grid)
        # self.y = len(self.grid) * self.grid_step
        # self.x = len(self.grid[0]) * self.grid_step
        return grid

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

        self.grid_step = 10
        l = LoadLayers("./floor_plans/small_basement.png")
        if self.model_params["enable_walls"]:
            self.grid = l.convert_plan(downsmpl=3)
        else:
            self.grid = np.zeros(np.shape(l.convert_plan(downsmpl=3))).tolist()

        if self.model_params["rssi_source"] == "real_data":
            self.rssi_layer = (np.flipud(l.load_grid("./grid_layers/interpolate_rssi.layer"))).tolist()
            
        elif self.model_params["rssi_source"] == "shadowing":
            self.rssi_layer = np.zeros(np.shape(self.grid)).tolist()
            for y in range(len(self.grid)):
                for x in range(len(self.grid[0])):
                    # Find the number of grid pixels that are filled in between the agents
                    # This is the number of walls that block the signal
                    fixed_x = int(1950/ self.grid_step)
                    fixed_y = int(285 / self.grid_step)

                    walls = self.walls_in_between((x, y), (fixed_x, fixed_y))

                    distance = math.sqrt((x - fixed_x)**2 + (y - fixed_y)**2)
                    if distance == 0:
                        self.rssi_layer[y][x] = 0
                        continue

                    # noise = self.random.gauss(0, self.model_params["rssi_noise_stdev"])
                    self.rssi_layer[y][x] =  10 * 2.5 * math.log10(1/(distance * self.grid_step + 100*walls)) #+ noise

        else:
            self.rssi_layer = np.zeros(np.shape(self.grid)).tolist()

        assert(np.shape(self.grid) == np.shape(self.rssi_layer))

        # print(max(self.rssi_layer[154]))

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
            elif "id" != 1:
                while self.grid[math.floor(options["pos"][1] / self.grid_step)][math.floor(options["pos"][0] / self.grid_step)] == 1:
                    options["pos"] = (self.random.uniform(0, self.space.width),
                                      self.random.uniform(0, self.space.height))

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

    def walls_in_between(self, pos1, pos2):
        points = bresenham(pos1[0], pos1[1], pos2[0], pos2[1])

        # Count the number of walls that block the signal
        walls = 0
        for p in points:
            try:
                if self.grid[p[1]][p[0]] == 1:
                    walls += 1
            except:
                pass

        return walls

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

        # distance = self.space.get_distance(agent.pos, other.pos)
        # if distance == 0:
        #     return 0
        # clean_rssi = 10 * 2.5 * math.log10(1/distance)
        # noise = self.random.gauss(0, self.model_params["rssi_noise_stdev"])
        # return clean_rssi + noise

        # I created a new parameter to choose the source of the rssi values
        rssi_source = self.model_params.get("rssi_source", "path_loss")

        if rssi_source == "real_data":
            idx_y = math.floor(agent.pos[1] / self.grid_step)
            idx_x = math.floor(agent.pos[0] / self.grid_step)
            return self.rssi_layer[idx_y][idx_x]
        
        elif rssi_source == "shadowing":
            idx_y = math.floor(agent.pos[1] / self.grid_step)
            idx_x = math.floor(agent.pos[0] / self.grid_step)
            noise = self.random.gauss(0, self.model_params["rssi_noise_stdev"])
            return self.rssi_layer[idx_y][idx_x] + noise

        else:
            distance = self.space.get_distance(agent.pos, other.pos)
            if distance == 0:
                return 0
            clean_rssi = 10 * 2.5 * math.log10(1/distance)
            noise = self.random.gauss(0, self.model_params["rssi_noise_stdev"])
            print(noise)
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

        obs = self.grid[math.floor(pos[1] / self.grid_step)][math.floor(pos[0] / self.grid_step)]
        return self.space.out_of_bounds(pos) or obs == 1

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
