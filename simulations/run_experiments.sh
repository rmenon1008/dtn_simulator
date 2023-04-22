#!/bin/bash

# Must be run from top-level of dcgr_simulation directory

EXP=$1
agent_path=(./simulations/scenario${EXP}/agents_s${EXP}.json)
model_path=(./simulations/scenario${EXP}/model_s${EXP}.json)

cmd="python run_model_vis.py -a $agent_path -m $model_path"
echo "executing: $cmd"
exec $cmd