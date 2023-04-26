from model import LunarModel
from lunar_vis import LunarVis
import mesa
import json
import argparse
import time

from peripherals.movement import *
from agent.router_agent import RoutingProtocol

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
    argParser.add_argument("-rp", default=0, help="choose routing protocol (0-dtn/cgr, 1-epidemic, 2-spray) [default=0]")
    argParser.add_argument("-nv", default=False, action='store_true', help="run without web server that provides visualization")
    argParser.add_argument("--correctness", default=False, action='store_true', help="run with expensive checks to verify invariants")
    argParser.add_argument("--debug", default=False, action='store_true', help="run with debug print statements")
    argParser.add_argument("--log-metrics", default=False, action='store_true', help="path to file to log metrics in")
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
    if args.debug:
        new_json = model_params.value
        new_json["debug"] = True
        model_params.value = json.dumps(new_json)

    if args.make_contact_plan:
        new_json = model_params.value
        new_json["make_contact_plan"] = True
        model_params.value = json.dumps(new_json)

    if args.log_metrics:
        new_json = model_params.value
        new_json["log_metrics"] = True
        model_params.value = json.dumps(new_json)

    # Set routing_protocol param, default = 0
    new_json = model_params.value
    new_json["routing_protocol"] = int(args.rp)
    model_params.value = json.dumps(new_json)

    new_json = model_params.value
    new_json["correctness"] = args.correctness
    model_params.value = json.dumps(new_json)

    agent_state = ObjectOption(
        "Initial agent states",
        value=init_agent_params,
    )
    print("Routing protocol for this simulation is: ", RoutingProtocol(model_params.value["routing_protocol"]), flush=True)
    if args.nv:
        print("\nStarting simulation at {}\n".format(time.ctime()), flush=True)
        start_time = time.time()
        model = LunarModel(size=(SIM_WIDTH,SIM_HEIGHT), model_params=model_params.value, initial_state=agent_state.value)
        max_steps = model_params.value["max_steps"]
        for i in range(max_steps):
            if i % (max_steps / 10) == 0:
                print("\t step {} out of {}".format(i, max_steps), flush=True)
            model.step()
        elapsed_time = time.time() - start_time
        print("\n\nSimulation took {} s to run".format(elapsed_time), flush=True)
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