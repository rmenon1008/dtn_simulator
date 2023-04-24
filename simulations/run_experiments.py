import os
import argparse


def main():
    argParser = argparse.ArgumentParser()
    argParser.add_argument("scenario_id", help="scenario id")
    argParser.add_argument("--clients-are-roaming", default=False, action='store_true', help="if present, clients roam around instead of staying in one region of the map")
    args = argParser.parse_args()

    cmd_str = "python run_model_vis.py "

    agent_arg = "-a "
    if args.clients_are_roaming:
        agent_arg += "./simulations/scenario{0}/agents_roaming_clients_s{0}.json ".format(args.scenario_id)
    else:
        agent_arg += "./simulations/scenario{0}/agents_stable_clients_s{0}.json ".format(args.scenario_id)

    model_arg = "-m "
    model_arg += "./simulations/scenario{0}/model_s{0}.json ".format(args.scenario_id)

    cmd_str += agent_arg + model_arg
    print("executing:\n\t{}".format(cmd_str))
    os.system(cmd_str)

if __name__ == "__main__":
    main()