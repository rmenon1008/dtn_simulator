import os
import time

def main():
    all_scenario_ids = ['1a', '1b', '1c', '1d', '1e', '1f',
               '2a', '2b', '2c', '2d', '2e', '2f',
               '3a', '3b', '3c', '3d', '3e', '3f']
    
    for id in all_scenario_ids:
        cmd_str = "python simulations/run_single_experiment.py {} -b 10 -nv --log-metrics".format(id)
        print("Time is:\n\t{}".format(time.ctime()), flush=True)
        print("Executing:\n\t{}".format(cmd_str), flush=True)
        os.system(cmd_str)

if __name__ == "__main__":
    main()