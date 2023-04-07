import math


def pol_to_cart(r, phi):
    return (r * math.cos(phi), r * math.sin(phi))


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
