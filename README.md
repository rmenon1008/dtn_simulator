# DCGR Simulation

## Running the simulation
1. Make sure the required Python modules are installed: `pip3 install numpy scipy mesa`
2. Run the visualization server: `python3 run_model_vis.py`
3. If it does not open automatically in a browser, go to `localhost:8521`

## CLI Options

```
-a                          used to provide path to json file containing initial agent states
-m                          used to provide path to json file containing model parameters
-rp                         choose routing protocol (0-dtn/cgr, 1-epidemic, 2-spray) [default=0]
-nv                         if present, simulator runs without web server visualization
--log-metrics               if present, logs metrics to file and prints summary statistics
--debug                     if present, run with debug print statements
--correctness               if present, run with expensive checks that verify some invariants
--make-contact-plan         used to generate a contact plan between RouterAgents within the simulator
                                (must have a max_step number in model params)

```