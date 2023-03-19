from model import LunarModel
from lunar_vis import LunarVis
import mesa

NUM_AGENTS = 1
SIM_WIDTH = 1000
SIM_HEIGHT = 500

vis = LunarVis(SIM_WIDTH, SIM_HEIGHT)
server = mesa.visualization.ModularServer(
    LunarModel,
    [vis],
    "Model",
    {
        "N": NUM_AGENTS,
        "width": SIM_WIDTH,
        "height": SIM_HEIGHT
    })
server.port = 8521 # The default
server.launch()
