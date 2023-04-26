from model import LunarModel
from lunar_vis import LunarVis
import mesa
import json
import argparse
import time
import multiprocessing as mp
import os

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

def get_trial_results(output_q, model_params, initial_state, max_steps):
    model = LunarModel(size=(SIM_WIDTH,SIM_HEIGHT), model_params=model_params, initial_state=initial_state)
    for i in range(max_steps):
        if i % (max_steps / 10) == 0:
            print("\t step {} out of {}".format(i, max_steps), flush=True)
        model.step()
    model.datacollector.collect(model)
    final_stuff = model.datacollector.get_model_vars_dataframe()
    output_df_row_values = final_stuff.head().values[0]
    output_tuple = (output_df_row_values[0], output_df_row_values[1], output_df_row_values[2])
    print(output_tuple)
    output_q.put(output_tuple)

def print_sim_results(title, num_trials, m0, m1, m2):
    if not os.path.exists("out"):
        # Create a new directory because it does not exist
        os.makedirs("out")
    file_name = "out/summary_" + time.ctime().replace(" ", "_").replace(":", "_") + ".txt"
    def log_and_print(str):
        with open(file_name, "a") as outfile:
            if "\n" in str:
                outfile.write(str)
            else:
                outfile.write(str + "\n")
        print(str, flush=True)
    print("============ Simulation Results ({} Trials) ============".format(num_trials), flush=True)
    print(title, flush=True)
    print("Average payload delivery latency: {} ticks".format(m0), flush=True)
    print("Payload delivery success rate: {}%".format(m1), flush=True)
    print("Average bundle storage overhead: {}".format(m2), flush=True)
    
def main():
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-a", default="simulations/demo/agents_d1.json", help="path to json file with agent parameters")
    argParser.add_argument("-m", default="simulations/demo/model_d1.json", help="path to json file with model parameters")
    argParser.add_argument("-rp", default=0, help="choose routing protocol (0-cgr, 1-epidemic, 2-spray) [default=0]")
    argParser.add_argument("-nv", default=False, action='store_true', help="run without web server that provides visualization")
    argParser.add_argument("-b", default=0, help="run n batches")
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
    
    title = model_params.value["title"] + "\n"
    title += "\tRouting Protocol: {}\n".format(str(RoutingProtocol(model_params.value["routing_protocol"])))
    title += "\tMax Steps: {} steps \n".format(model_params.value["max_steps"])
    title += "\tRSSI Noise STDEV: {} \n".format(model_params.value["rssi_noise_stdev"])
    title += "\tModel Speed Limit: {} m/s \n".format(model_params.value["model_speed_limit"])
    title += "\tHost Router Timeout: {} steps \n".format(model_params.value["host_router_mapping_timeout"])
    title += "\tPayload Lifespan: {} steps \n".format(model_params.value["payload_lifespan"])
    title += "\tBundle Lifespan: {} steps \n".format(model_params.value["bundle_lifespan"])
    new_json = model_params.value
    new_json["title"] = args.correctness
    model_params.value = json.dumps(new_json)

    agent_state = ObjectOption(
        "Initial agent states",
        value=init_agent_params,
    )
    print("Routing protocol for this simulation is: ", RoutingProtocol(model_params.value["routing_protocol"]), flush=True)
    if int(args.b) > 0:
        #https://stackoverflow.com/questions/31711378/python-multiprocessing-how-to-know-to-use-pool-or-process
        output_q = mp.Queue()
        num_processes = int(args.b)
        processes = [mp.Process(target=get_trial_results, args=(output_q, model_params.value, agent_state.value, model_params.value["max_steps"])) for x in range(num_processes)]
        for p in processes:
            p.start()
        for p in processes:
            p.join()
        # Process results
        results = [output_q.get() for p in processes]
        print(results)
        avg_avg_latency = 0
        avg_payload_rate = 0
        avg_avg_storage_overhead = 0
        for res in results:
            if res[0] is not None:
                avg_avg_latency += res[0]
            else:
                avg_avg_latency += 0
            if res[1] is not None:
                avg_payload_rate += res[1]
            else:
                avg_payload_rate += 0
            avg_avg_storage_overhead += res[2]
        avg_avg_latency /= num_processes
        avg_payload_rate /= num_processes
        avg_avg_storage_overhead /= num_processes
        print_sim_results(title, num_processes, avg_avg_latency, avg_payload_rate, avg_avg_storage_overhead)
        exit()

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