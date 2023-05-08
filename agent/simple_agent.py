import mesa

from agent.agent_common import try_getting, least_squares_convergence
from peripherals.movement import Movement
from peripherals.radio import Radio

class SimpleAgent(mesa.Agent):
    # Maximum length of the history to keep. Prevents the simulation from slowing down.
    MAX_HISTORY_LENGTH = 150

    def __init__(self, model, node_options):
        super().__init__(node_options["id"], model)
        self.name = try_getting(node_options, "name", default=None)
        self.history = []
        self.special_behavior = try_getting(node_options, "special_behavior", default={})
        
        # Peripherals
        # We supply these with the entire agent and model, so they can access
        # everything they might need. Be careful about using info that agents
        # might not have access to in real life (e.g. the pos of other agents)
        self.movement = Movement(self, model, node_options["movement"])
        self.radio = Radio(self, model, node_options["radio"])

    def update_history(self):
        # Keep a list of past positions and radio states
        # Used for least squares convergence right now
        self.history.append({
            "pos": self.pos,
            "radio": self.radio.get_state(),
        })
        self.history = self.history[-self.MAX_HISTORY_LENGTH:]
    
    def step(self):
        # @Everyone: This function gets called every step of the simulation by the model
        #            It's where the logic for the agent lives.

        # Update our peripherals
        self.movement.refresh()
        self.radio.refresh()
        self.update_history()

        # Special behavior
        if self.special_behavior is not None:
            sb_type = try_getting(self.special_behavior, "type", default=None)

            # @Alex: "special behavior" is an agent parameter that gets run instead
            #        of the normal movement pattern. Right now, the only implemented
            #        special behavior is least squares convergence, but we can add
            #        different convergence algorithms as well.

            if sb_type == "least_squares_convergence":
                # Move towards a target based on RSSI

                # We pass this method our entire agent, so it has access to 
                # everything the agent has, including its peripherals.
                least_squares_convergence(self)

            elif sb_type == "other_alg":
                # Do something else
                pass
            
            else:
                # Just move based on the movement pattern
                self.movement.step()

    def get_state(self):
        return {
            "id": self.unique_id,
            "name": self.name,
            "pos": self.pos,
            "history": self.history,
            "radio": self.radio.get_state(),
        }