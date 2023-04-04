from model import LunarModel
from lunar_vis import LunarVis
import mesa

SIM_WIDTH = 1000
SIM_HEIGHT = 750

MODEL_PARAMS = {
    "size": (SIM_WIDTH, SIM_HEIGHT),
    "rssi_noise_stdev": 0.03
}

INITIAL_STATE = {
    "agent_defaults": {
        # If this is provided, all nodes will have
        # these options. It can be overridden by an
        # individual node's options.
        "radio": {
            "detection_range": 50,
            "connection_range": 20,
        }
    },
    "agents": [
        # The model will create an agent for each
        # node defined here. If "id" or "pos" are
        # not provided, they will be assigned
        # randomly.
        {
            "behavior": "mobile",
            # "pos": (10, 10),
            "hdtn": {
                "has_data": True,
                "current_target": 99
            },
            "radio": {
                "tx_power_dbm": 80,
            }
        },
        {
            "behavior": "fixed",
            "pos": (250, 250),
            "hdtn": {
                "has_data": False,
                "current_target": None
            },
        }
    ]
}


vis = LunarVis(SIM_WIDTH, SIM_HEIGHT)
# num_agents = mesa.visualization.UserSettableParameter('number', 'Agent count', value=1)
# radio_noise = mesa.visualization.UserSettableParameter('slider', 'RSSI noise stdev', value=0.03, min_value=0, max_value=0.50, step=0.01)
# radio_detection_range = mesa.visualization.UserSettableParameter('slider', 'Detection range', value=100, min_value=10, max_value=700, step=10)
# radio_connection_range = mesa.visualization.UserSettableParameter('slider', 'Connection range', value=15, min_value=10, max_value=200, step=10)
# move_spiral = mesa.visualization.UserSettableParameter('checkbox', 'Move in spiral', value=False)
# move_towards_target = mesa.visualization.UserSettableParameter('checkbox', 'Move towards target', value=False)
# center_static = mesa.visualization.UserSettableParameter('checkbox', 'Center static node', value=True)
# finish_on_transfer = mesa.visualization.UserSettableParameter('checkbox', 'Finish on data transfer', value=True)
server = mesa.visualization.ModularServer(
    LunarModel,
    [vis],
    "Model",
    {
        "model_params":  MODEL_PARAMS,
        "initial_state": INITIAL_STATE,
    })
server.settings["template_path"] = "visualization"
server.port = 8521 # The default
server.launch(open_browser=True)
