from model import LunarModel
from lunar_vis import LunarVis
import mesa
import json

from peripherals.movement import *

# AGENT UNITS
# Agent top speed = 3.5 m/s (7.8 mph, max speed of the Lunar Roving Vehicle)
# 1 model pixel = 1 meter
# 1 tick = 1 second

SIM_WIDTH = 1000  # 1 km
SIM_HEIGHT = 650  # 650 m


# Model parameters defines model-wide constants
DEFAULT_MODEL_PARAMS = {
    # Max number of steps to run the model for (can be None)
    "max_steps": None,
    "rssi_noise_stdev": 4.5,    # Standard deviation of the noise added to RSSI values
    "model_speed_limit": 10,    # Maximum speed of any agent in the model
}

# Agent state defines the agents that will be created and their initial states
DEFAULT_AGENT_STATE = {

    # Agent defaults are deep-merged with every agent's options
    # If a key is provided in both, the value provided here is ignored
    "agent_defaults": {
        "radio": {
            "detection_thresh": -60,    # RSSI threshold for detecting another agent
            "connection_thresh": -25,   # RSSI threshold for connecting to another agent
        },
        "routing_protocol": {},
        "movement": {},
        "type": "router"  # can be a "router" or a "client".
    },

    # Agents is a list of agents that will be created by the model
    "agents": [
        # Agent 1:
        {
            "id": 0,                        # Unique id of the agent (optional, default is assigned by model)
            "radio": {
                "detection_thresh": -65,    # This agent is overriding the default detection
                                            # threshold for its radio
            },
            "movement": {
                "pattern": "fixed",         # Fixed movement pattern
                "speed": 0,                 # Speed of this agent in m/s
                "options": {
                    "pos": (SIM_WIDTH/2,
                            SIM_HEIGHT/2),  # The only option for "fixed" is the position
                }
            }
        },

        # Agent 2:
        {
            "movement": {
                "pattern": "spline",        # Spline movement pattern
                "speed": 2.5,               # Speed of this agent in m/s
                "options": {
                    "control_points": [     # Control points for the spline
                        (700, 150),         # The spline will pass through these points
                        (780, 500),
                        (690, 400),         # If the first and last points are the same,
                        (650, 450),         # the spline will be closed smoothly
                        (700, 320),
                        (700, 150),
                    ],
                    "repeat": True,         # Whether to repeat the pattern or just stop (opt, default True)
                    "bounce": False,        # If repeat is True, whether to retrace points
                                            # at the end or to start over from the beginning (opt, default False)
                }
            }
        },

        # Agent 3:
        {
            "movement": {
                "pattern": "waypoints",     # Waypoint movement pattern
                "speed": 3.5,               # Speed of this agent in m/s
                "options": {
                    "waypoints": [          # Waypoints for the agent to go between
                        (100, 100),
                        (100, 550),
                        (900, 550),
                        (900, 100),
                        (100, 100),
                    ],
                    "repeat": True,         # Whether to repeat the pattern or just stop (opt, default True)
                    "bounce": False,        # If repeat is True, whether to retrace points
                                            # at the end or to start over from the beginning (opt, default False)
                }
            }
        },

        # Agent 4:
        {
            "movement": {
                "pattern": "circle",        # Circle movement pattern
                "speed": 3.5,               # Speed of this agent in m/s
                "options": {
                    "radius": 100,          # Radius of the circle
                    "center": (300, 300),   # Center of the circle
                    "repeat": True,         # Whether to repeat the circle or just stop (opt, default True)
                }
            }
        },

        # Agent 5:
        {
            "special_behavior": {           # Agent special behavior (optional)
                "type": "find_node_rssi",   # This is the only special behavior implemented right now
                "options": {                # Options specific to this special behavior
                    "target_id": 0,         # The id of the agent to find
                }
            },
            "movement": {
                "pattern": "spiral",        # Random movement pattern
                "speed": 3.5,               # Speed of this agent in m/s
                "options": {
                    "center": (500, 100),   # Center of the spiral
                    "separation": 10,       # Distance between spiral arms
                }
            }
        },
        {
            "movement": {
                "pattern": "spiral",  # Random movement pattern
                "speed": 3.5,  # Speed of this agent in m/s
                "options": {
                    "center": (500, 100),  # Center of the spiral
                    "separation": 10,  # Distance between spiral arms
                }
            },
            "type": "client"  # set the agent type to be a ClientAgent.
        }
    ]
}

vis = LunarVis(SIM_WIDTH, SIM_HEIGHT)


class ObjectOption(mesa.visualization.UserParam):
    def __init__(self, name="", value=None, choices=None, description=None):
        self.param_type = "object"
        self.name = name
        self._value = json.dumps(value)

    @property
    def value(self):
        return json.loads(self._value)

    @value.setter
    def value(self, value):
        self._value = value


model_params = ObjectOption(
    "Model parameters",
    value=DEFAULT_MODEL_PARAMS,
)

agent_state = ObjectOption(
    "Initial agent states",
    value=DEFAULT_AGENT_STATE,
)

server = mesa.visualization.ModularServer(
    LunarModel,
    [vis],
    "Model",
    {
        "size": (SIM_WIDTH, SIM_HEIGHT),
        "model_params":  model_params,
        "initial_state": agent_state,
    })
server.settings["template_path"] = "visualization"
server.port = 8521  # The default
server.launch(open_browser=True)
