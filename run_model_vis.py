from model import LunarModel
from lunar_vis import LunarVis
import mesa
import json
import argparse
import time
import multiprocessing as mp
import os
from statistics import mean, stdev

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

# Run in Batches
def run_batches(num_trials, model_params, agent_state):
    #https://stackoverflow.com/questions/31711378/python-multiprocessing-how-to-know-to-use-pool-or-process
    output_q = mp.Queue()
    num_processes = num_trials
    processes = [mp.Process(target=get_trial_results, args=(i, output_q, model_params.value, agent_state.value, model_params.value["max_steps"])) for i in range(num_processes)]
    for p in processes:
        p.start()
    for p in processes:
        p.join()
    # Process results
    # list of n 3-tuples [(m0, m1, m2), (m0, m1, m2)]
    results = [output_q.get() for _ in processes]
    # list of 3 n-tuples [(m0, m0, m0, ...), (m1, m1, ...), (m2, m2, ...)]
    result_unzipped = list(zip(*results))
    avg_latencies = list(result_unzipped[0])
    avg_payload_rates = list(result_unzipped[1])
    avg_bundles_stored = list(result_unzipped[2])
    routing_protocol = str(RoutingProtocol(model_params.value["backbone_routing_protocol"])).split('.')[1]
    print_sim_results(model_params.value["title"], model_params.value["scenario_name"], routing_protocol,
                      num_processes,
                      (mean(avg_latencies), stdev(avg_latencies)),
                      (mean(avg_payload_rates), stdev(avg_payload_rates)),
                      (mean(avg_bundles_stored), stdev(avg_bundles_stored)))

def get_trial_results(trial_num, output_q, model_params, initial_state, max_steps):
    model = LunarModel(size=(SIM_WIDTH,SIM_HEIGHT), model_params=model_params, initial_state=initial_state)
    for i in range(max_steps):
        if i % (max_steps / 10) == 0:
            print("\t Trial {}: {}/{} steps, {}% done".format(trial_num, i, max_steps, 100 * i / max_steps), flush=True)
        model.step()
    output_tuple = (model.avg_latency, model.payload_rate, model.avg_storage_overhead)
    output_q.put(output_tuple)

def print_sim_results(title, scenario_name, routing_protocol, num_trials, m0, m1, m2):
    if not os.path.exists("out"):
        # Create a new directory because it does not exist
        os.makedirs("out")
    file_name = "out/" + scenario_name.replace(" ", "_") + "_" + routing_protocol + "_" + time.ctime().replace(" ", "_").replace(":", "_") + ".txt"
    def log_and_print(str):
        with open(file_name, "a") as outfile:
            if "\n" in str:
                outfile.write(str)
            else:
                outfile.write(str + "\n")
        print(str, flush=True)
    log_and_print("============ Simulation Results ({} Trials) ============".format(num_trials))
    log_and_print(title)
    log_and_print("Average payload delivery latency: {} ticks (stdev={})".format(m0[0], m0[1]))
    log_and_print("Payload delivery success rate: {}% (stdev={})".format(m1[0], m1[1]))
    log_and_print("Average bundle storage overhead: {} (stdev={})".format(m2[0], m2[1]))

# No Web Server, CLI only
def run_cli_only(model_params, agent_state):
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
    if "log_metrics" in model_params.value:
        print_stats_for_one_trial(model_params.value["title"], model.avg_latency, model.payload_rate, model.avg_storage_overhead)

def print_stats_for_one_trial(title, m0, m1, m2):
    print("============ Simulation Results ============", flush=True)
    print(title, flush=True)
    print("Average payload delivery latency: {} ticks".format(m0), flush=True)
    print("Payload delivery success rate: {}%".format(m1), flush=True)
    print("Average bundle storage overhead: {}".format(m2), flush=True)

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
        })
    server.settings["template_path"] = "visualization"
    server.port = 8521  # The default port
    server.launch(open_browser=True)

