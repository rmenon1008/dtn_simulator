import math
import logging

DETECTION_RANGE = 600
CONNECTION_RANGE = 20
RSSI_NOISE_DBM_STDEV = 0.03

class Radio():
    def __init__(self, agent, model, detection_range=DETECTION_RANGE, connection_range=CONNECTION_RANGE):
        self.agent = agent
        self.model = model
        self.detection_range = detection_range
        self.connection_range = connection_range
        self.neighborhood = []
        self.best_rssi = -999

    def rssi(self, distance):
        if distance > self.detection_range:
            return -999
        if distance == 0:
            return 0
        return 10 * 2.5 * math.log10(1/distance) * self.agent.random.normalvariate(1, RSSI_NOISE_DBM_STDEV)
    
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
        self.best_rssi = max([neighbor["rssi"] for neighbor in self.neighborhood]) if len(self.neighborhood) > 0 else -999

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
            "best_rssi": self.best_rssi
        }

class HDTN():
    def __init__(self, agent, model):
        self.agent = agent
        self.model = model
        self.has_data = False
        self.current_target = None

    def create_data(self):
        self.has_data = True

    def schedule_transfer(self, other_id):
        self.current_target = other_id
    
    def refresh(self):
        if self.current_target is not None:
            if self.agent.radio.is_connected(self.current_target):
                logging.info("Agent {} transferred data to agent {}".format(self.agent.unique_id, self.current_target))
                for agent in self.model.schedule.agents:
                    if agent.unique_id == self.current_target:
                        logging.info("Agent {} received data from agent {}".format(agent.unique_id, self.agent.unique_id))
                        agent.hdtn.has_data = True
                        break

                self.has_data = False
                self.current_target = None
                

    def get_state(self):
        return {
            "has_data": self.has_data,
            "current_target": self.current_target
        }
