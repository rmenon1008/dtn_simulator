import os
import argparse
import sys

def get_paths_for_scenario(scenario_id):
    num = scenario_id[0]
    letter = scenario_id[1]
    scenario_folder_path = "./simulations/scenario{0}/".format(num)
    model_path = scenario_folder_path + "model_s{0}.json".format(num)
    agent_path = scenario_folder_path
    if letter == "a":
        agent_path += "roamdtn_stable_clients_s{}.json".format(num)
    elif letter == "b":
        agent_path += "roamdtn_roaming_clients_s{}.json".format(num)
    elif letter == "c":
        agent_path += "epidemic_stable_clients_s{}.json".format(num)
    elif letter == "d":
        agent_path += "epidemic_roaming_clients_s{}.json".format(num)
    elif letter == "e":
        agent_path += "spray_and_wait_stable_clients_s{}.json".format(num)
    elif letter == "f":
        agent_path += "spray_and_wait_roaming_clients_s{}.json".format(num)
    return model_path, agent_path

def get_cmd_str():
    argParser = argparse.ArgumentParser()
    argParser.add_argument("s", help="")
    argParser.add_argument("-rp", default=False, help="choose backbone routing protocol (0-cgr, 1-epidemic, 2-spray) [default=0]")
    argParser.add_argument("-nv", default=False, action='store_true', help="run without web server that provides visualization")
    argParser.add_argument("-b", default=False, help="run n batches")
    argParser.add_argument("--correctness", default=False, action='store_true', help="run with expensive checks to verify invariants")
    argParser.add_argument("--debug", default=False, action='store_true', help="run with debug print statements")
    argParser.add_argument("--log-metrics", default=False, action='store_true', help="path to file to log metrics in")
    argParser.add_argument("--make-contact-plan", default=False, action='store_true', help="simulation tracks contacts between nodes and generates a contact plan")
    argParser.add_argument("--dry-run", default=False, action='store_true', help="don't execute the command")
    args = argParser.parse_args()
    model_path, agent_path = get_paths_for_scenario(args.s)
    cmd_str = "python run_model_vis.py -m {} -a {} ".format(model_path, agent_path)
    if args.rp:
        cmd_str += "-rp {} ".format(args.rp)
    if args.nv:
        cmd_str += "-nv "
    if args.b:
        cmd_str += "-b {} ".format(int(args.b))
    if args.correctness:
        cmd_str += "--correctness "
    if args.log_metrics:
        cmd_str += "--log-metrics "
    if args.make_contact_plan:
        cmd_str += "--make-contact-plan "
    print("Executing:\n\t{}".format(cmd_str), flush=True)
    if args.dry_run:
        exit()
    return cmd_str

def main():
    options_str = \
        """Must run with scenario id:
$ python simulations/run_experiments.py [2-letter scenario id]
        Scenario 1:
        \t1a) Roaming DTN w/ stable clients
        \t1b) Roaming DTN w/ roaming clients
        \t1c) Epidemic w/ stable clients
        \t1d) Epidemic w/ roaming clients
        \t1e) Spray-and-Wait w/ stable clients
        \t1f) Spray-and-Wait w/ roaming clients

        Scenario 2:
        \t2a) Roaming DTN w/ stable clients
        \t2b) Roaming DTN w/ roaming clients
        \t2c) Epidemic w/ stable clients
        \t2d) Epidemic w/ roaming clients
        \t2e) Spray-and-Wait w/ stable clients
        \t2f) Spray-and-Wait w/ roaming clients

        Scenario 2:
        \t3a) Roaming DTN w/ stable clients
        \t3b) Roaming DTN w/ roaming clients
        \t3c) Epidemic w/ stable clients
        \t3d) Epidemic w/ roaming clients
        \t3e) Spray-and-Wait w/ stable clients
        \t3f) Spray-and-Wait w/ roaming clients
        """
    if len(sys.argv)==1:
        print(options_str)
        sys.exit(1)
    cmd_str = get_cmd_str()
    os.system(cmd_str)

if __name__ == "__main__":
    main()