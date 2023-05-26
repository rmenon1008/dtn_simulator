"""
Stores content shared across agent classes + files.
"""
import mesa
import numpy as np
from scipy.optimize import leastsq

def try_getting(obj, *keys, default=None):
    """Helper that tries to get a value from a nested dict."""
    for key in keys:
        if key in obj:
            obj = obj[key]
        else:
            return default
    return obj

def least_squares_convergence(agent: mesa.Agent):
    # @Alex @Andrew: This is how we converge on another agents right now.
    #                It uses the agent's historical RSSI to another agent
    #                to find the best fit for where the target might be.

    # If no target is specified, set it to "all"
    target = try_getting(agent.special_behavior, "target", default="all")

    # Check if connected to target
    if agent.radio.is_connected(target):
        agent.special_behavior["type"] = None
        agent.movement.stop()

    # 1. Create a matrix with previous data
    positions = []
    rssis = []
    for h in agent.history:
        if "neighborhood" in h["radio"]:
            for n in h["radio"]["neighborhood"]:
                if n["id"] == target or target == "all":
                    positions.append(h["pos"])
                    rssis.append(n["rssi"])

    positions = np.array(positions[-30:])
    rssis = np.array(rssis[-30:])

    if len(positions) < 10:
        agent.movement.step()
        return

    # 2. Assume RSSI is approximately of the form
    #    best_rssi = 10 * 2.5 * log10(1/((x-a)^2 + (y-b)^2)**0.5)
    #    where (a, b) is the position of the target
    def rssi_model(x, y, a, b, c):
        return 10 * c * np.log10(1 / ((a - x) ** 2 + (b - y) ** 2) ** 0.5)

    def rssi_error(params):
        a, b, c = params
        return rssis - rssi_model(positions[:, 0], positions[:, 1], a, b, c)

    # 3. Find the best fit for a potential target
    a, b, c = leastsq(rssi_error, (0, 0, 0))[0]

    agent.movement.target_pos = (a, b)

    if agent.model.space.out_of_bounds((a, b)):
        agent.movement.step()
        return

    agent.movement.move_towards((a, b))