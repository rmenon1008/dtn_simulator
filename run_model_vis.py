from model import LunarModel
from lunar_vis import LunarVis
import mesa
import json

# AGENT UNITS
# Agent top speed = 3.5 m/s (7.8 mph, max speed of the Lunar Roving Vehicle)
# 1 model pixel = 1 meter
# 1 tick = 1 second

SIM_WIDTH = 1000  # 1 km
SIM_HEIGHT = 650  # 650 m

DEFAULT_MODEL_PARAMS = {
    "max_steps": None,
    "rssi_noise_stdev": 4.5,
    "model_speed_limit": 3.0,
}

DEFAULT_INITIAL_STATE = {
    "agent_defaults": {
        # If this is provided, all nodes will have
        # these options. It can be overridden by an
        # individual node's options.
        "radio": {
            "detection_thresh": -60,
            "connection_thresh": -25,
        },
        "dtn": {},
        "movement": {}
    },
    "agents": [
        # The model will create an agent for each
        # node defined here. If "id" or "pos" are
        # not provided, they will be assigned
        # randomly.
        {
            "id": 0,
            "behavior": {
                "type": "fixed",
            },
            "pos": (SIM_WIDTH/2, SIM_HEIGHT/2),
            "dtn": {},
        },
        {
            "behavior": {
                "type": "rssi_find_target",
                "options": {
                    "target_id": 0,
                },
            },
            "radio": {},
        },
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

initial_state = ObjectOption(
    "Initial agent states",
    value=DEFAULT_INITIAL_STATE,
)

server = mesa.visualization.ModularServer(
    LunarModel,
    [vis],
    "Model",
    {
        "size": (SIM_WIDTH, SIM_HEIGHT),
        "model_params":  model_params,
        "initial_state": initial_state,
    })
server.settings["template_path"] = "visualization"
server.port = 8521  # The default
server.launch(open_browser=True)
