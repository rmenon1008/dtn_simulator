from model import LunarModel
from lunar_vis import LunarVis
import mesa
import json
import argparse

from peripherals.movement import *

SIM_WIDTH = 1000  # 1 km
SIM_HEIGHT = 650  # 650 m

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

def main():
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-a", default="simulations/demo/agents_d1.json", help="path to json file with agent parameters")
    argParser.add_argument("-m", default="simulations/demo/model_d1.json", help="path to json file with model parameters")
    argParser.add_argument("-nv", default=False, action='store_true', help="run without web server that provides visualization")
    argParser.add_argument("--make-contact-plan", default=False, action='store_true', help="simulation tracks contacts between nodes and generates a contact plan")
    args = argParser.parse_args()
    
    init_agent_params = None
    init_model_params = None
    with open(args.a, "r") as init_json_file:
        init_agent_params = json.load(init_json_file)

    with open(args.m, "r") as init_json_file:
        init_model_params = json.load(init_json_file)

    model_params = ObjectOption(
        "Model parameters",
        value=init_model_params,
    )

    # Insert a new field into model parameters
    if (args.make_contact_plan):
        new_json = model_params.value
        new_json["make_contact_plan"] = True
        model_params.value = json.dumps(new_json)

    agent_state = ObjectOption(
        "Initial agent states",
        value=init_agent_params,
    )
    
    if args.nv:
        model = LunarModel(size=(SIM_WIDTH,SIM_HEIGHT), model_params=model_params.value, initial_state=agent_state.value)
        for i in range(model_params.value["max_steps"]):
            model.step()
        print("done")
        exit()

    # To run simulation with web server
    vis = LunarVis(SIM_WIDTH, SIM_HEIGHT)
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
    server.port = 8521  # The default port
    server.launch(open_browser=True)

if __name__ == "__main__":
    main()