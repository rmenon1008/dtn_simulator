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
    elif letter == "g":
        agent_path += "roamdtn_stable_clients_s{}.json".format(num)
        agent_path += " -rp 1 " # for Epidemic Backbone
    elif letter == "h":
        agent_path += "roamdtn_roaming_clients_s{}.json".format(num)
        agent_path += " -rp 1 " # for Epidemic Backbone
    elif letter == "i":
        agent_path += "roamdtn_stable_clients_s{}.json".format(num)
        agent_path += " -rp 2 " # for Spray and Wait Backbone
    elif letter == "j":
        agent_path += "roamdtn_roaming_clients_s{}.json".format(num)
        agent_path += " -rp 2 " # for Spray and Wait Backbone
    return model_path, agent_path

def get_cmd_str():
    argParser = argparse.ArgumentParser()
    argParser.add_argument("s", help="")
    argParser.add_argument("-rp", default=False, help="see run_model_vis.py")
    argParser.add_argument("-nv", default=False, action='store_true', help="see run_model_vis.py")
    argParser.add_argument("-b", default=False, help="see run_model_vis.py")
    argParser.add_argument("--correctness", default=False, action='store_true', help="see run_model_vis.py")
    argParser.add_argument("--debug", default=False, action='store_true', help="see run_model_vis.py")
    argParser.add_argument("--log-metrics", default=False, action='store_true', help="see run_model_vis.py")
    argParser.add_argument("--make-contact-plan", help="see run_model_vis.py")
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
        cmd_str += "--make-contact-plan {}".format(args.make_contact_plan)
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
        \t1g) Roaming DTN w/ stable clients (Epidemic Backbone)
        \t1h) Roaming DTN w/ roaming clients (Epidemic Backbone)
        \t1i) Roaming DTN w/ stable clients (Spray and Wait Backbone)
        \t1j) Roaming DTN w/ roaming clients (Spray and Wait Backbone)

        Scenario 2:
        \t2a) Roaming DTN w/ stable clients
        \t2b) Roaming DTN w/ roaming clients
        \t2c) Epidemic w/ stable clients
        \t2d) Epidemic w/ roaming clients
        \t2e) Spray-and-Wait w/ stable clients
        \t2f) Spray-and-Wait w/ roaming clients
        \t2g) Roaming DTN w/ stable clients (Epidemic Backbone)
        \t2h) Roaming DTN w/ roaming clients (Epidemic Backbone)
        \t2i) Roaming DTN w/ stable clients (Spray and Wait Backbone)
        \t2j) Roaming DTN w/ roaming clients (Spray and Wait Backbone)

        Scenario 3:
        \t3a) Roaming DTN w/ stable clients
        \t3b) Roaming DTN w/ roaming clients
        \t3c) Epidemic w/ stable clients
        \t3d) Epidemic w/ roaming clients
        \t3e) Spray-and-Wait w/ stable clients
        \t3f) Spray-and-Wait w/ roaming clients
        \t3g) Roaming DTN w/ stable clients (Epidemic Backbone)
        \t3h) Roaming DTN w/ roaming clients (Epidemic Backbone)
        \t3i) Roaming DTN w/ stable clients (Spray and Wait Backbone)
        \t3j) Roaming DTN w/ roaming clients (Spray and Wait Backbone)
        """
    if len(sys.argv)==1:
        print(options_str)
        sys.exit(1)
    cmd_str = get_cmd_str()
    os.system(cmd_str)

if __name__ == "__main__":
    main()