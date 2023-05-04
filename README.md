# DTN Simulator

## Running the simulation
1. Make sure the required Python modules are installed: `pip3 install numpy scipy mesa pytest`
2. Run the visualization server: `python3 run_model_vis.py`
3. If it does not open automatically in a browser, go to `localhost:8521`

## CLI Options

```
-a [path]                   used to provide path to json file containing initial agent states
-m [path]                   used to provide path to json file containing model parameters
-rp [0, 1, or 2]            choose routing protocol (0-cgr, 1-epidemic, 2-spray) [default=0]
-b [n > 0]                  run batch of n trials and report statistics
-nv                         if present, simulator runs without web server visualization
--log-metrics               if present, logs metrics to file and prints summary statistics
--debug                     if present, run with debug print statements
--correctness               if present, run with expensive checks that verify some invariants
--make-contact-plan         used to generate a contact plan between RouterAgents within the simulator
                                (must have a max_step number in model params)
```
## Running the simulation using real rssi data

The original get_rssi function has been commented out as to switch between simulated vs experimental values easily

```
python3 run_model_vis.py -i 'experiments/rssi_scenario/rssi_scenario.json' -m 'experiments/rssi_scenario/rssi_scenario_modelparams.json'

```

### Experimental RSSI Interpolation used for simulation 

Under the rssi directory, the rssi data is interpolated in a jupyter notebook

