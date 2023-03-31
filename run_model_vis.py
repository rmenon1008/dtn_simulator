from model import LunarModel
from lunar_vis import LunarVis
import mesa

SIM_WIDTH = 1000
SIM_HEIGHT = 750

vis = LunarVis(SIM_WIDTH, SIM_HEIGHT)
num_agents = mesa.visualization.UserSettableParameter('number', 'Agent count', value=1)
radio_noise = mesa.visualization.UserSettableParameter('slider', 'RSSI noise stdev', value=0.03, min_value=0, max_value=0.50, step=0.01)
radio_detection_range = mesa.visualization.UserSettableParameter('slider', 'Detection range', value=100, min_value=10, max_value=700, step=10)
radio_connection_range = mesa.visualization.UserSettableParameter('slider', 'Connection range', value=15, min_value=10, max_value=200, step=10)
move_spiral = mesa.visualization.UserSettableParameter('checkbox', 'Move in spiral', value=False)
move_towards_target = mesa.visualization.UserSettableParameter('checkbox', 'Move towards target', value=False)
center_static = mesa.visualization.UserSettableParameter('checkbox', 'Center static node', value=True)
finish_on_transfer = mesa.visualization.UserSettableParameter('checkbox', 'Finish on data transfer', value=True)
server = mesa.visualization.ModularServer(
    LunarModel,
    [vis],
    "Model",
    {
        "N": num_agents,
        "width": SIM_WIDTH,
        "height": SIM_HEIGHT,
        "radio_noise": radio_noise,
        "radio_detection_range": radio_detection_range,
        "radio_connection_range": radio_connection_range,
        "move_spiral": move_spiral,
        "move_towards_target": move_towards_target,
        "center_static": center_static,
        "finish_on_transfer": finish_on_transfer
    })
server.settings["template_path"] = "visualization"
server.port = 8521 # The default
server.launch(open_browser=True)