# Main
def main():
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-a", default="simulations/demo/agents_d1.json", help="path to json file with agent parameters")
    argParser.add_argument("-m", default="simulations/demo/model_d1.json", help="path to json file with model parameters")
    argParser.add_argument("-rp", default=0, help="choose backbone routing protocol for Roaming DTN (0-cgr, 1-epidemic, 2-spray) [default=0]")
    argParser.add_argument("-nv", default=False, action='store_true', help="run without web server that provides visualization")
    argParser.add_argument("-b", default=0, help="run n batches")
    argParser.add_argument("--correctness", default=False, action='store_true', help="run with expensive checks to verify invariants")
    argParser.add_argument("--debug", default=False, action='store_true', help="run with debug print statements")
    argParser.add_argument("--log-metrics", default=False, action='store_true', help="path to file to log metrics in")
    argParser.add_argument("--make-contact-plan", help="Make contact plan for connections between... [0-routers-only, 1-all nodes]")
    args = argParser.parse_args()

    # Get agent parameters
    init_agent_params = None
    init_model_params = None
    with open(args.a, "r") as init_json_file:
        init_agent_params = json.load(init_json_file)

    agent_state = ObjectOption(
        "Initial agent states",
        value=init_agent_params,
    )

    # Get model parameters
    with open(args.m, "r") as init_json_file:
        init_model_params = json.load(init_json_file)

    model_params = ObjectOption(
        "Model parameters",
        value=init_model_params,
    )

    # Insert new fields into model parameters
    new_json = model_params.value
    new_json["model_filepath"] = args.m
    model_params.value = json.dumps(new_json)

    new_json = model_params.value
    new_json["agent_filepath"] = args.a
    model_params.value = json.dumps(new_json)

    if args.debug:
        new_json = model_params.value
        new_json["debug"] = True
        model_params.value = json.dumps(new_json)

    if args.make_contact_plan:
        new_json = model_params.value
        new_json["make_contact_plan"] = args.make_contact_plan
        model_params.value = json.dumps(new_json)

    if args.log_metrics or int(args.b) > 0:
        new_json = model_params.value
        new_json["log_metrics"] = True
        model_params.value = json.dumps(new_json)

    if args.correctness:
        new_json = model_params.value
        new_json["correctness"] = True
        model_params.value = json.dumps(new_json)
    
    # Loop through agents to figure out which type of sim this is
    #   could be (0-Roaming DTN, 1-Epidemic, or 2-Spray-and-Wait)
    sim_type = 0
    for agent_options in agent_state.value["agents"]:
        if agent_options["type"] == "router" or agent_options["type"] == "client":
            sim_type = 0
            new_json = model_params.value
            new_json["backbone_routing_protocol"] = int(args.rp)
            model_params.value = json.dumps(new_json)
            break
        elif agent_options["type"] == "epidemic":
            sim_type = 1
            break
        elif agent_options["type"] == "spray":
            sim_type = 2
            break
        else:
            print("error")
    new_json = model_params.value
    new_json["sim_type"] = sim_type
    model_params.value = json.dumps(new_json)

    # Create a concise summary of what this sim is going to do
    title = model_params.value["scenario_name"] + "\n"
    if sim_type == 0:
        title += "\tSimulator: Roaming DTN\n"
        title += "\tBackbone Routing Protocol: {}\n".format(str(RoutingProtocol(model_params.value["backbone_routing_protocol"])).split('.')[1])
    elif sim_type == 1:
        title += "\tSimulator: Epidemic\n"
    elif sim_type == 2:
        title += "\tSimulator: Spray-and-Wait\n"
    title += "\tModel File: {}\n".format(model_params.value["model_filepath"])
    title += "\tAgent File: {}\n".format(model_params.value["agent_filepath"])
    title += "\tRSSI Noise St. Deviation: {} \n".format(model_params.value["rssi_noise_stdev"])
    title += "\tModel Speed Limit: {} m/s \n".format(model_params.value["model_speed_limit"])
    title += "\tMax Steps: {} steps \n".format(model_params.value["max_steps"])
    title += "\tHost Router Timeout: {} steps \n".format(model_params.value["host_router_mapping_timeout"])
    title += "\tPayload Lifespan: {} steps \n".format(model_params.value["payload_lifespan"])
    title += "\tBundle Lifespan: {} steps \n".format(model_params.value["bundle_lifespan"])
    new_json = model_params.value
    new_json["title"] = title
    model_params.value = json.dumps(new_json)

    # Run model
    print(title, flush=True)
    if int(args.b) > 0:
        run_batches(int(args.b), model_params, agent_state)
    elif args.nv:
        run_cli_only(model_params, agent_state)
    else:
        run_web_server(model_params, agent_state)

if __name__ == "__main__":
    main()
