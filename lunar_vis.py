import json

from mesa.visualization.ModularVisualization import VisualizationElement

class LunarVis(VisualizationElement):
    local_includes = ["js/lunar_vis.js", "js/fullscreen.js"]

    def __init__(self, simWidth, simHeight):
        self.width = simWidth
        self.height = simHeight
        new_element = "new LunarVis({}, {})".format(self.width, self.height)
        self.js_code = "elements.push(" + new_element + ");"

    def render(self, model):
        nodes = []
        for agent in model.schedule.agents:
            nodes.append(agent.get_state())
        return nodes
