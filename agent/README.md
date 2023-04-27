This directory contains the several types for simulation purposes:

These 2 agents are used for a Roaming DTN simulator
- RouterAgent:  These agents represent the DTN-based backbone of the network.
  - By default the backbone uses CGR as the routing algorithm,
    although epidemic and spray-and-wait are alternative options
  - IRL, these would be things with reliable/predictable regular movement patterns like satellites.
- ClientAgent:  These agents represent devices which utilize the DTN backbone for communications.
  - IRL, these would be things like rover robotics.

This agent is for an Epidemic only simulator
- EpidemicAgent: Floods bundles throughout the network
  - Only agents with names starting with "C" are able to pick up drops from the ground

This agent is for a Spray-and-Wait only simulator
- SprayAndWaitAgent: Upon picking up a payload, sprays a bundle to N others who will wait for the destination to pass by
  - Only agents with names starting with "C" are able to pick up drops from the ground

`agent_common.py` contains code content shared between all agent types.