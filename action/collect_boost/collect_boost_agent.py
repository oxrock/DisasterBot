from action.base_test_agent import BaseTestAgent
from action.collect_boost import CollectBoost


class TestAgent(BaseTestAgent):
    def create_action(self):
        return CollectBoost(self, rendering_enabled=True)
