def makeSerializeable(obj):
    """
    Helper function to make sure an object is serializeable
    to be sent to the visualization server.
    """
    if isinstance(obj, dict):
        return {k: makeSerializeable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [makeSerializeable(v) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(makeSerializeable(v) for v in obj)
    elif isinstance(obj, set):
        return set(makeSerializeable(v) for v in obj)
    elif isinstance(obj, complex):
        return (obj.real, obj.imag)
    elif isinstance(obj, type):
        return obj.__name__
    elif hasattr(obj, "__dict__"):
        return makeSerializeable(obj.__dict__)
    else:
        return obj


class Radio():
    def __init__(self, agent, model, options):
        self.agent = agent
        self.model = model
        self.detection_thresh = options["detection_thresh"]
        self.connection_thresh = options["connection_thresh"]
        self.neighborhood = []

    def refresh(self):
        # Update the neighborhood from the model helper
        self.neighborhood = self.model.get_neighbors(self.agent)

    def is_connected(self, other):
        for agent in self.neighborhood:
            if agent["connected"]:
                if agent["id"] == other or other == "all":
                    return True
        return False

    def get_state(self):
        return {
            "detection_thresh": self.detection_thresh,
            "estimated_detection_range": self.model.get_distance(self.detection_thresh),
            "connection_thresh": self.connection_thresh,
            "estimated_connection_range": self.model.get_distance(self.connection_thresh),
            "neighborhood": makeSerializeable(self.neighborhood)
        }
