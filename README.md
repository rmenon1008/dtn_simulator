# DTN Simulator · rss_dev branch
This branch is a greatly simplified version of the main branch. It has far fewer features, hopefully making it easier to quickly develop a better simulated radio environment, physical objects, and incorporate real RSSI data.

There are places in the code where I left comments about where those different pieces might fit, but feel free to modify the simulation however works best.


## Running the simulation
1. Make sure the required Python modules are installed: `pip3 install numpy scipy mesa pytest`
2. Run the visualization server: `python3 run_model_vis.py`
3. If it does not open automatically in a browser, go to `localhost:8521`


## Simulation Parameters
Use the `experiments` folder to create new configurations for the simulation and specify them when running the model using the CLI options. There is additional information on configuring the simulation in `experiments/README.md`


## CLI Options
```
-a [path]        path to json file containing initial agent states
-m [path]        path to json file containing model parameters
```