import os
import csv, operator
import argparse
import math


""" REFERENCE OUTPUT
============ Simulation Results (10 Trials) ============
Scenario 1
	Simulator: Roaming DTN
	Backbone Routing Protocol: CGR # THIS IS AN EXTRA LINE THAT EXISTS ONLY FOR ROAMING DTN
	Model File: ./simulations/scenario1/model_s1.json
	Agent File: ./simulations/scenario1/roamdtn_roaming_clients_s1.json
	RSSI Noise St. Deviation: 2 
	Model Speed Limit: 10 m/s 
	Max Steps: 10000 steps 
	Host Router Timeout: 2000 steps 
	Payload Lifespan: 5000 steps 
	Bundle Lifespan: 5000 steps 
Average payload delivery latency: 601.2080537632955 ticks (stdev=48.53555319840771)
Payload delivery success rate: 67.96296296296296% (stdev=4.236385169573701)
Average bundle storage overhead: 22.84955 (stdev=2.824532160376298)
"""

""" REFERENCE OUTPUT
============ Simulation Results (10 Trials) ============
Scenario 1
	Simulator: Spray-and-Wait
	Model File: ./simulations/scenario1/model_s1.json
	Agent File: ./simulations/scenario1/spray_and_wait_roaming_clients_s1.json
	RSSI Noise St. Deviation: 2 
	Model Speed Limit: 10 m/s 
	Max Steps: 10000 steps 
	Host Router Timeout: 2000 steps 
	Payload Lifespan: 5000 steps 
	Bundle Lifespan: 5000 steps 
Average payload delivery latency: 358.31182795698925 ticks (stdev=15.167878619715834)
Payload delivery success rate: 100.0% (stdev=0.0)
Average bundle storage overhead: 25.15813 (stdev=0.8880545817184385)
"""

NUM_TRIALS = 10

def get_scenario_id(file_path):
    """
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
    """
    outfile = open(file_path, "r")
    data = outfile.readlines()
    scenario_id = data[1].split(' ')[1].strip() #1, 2, or 3
    sim_type = data[2].split(' ')[1].strip() # Roaming, Epidemic, or Spray-and-Wait
    if sim_type == "Epidemic":
        is_stable_clients = "stable_clients" in data[4]
        if is_stable_clients:
            scenario_id += "c"
        else:
            scenario_id += "d"
    elif sim_type == "Spray-and-Wait":
        is_stable_clients = "stable_clients" in data[4]
        if is_stable_clients:
            scenario_id += "e"
        else:
            scenario_id += "f"
    elif sim_type == "Roaming":
        is_stable_clients = "stable_clients" in data[5]
        backbone = data[3].split(' ')[-1].strip() # remove newline char
        if backbone == "CGR":
            if is_stable_clients:
                scenario_id += "a"
            else:
                scenario_id += "b"
        elif backbone == "EPIDEMIC":
            if is_stable_clients:
                scenario_id += "g"
            else:
                scenario_id += "h"
        elif backbone == "SPRAY_AND_WAIT":
            if is_stable_clients:
                scenario_id += "i"
            else:
                scenario_id += "j"
        else:
            print("ERROR1")
            exit()
    else:
        print("ERROR2", sim_type)
        exit()

    print(file_path, "is", scenario_id)
    return scenario_id

# Returns (success rate, disk_burden, latency)
# Each of those are tuples of (mean, stderr)
def parse_data(file_path):
    outfile = open(file_path, "r")
    data = outfile.readlines()
    # Get latency
    latency_line = data[-3].split(' ')
    latency_mean = float(latency_line[-3])
    latency_stdev = float(latency_line[-1].split('=')[1].split(')')[0])
    latency_stderr = latency_stdev / math.sqrt(NUM_TRIALS)
    latency = (latency_mean, latency_stderr)
    # Get success rate
    success_rate_line = data[-2].split(' ')
    success_rate_mean = float(success_rate_line[-2].split('%')[0])
    success_rate_stdev = float(success_rate_line[-1].split('=')[1].split(')')[0])
    success_rate_stderr = success_rate_stdev / math.sqrt(NUM_TRIALS)
    success_rate = (success_rate_mean, success_rate_stderr)
    # Get disk burden
    disk_burden_line = data[-1].split(' ')
    disk_burden_mean = float(disk_burden_line[-2])
    disk_burden_stdev = float(disk_burden_line[-1].split('=')[1].split(')')[0])
    disk_burden_stderr = disk_burden_stdev / math.sqrt(NUM_TRIALS)
    disk_burden = (disk_burden_mean, disk_burden_stderr)
    
    return success_rate, disk_burden, latency

def main():
    argParser = argparse.ArgumentParser()
    argParser.add_argument("dir", help="")
    args = argParser.parse_args()
    dir_name = args.dir
    # field names 
    fields = ['scenario_id',
              'success_rate_mean', 'success_rate_stderr',
              'disk_burden_mean', 'disk_burden_stderr',
              'latency_mean', 'latency_stderr'] 
        
    # Get data
    data_list = []
    for filename in os.listdir(dir_name):
        f = os.path.join(dir_name, filename)
        if os.path.isfile(f) and f.endswith('.txt'):
            scenario_id = get_scenario_id(f)
            m0, m1, m2 = parse_data(f)
            data = [scenario_id, m0[0], m0[1], m1[0], m1[1], m2[0], m2[1]]
            data_list.append(data)

    # Sort by scenario_id
    data_list = sorted(data_list, key=operator.itemgetter(0))    
    
    # Write to CSV
    csv_out_file = "sim_analysis.csv"
    with open(csv_out_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)
        for data in data_list:
            csvwriter.writerow(data)

if __name__ == "__main__":
    main()