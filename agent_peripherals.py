import math


def pol_to_cart(r, phi):
    return (r * math.cos(phi), r * math.sin(phi))


def makeSerializeable(obj):
    """
    Helper function to make sure an object is serializeable
    to be sent to the visualization server.
    """
    if isinstance(obj, dict):
        return {k: makeSerializeable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [makeSerializeable(v) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(makeSerializeable(v) for v in obj)
    elif isinstance(obj, set):
        return set(makeSerializeable(v) for v in obj)
    elif isinstance(obj, complex):
        return (obj.real, obj.imag)
    elif isinstance(obj, type):
        return obj.__name__
    elif hasattr(obj, "__dict__"):
        return makeSerializeable(obj.__dict__)
    else:
        return obj


class Movement():
    def __init__(self, agent, model, options):
        self.agent = agent
        self.model = model
        # Options are unused for now

        # Move at the speed limit
        self.speed = self.model.model_params["model_speed_limit"]

    def refresh(self):
        # This peripheral does not need to refresh because
        # it's state can not change based on the other nodes
        pass

    def move(self, dx, dy):
        mag = (dx**2 + dy**2)**0.5
        if mag > self.speed:
            dx = dx / mag * self.speed
            dy = dy / mag * self.speed

        self.model.move_agent(self.agent, dx, dy)

    def move_towards(self, target_pos):
        dx = target_pos[0] - self.agent.pos[0]
        dy = target_pos[1] - self.agent.pos[1]
        self.move(dx, dy)

    def step_random(self):
        dx = self.agent.random.random() * self.speed * 2 - self.speed
        dy = self.agent.random.random() * self.speed * 2 - self.speed
        self.move(dx, dy)

    def step_spiral(self, separation=50, reset=False):
        if reset:
            self.spiral_r = None
        if not hasattr(self, "spiral_r"):
            self.spiral_r = self.speed
            self.spiral_phi = self.spiral_r / (separation / (2*math.pi))

        dx, dy = pol_to_cart(self.spiral_r, self.spiral_phi)
        self.move(dx, dy)
        self.spiral_phi += self.speed / self.spiral_r
        self.spiral_r = (separation / (2*math.pi)) * self.spiral_phi

    def step_circle(self, radius=100, reset=False):
        if reset:
            self.circle_phi = None
        if not hasattr(self, "circle_phi"):
            self.circle_phi = 0

        dx, dy = pol_to_cart(radius, self.circle_phi)
        self.move(dx, dy)
        self.circle_phi += self.speed / radius


class Radio():

    def __init__(self, agent, model, options):
        self.agent = agent
        self.model = model
        self.detection_thresh = options["detection_thresh"]
        self.connection_thresh = options["connection_thresh"]
        self.neighborhood = []

    def refresh(self):
        # Update the neighborhood from the model helper
        self.neighborhood = self.model.get_neighbors(self.agent)

    def is_connected(self, other):
        for agent in self.neighborhood:
            if agent["connected"]:
                if agent["id"] == other or other == "all":
                    return True
        return False

    def get_state(self):
        return {
            "detection_thresh": self.detection_thresh,
            "estimated_detection_range": self.model.get_distance(self.detection_thresh),
            "connection_thresh": self.connection_thresh,
            "estimated_connection_range": self.model.get_distance(self.connection_thresh),
            "neighborhood": makeSerializeable(self.neighborhood)
        }


class HDTN():
    # Skeleton for the HDTN peripheral

    # The recevie_bundle method is called by another agent
    # when in contact range

    def __init__(self, agent, model, options):
        self.agent = agent
        self.model = model
        self.options = options

    def receive_bundle(self, bundle, type="data"):
        # Receive a bundle from another agent
        # This function can be called by another agent in connection range
        print("Agent {} received bundle {}".format(
            self.agent.unique_id, bundle))

    def get_state(self):
        # Called by the agent and sent to the visualization and added to history
        return {
            # "has_data": self.has_data,
            # "current_target": self.current_target
        }

    def refresh(self):
        # Called every step by the agent
        pass
