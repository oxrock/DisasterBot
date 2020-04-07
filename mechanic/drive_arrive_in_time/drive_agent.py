from mechanic.base_test_agent import BaseTestAgent
from mechanic.drive_arrive_in_time import DriveArriveInTime
from util.ball_utils import get_ground_ball_intercept_state


class TestAgent(BaseTestAgent):
    def create_mechanic(self):
        return DriveArriveInTime(self, rendering_enabled=True)

    def get_mechanic_controls(self):

        target_loc, target_dt = get_ground_ball_intercept_state(self.game_data)

        return self.mechanic.get_controls(self.game_data.my_car, target_loc, target_dt)
