import mesa
from model import LunarModel

SIM_WIDTH = 1000
SIM_HEIGHT = 750

num_agents = 1
radio_noise = 0.03
radio_detection_range = 700
radio_connection_range = 20
center_static = True

params = {
    "N": num_agents,
    "width": SIM_WIDTH,
    "height": SIM_HEIGHT,
    "radio_noise": radio_noise,
    "radio_detection_range": radio_detection_range,
    "radio_connection_range": radio_connection_range,
    "center_static": center_static
}

mesa.batch_run(LunarModel, params, 1)
