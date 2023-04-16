ROUTER_ID_0 = "r0"
ROUTER_ID_1 = "r1"
CLIENT_ID_0 = "c0"
CLIENT_ID_1 = "c1"

DEFAULT_SIZE = (1000, 550)

DEFAULT_MODEL_PARAMS = {
    # "size": (SIM_WIDTH, SIM_HEIGHT),
    "max_steps": 100000,
    "rssi_noise_stdev": 4.5,
    "model_speed_limit": 5,
}

DEFAULT_INITIAL_STATE = {
    "agent_defaults": {
        # If this is provided, all nodes will have
        # these options. It can be overridden by an
        # individual node's options.
        "radio": {
            "detection_thresh": -60,
            "connection_thresh": -25,
        },
        "dtn": {},
        "movement": {},
        "type": "router"  # can be a "router" or a "client".
    },
    "agents": [
        # The model will create an agent for each
        # node defined here. If "id" or "pos" are
        # not provided, they will be assigned
        # randomly.
        {
            "id": ROUTER_ID_0,
            "behavior": {
                "type": "fixed",
            },
            "pos": (DEFAULT_SIZE[0]/2, DEFAULT_SIZE[1]/2),
            "dtn": {},
        },
        {
            "id": ROUTER_ID_1,
            "behavior": {
                "type": "rssi_find_target",
                "options": {
                    "target_id": ROUTER_ID_0,
                },
            },
            "radio": {},
        },
        {
            "id": CLIENT_ID_0,
            "behavior": {
                "type": "random",
                "options": {
                    "target_id": 0,
                },
            },
            "radio": {},
            "type": "client"
        }
    ]
}