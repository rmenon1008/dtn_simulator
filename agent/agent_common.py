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


def rssi_find_router_target(agent: mesa.Agent):
    target = agent.special_behavior["options"]["target_id"]

    # Check if connected to target
    if agent.radio.is_connected(target):
        agent.behavior["type"] = "fixed"

    # 1. Create a matrix with previous data
    positions = []
    rssis = []
    for h in agent.history:
        if "neighborhood" in h["radio"]:
            for n in h["radio"]["neighborhood"]:
                # if desired_target_agent_type is not None + n is not of desired_target_agent_type,
                # skip n.
                if n["id"] not in agent.model.router_agents.keys():
                    continue

                if n["id"] == target or target == "all":
                    positions.append(h["pos"])
                    rssis.append(n["rssi"])

    positions = np.array(positions[-100:])
    rssis = np.array(rssis[-100:])

    if len(positions) < 10:
        agent.movement.step_spiral()
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

    if agent.model.space.out_of_bounds((a, b)):
        agent.movement.step_spiral()
        return

    agent.movement.move_towards((a, b))