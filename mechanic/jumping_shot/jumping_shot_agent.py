import numpy as np
import math
from mechanic.base_test_agent import BaseTestAgent
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator
from util.linear_algebra import normalize
from .jumping_shot import JumpingShot


class TestAgent(BaseTestAgent):

    def create_mechanic(self):
        self.mechanic = JumpingShot(self, np.array([self.game_data.ball.location.x, self.game_data.ball.location.y,
                                                    self.game_data.ball.location.z]),
                                    self.game_data.time + (self.game_data.ball.location.z * .333 * 0.00833),
                                    self.game_data.game_tick_packet, rendering_enabled=False)

    def get_mechanic_controls(self):
        return self.mechanic.get_controls(self.game_data.my_car, self.game_data.game_tick_packet)
