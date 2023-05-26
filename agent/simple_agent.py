import mesa

from agent.agent_common import try_getting, least_squares_convergence
from peripherals.movement import Movement
from peripherals.radio import Radio
from peripherals.convergence import Convergence

class SimpleAgent(mesa.Agent):
    # Maximum length of the history to keep. Prevents the simulation from slowing down.
    MAX_HISTORY_LENGTH = 150

    def __init__(self, model, node_options):
        super().__init__(node_options["id"], model)
        self.name = try_getting(node_options, "name", default=None)
        self.special_behavior = try_getting(node_options, "special_behavior", default={})
        
        # Peripherals
        # We supply these with the entire agent and model, so they can access
        # everything they might need. Be careful about using info that agents
        # might not have access to in real life (e.g. the pos of other agents)
        self.movement = Movement(self, model, node_options["movement"])
        self.radio = Radio(self, model, node_options["radio"])

        target = try_getting(node_options, "special_behavior", "options", "target_id", default="all")
        self.convergence = Convergence(self, model, target)
    
    def step(self):
        # @Everyone: This function gets called every step of the simulation by the model
        #            It's where the logic for the agent lives.

        # Update our peripherals
        self.movement.refresh()
        self.convergence.refresh()
        self.radio.refresh()

        # Special behavior
        if self.special_behavior is not None:
            sb_type = try_getting(self.special_behavior, "type", default=None)

            if sb_type == "least_squares_convergence":
                self.convergence.step()
            else:
                self.movement.step()

    def get_state(self):
        return {
            "id": self.unique_id,
            "name": self.name,
            "pos": self.pos,
            "radio": self.radio.get_state(),
            "movement": self.movement.get_state(),
            "history": self.convergence.history,
        }