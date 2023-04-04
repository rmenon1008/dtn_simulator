import math
import logging

DETECTION_RANGE = 600
CONNECTION_RANGE = 20
RSSI_NOISE_DBM_STDEV = 0.1

class Radio():
    def __init__(self, agent, model, options):
        self.agent = agent
        self.model = model
        print(options)
        self.detection_range = options["detection_range"]
        self.connection_range = options["connection_range"]
        self.neighborhood = []

    def rssi(self, distance):
        if distance > self.detection_range:
            return None
        if distance == 0:
            return 0
        return 10 * 2.5 * math.log10(1/distance) * self.agent.random.normalvariate(1, self.radio_noise)
    
    def nodes_in_range(self, range):
        all_agents = self.model.schedule.agents
        within_range = []
        for other in all_agents:
            if other is not self.agent:
                distance = self.model.space.get_distance(self.agent.pos, other.pos)
                if distance <= range:
                    within_range.append(other)
        return within_range
    
    def refresh(self):
        self.neighborhood  = []
        other_agents = self.nodes_in_range(self.detection_range)
        for other in other_agents:
            distance = self.model.space.get_distance(self.agent.pos, other.pos)
            self.neighborhood.append({
                "id": other.unique_id,
                "rssi": self.rssi(distance),
                "connected": distance <= self.connection_range
            })
    
    def is_connected(self, other_id):
        for neighbor in self.neighborhood:
            if neighbor["id"] == other_id:
                return neighbor["connected"]
        return False
    
    def get_state(self):
        return {
            "detection_range": self.detection_range,
            "connection_range": self.connection_range,
            "neighborhood": self.neighborhood,
        }

class HDTN():
    def __init__(self, agent, model, options):
        self.agent = agent
        self.model = model
        self.has_data = False
        self.current_target = None

    def create_data(self):
        self.has_data = True

    def schedule_transfer(self, other_id, cb=None):
        self.current_target = other_id
        self.cb = cb
    
    def refresh(self):
        if self.current_target is not None:
            if self.current_target == "all":
                for agent in self.agent.radio.neighborhood:
                    if agent["connected"]:
                        self.current_target = agent["id"]
                        break
            if self.agent.radio.is_connected(self.current_target):
                logging.info("Agent {} transferred data to agent {}".format(self.agent.unique_id, self.current_target))
                for agent in self.model.schedule.agents:
                    if agent.unique_id == self.current_target:
                        logging.info("Agent {} received data from agent {}".format(agent.unique_id, self.agent.unique_id))
                        agent.hdtn.has_data = True
                        break

                if self.cb is not None:
                    self.cb(self.current_target)
                    self.cb = None

                self.has_data = False
                self.current_target = None


    def get_state(self):
        return {
            "has_data": self.has_data,
            "current_target": self.current_target
        }
