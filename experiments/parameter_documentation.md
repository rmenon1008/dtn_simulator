# Model Parameters

Model parameters defines model-wide constants

## Example JSON Format:
```
{
    "max_steps": 10000,         # Max number of steps to run the model for (can be None)
    "rssi_noise_stdev": 0,      # Standard deviation of the noise added to RSSI values
    "model_speed_limit": 10,    # Maximum speed of any agent in the model in m/s
    "host_router_mapping_timeout": 1000, # How long a client to host router mapping should be valid for
    "bundle_lifespan": 5000, # How long a bundle should be valid for
    "payload_lifespan": 5000, # How long a raw payload should be valid for
    "data_drop_schedule": [
        # Schedule of data drops
        #   - Drops can be picked up by any client that comes within 5 units
        #   - A payload is created from the drop and stored on the client
        #   - repeat_every is optional and can be used to repeat a drop every n steps
      {
        "drop_id": 0,
        "time": 5000,
        "pos": [
          475,
          400
        ],
        "target_id": 9,
        "repeat_every": 100 
        "until": 750        # optional parameter for "repeat_every". Repeat this drop until "until" steps is reached.
      },
      {
        "drop_id": 1,
        "time": 5000,
        "pos": [
          475005,
          400
        ],
        "target_id": 10,
        "repeat_every": 100
      }
    ]
  }
```

# Agent Parameters

Agent parameters defines the agents that will be created and their initial states

## Agent Units

- Reference speed = 3.5 m/s (7.8 mph, max speed of the Lunar Roving Vehicle)
- 1 model pixel = 1 meter
- 1 tick = 1 second

## Example JSON Format
```
{
    # Agent defaults are deep-merged with every agent's options
    # If a key is provided in both, the value provided here is ignored
  "agent_defaults": {
    "radio": {
      "detection_thresh": -60,  # RSSI threshold for detecting another agent
      "connection_thresh": -50  # RSSI threshold for connecting to another agent
    },
    "cp_file": "experiments/demo/5000steps_cp_d1.json"  # Contact plan file that routers should use for CGR
  },
    # Agents is a list of agents that will be created by the model
  "agents": [
    {
      "name": "P1",             # name used for special identification
      "type": "router",         # can be a "router" or a "client".
      "id": 1,                  # unique id used for doing work within simulation
      "movement": {
        "pattern": "arc",       " Arc Movement Pattern (currently buggy)
        "speed": 2.5,           # Speed of this agent in m/s
        "options": {
            "control_points": [ # Total of 3 points
              [0, 0],           # First 2 points must have same x or y values (roots of parabola)
              [0, 650],
              [200, 325]        # 3rd point is vertex of parabola (although this is the buggy part, vertex isn't used properly)
            ],
            "repeat": true,     # Whether to repeat the pattern or just stop (opt, default True)
            "bounce": false     # If repeat is True, whether to retrace points at the end or to start over from the beginning (opt, default False)
        }
      }
    },
    {
      "name": "P2",
      "type": "router",
      "id": 2,
      "movement": {
        "pattern": "waypoints", # Waypoint movement pattern
        "speed": 2.5,
        "options": {
            "waypoints": [      # Waypoints for the agent to go between in a straight line
              [200, 649],
              [200, 0]
            ],
            "repeat": true,
            "bounce": false
        }
      }
    },
    {
      "name": "P3",
      "type": "router",
      "id": 3,
      "movement": {
        "pattern": "circle",    # Circle movement pattern
        "speed": 3.5,
        "options": {
            "radius": 324,      # Radius of the circle
            "center": [         # Center of the circle
              500,
              325],
            "repeat": true      # Whether to repeat the circle or just stop (opt, default True)
        }
      }
    },
    {
      "name": "L1",
      "type": "router",
      "id": 4,
      "movement": {
        "pattern": "fixed",     # Fixed movement pattern, does not move
        "speed": 0,             # Must be speed of 0
        "options": {
          "pos": [              # Location of fixed node
            50,
            550
          ]
        }
      }
    },
    {
      "name": "C1",
      # Optional comment parameter for human readers of JSON file
      "comment": "this client spirals in the center of the screen. If sim goes on long enough, repeatedly runs into wall",
      "type": "client",         # set the agent type to be a ClientAgent.
      "id": 5,
      "radio": {
        "detection_thresh": -65 # customize detection threshold to be more loose (compared to default of -60)
      },
      "movement": {
        "pattern": "spiral",    # Spiral movement pattern
                                # Note: Spiral grows until its so large that it repeatedly runs into map's boundaries.
        "speed": 3.5,
        "options": {
          "center": [500,400],  # Center of the spiral
          "separation": 10      # Distance between spiral arms
        }
      }
    },
    {
      "name": "C2",
      "comment": "loops left of map -> loops right of map -> loops bottom of map -> repeat",
      "type": "client",
      "id": 6,
      "radio": {
        "detection_thresh": -65
      },
      "movement": {
        "pattern": "spline",        # Spline movement pattern
                                    # Interpolates a nice curve between given control points
                                    # If the first and last points are the same, the spline will be closed smoothly
                                    # Warning: Points between spline may cause a curve to be created
                                               that goes past map boundaries. Only current workaround is to change your control points.
        "speed": 3.5,
        "options": {
          "control_points": [       # Control points for the spline that is guaranted to be passed through
            [100,150],
            [150,150],
            [275,200],
            [250,300],
            [130,400],
            [175,260],
            [100,150],

            [750,150],
            [750,200],
            [950,150],
            [850,275],
            [950,300],
            [700,400],
            [850,150],
            [750,150],

            [500,600],
            [600,400],
            [500,500],
            [550,450],
            [400,500],
            [400,550],
            [450,625],
            [500,600],

            [100,150]
          ],
          "repeat": true,           # Whether to repeat the pattern or just stop (opt, default True)
          "bounce": false,          # If repeat is True, whether to retrace points
                                    # at the end or to start over from the beginning (opt, default False)
        }
      }
    },
  ]
}
```