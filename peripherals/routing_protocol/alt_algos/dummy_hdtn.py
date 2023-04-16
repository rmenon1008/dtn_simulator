# The old HDTN class. Remove when replaced with Dtn
class DummyHDTN():
    # Skeleton for the HDTN peripheral

    # The recevie_bundle method is called by another agent
    # when in contact range

    def __init__(self, agent, model, options):
        self.agent = agent
        self.model = model
        self.options = options

    def handle_bundle(self, bundle, type="data"):
        # Receive a bundle from another agent
        # This function can be called by another agent in connection range
        print("Agent {} received bundle {}".format(
            self.agent.unique_id, bundle))

    def get_state(self):
        # Called by the agent and sent to the visualization and added to history
        return {
            # "has_data": self.has_data,
            # "current_target": self.current_target
        }

    def refresh(self):
        # Called every step by the agent
        pass
