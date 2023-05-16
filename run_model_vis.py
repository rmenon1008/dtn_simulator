from model import LunarModel
from lunar_vis import LunarVis
import mesa
import json
import argparse
import time
import multiprocessing as mp
import os
from statistics import mean, stdev

# SIM_WIDTH = 1000  # 1 km
# SIM_HEIGHT = 650  # 650 m
SIM_WIDTH = 3490
SIM_HEIGHT = 1550

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

# Web Server
def run_web_server(model_params, agent_state):
    vis = LunarVis(SIM_WIDTH, SIM_HEIGHT)
    server = mesa.visualization.ModularServer(
        LunarModel,
        [vis],
        "Model",
        {
            "size": (SIM_WIDTH, SIM_HEIGHT),
            "model_params":  model_params,
            "initial_state": agent_state,

            # @Isaac, @Lyla, @Andrew: Pass more parameters here like the object and radio maps.

        })
    server.settings["template_path"] = "visualization"
    server.port = 8521  # The default port
    server.launch(open_browser=True)

# Main
def main():
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-a", default="experiments/simple/agents.json", help="path to json file with agent parameters")
    argParser.add_argument("-m", default="experiments/simple/model.json", help="path to json file with model parameters")

    # @Isaac, @Lyla, @Andrew: This is where you could provide the path to the object and radio maps.

    args = argParser.parse_args()

    # Get agent parameters and put into the viz JSON editor
    init_agent_params = None
    with open(args.a, "r") as init_json_file:
        init_agent_params = json.load(init_json_file)
    agent_state = ObjectOption(
        "Initial agent states",
        value=init_agent_params,
    )

    # Get model parameters and put into the viz JSON editor
    init_model_params = None
    with open(args.m, "r") as init_json_file:
        init_model_params = json.load(init_json_file)
    model_params = ObjectOption(
        "Model parameters",
        value=init_model_params,
    )

    # @Isaac, @Lyla, @Andrew: Things here will only get run once when the server is
    # started It's a good spot for pre-processing the object and radio maps if it's
    # needed.
    #
    # Not sure whether it makes more sense to do those steps beforehand, like in a
    # notebook, or within the model itself here. Maybe worth discussing.

    # Run the model
    run_web_server(model_params, agent_state)

if __name__ == "__main__":
    main()
