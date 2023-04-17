import math
import numpy as np
from scipy import interpolate


def pol_to_cart(r, phi):
    return (r * math.cos(phi), r * math.sin(phi))


class Movement():
    def __init__(self, agent, model, movement_options):
        self.agent = agent
        self.model = model
        self.pattern = generate_pattern(movement_options)
        self.max_speed = movement_options["speed"]

        self.target_pos = self.pattern.starting_pos

    def refresh(self):
        # This peripheral does not need to refresh because
        # it's state can not change based on the other nodes
        pass

    def move(self, dx, dy):
        mag = (dx**2 + dy**2)**0.5
        if mag > self.max_speed:
            dx = dx / mag * self.max_speed
            dy = dy / mag * self.max_speed

        self.model.move_agent(self.agent, dx, dy)

    def move_towards(self, target_pos):
        dx = target_pos[0] - self.agent.pos[0]
        dy = target_pos[1] - self.agent.pos[1]
        self.move(dx, dy)

    def is_close_to_point(self, pos, eps=0.01):
        pos2 = self.agent.pos
        return (pos[0] - pos2[0])**2 + (pos[1] - pos2[1])**2 < eps**2

    def step(self):
        if self.is_close_to_point(self.target_pos):
            self.target_pos = self.pattern.next()

        self.move_towards(self.target_pos)


class WaypointsPattern():
    def __init__(self, waypoints, start_index=0, forward=True, repeat=True, bounce=False):
        """
        waypoints: a list of (x, y) tuples
        start_index: the index of the waypoints to start at
        forward: whether to move forward or backward through the waypoints
        repeat: whether to stop after going through all the waypoints or to repeat
        bounce: whether to bounce in reverse at the end of the waypoints or to start over
        """
        # These stay constant
        self.waypoints = waypoints
        self.starting_pos = waypoints[start_index % len(waypoints)]

        # These may change each step
        self.index = start_index
        self.forward = forward
        self.repeat = repeat
        self.bounce = bounce

    def next(self):
        next_index = self.index
        # Advance the index
        if self.forward:
            next_index += 1
        else:
            next_index -= 1

        # Check if we need to bounce or repeat
        if next_index >= len(self.waypoints) or next_index < 0:
            if self.repeat:
                if self.bounce:
                    self.forward = not self.forward
                    if self.forward:
                        next_index = 1
                    else:
                        next_index = len(self.waypoints) - 2
                else:
                    next_index = 0
            else:
                next_index = self.index

        self.index = next_index
        return self.waypoints[self.index]


class SplinePattern(WaypointsPattern):
    OVERSAMPLING_AMOUNT = 50

    def __init__(self, control_points, start_index=0, forward=True, repeat=True, bounce=False, speed=1):
        # Generate the spline
        x = [p[0] for p in control_points]
        y = [p[1] for p in control_points]
        closed_loop = control_points[0] == control_points[-1]
        tck, u = interpolate.splprep([x, y], s=0, per=closed_loop)
        
        # Create the spline with way more points than we need
        # This oversampling number seemed to generate enough points
        approx_length = np.sum(np.sqrt(np.diff(x)**2 + np.diff(y)**2))
        n_points = int(approx_length * self.OVERSAMPLING_AMOUNT / speed)
        super_fine_t = np.linspace(0, 1, n_points)
        x, y = interpolate.splev(super_fine_t, tck, der=0)

        # Now we can sample the spline at a constant speed
        # We do this by finding the next point that is as far away as the desired speed
        waypoints = [(x[0], y[0])]
        for i in range(1, len(x)):
            dx = x[i] - waypoints[-1][0]
            dy = y[i] - waypoints[-1][1]
            dist = (dx**2 + dy**2)**0.5
            if dist >= speed:
                # Go back one point so we don't overshoot the speed
                waypoints.append((x[i-1], y[i-1]))

        super().__init__(waypoints, start_index, forward, repeat, bounce)


class CirclePattern(WaypointsPattern):
    def __init__(self, center, radius, start_index=0, clockwise=True, repeat=True, speed=1):
        waypoints = []
        n_waypoints = int(2 * math.pi * radius / speed) + 1
        for i in range(n_waypoints):
            phi = 2 * math.pi * i / n_waypoints
            if clockwise:
                phi = 2 * math.pi - phi
            dx, dy = pol_to_cart(radius, phi)
            waypoints.append((center[0] + dx, center[1] + dy))

        super().__init__(waypoints, start_index, clockwise, repeat)

class SpiralPattern(WaypointsPattern):
    def __init__(self, center, separation, speed=1):
        waypoints = [(center[0], center[1])]
        r = speed
        b = separation / (2 * math.pi)
        phi = float(r) / b
        while True:
            dx, dy = pol_to_cart(r, phi)
            waypoints.append((center[0] + dx, center[1] + dy))

            phi += float(speed) / r
            r = b * phi
            if r > 1000:
                break
        
        super().__init__(waypoints, 0, True, False)
        

class FixedPattern():
    def __init__(self, pos):
        self.starting_pos = pos

    def next(self):
        return self.starting_pos


def generate_pattern(movement_options):
    pattern = movement_options["pattern"]
    pattern_options = movement_options["options"]

    if pattern == "circle":
        return CirclePattern(**pattern_options, speed=movement_options["speed"])
    elif pattern == "spline":
        return SplinePattern(**pattern_options, speed=movement_options["speed"])
    elif pattern == "fixed":
        return FixedPattern(**pattern_options)
    elif pattern == "waypoints":
        return WaypointsPattern(**pattern_options)
    elif pattern == "spiral":
        return SpiralPattern(**pattern_options, speed=movement_options["speed"])
    else:
        raise Exception(f"Invalid pattern: {pattern}")
    

# class SplinePattern(WaypointPattern):
#     def __init__(self, controlPoints, speed, forward=True, repeat=True, bounce=False):
#         waypoints = []
