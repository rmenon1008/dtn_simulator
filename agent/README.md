This directory contains the two "agent" types in the simulation:
- RouterAgent:  These agents represent the DTN-based backbone of the network.
  - IRL, these would be things with reliable/predictable regular movement patterns like satellites.
- ClientAgent:  These agents represent devices which utilize the DTN backbone for communications.
  - IRL, these would be things like rover robotics.

`agent_common.py` contains code content shared between the two agent types.