import numpy as np

from mechanic.base_test_agent import BaseTestAgent
from mechanic.drive import DriveArriveInTime

from util.drive_physics_numpy import distance_traveled_numpy


class TestAgent(BaseTestAgent):

    def create_mechanic(self):
        return DriveArriveInTime(self)

    def get_mechanic_controls(self):

        ball_prediction = self.game_data.ball_prediction

        target_loc = self.game_data.ball.location
        target_dt = 0

        my_car_loc = self.game_data.my_car.location
        game_time = self.game_data.time

        # only accurate if we're already moving towards the target
        velocity = np.array([np.linalg.norm(self.game_data.my_car.velocity)] * len(ball_prediction))
        boost = np.array([self.game_data.my_car.boost] * len(ball_prediction))

        future_ball_locations = ball_prediction["physics"]["location"]
        distances = np.linalg.norm(future_ball_locations - my_car_loc, axis=1)
        times = ball_prediction["game_seconds"] - game_time

        reachable = (distance_traveled_numpy(times, velocity, boost) >
                     distances) & (future_ball_locations[:, 2] < 120)

        filtered_prediction = ball_prediction[reachable]

        if len(filtered_prediction) > 0:
            target_loc = filtered_prediction[0]["physics"]["location"]
            target_dt = filtered_prediction[0]["game_seconds"] - game_time

        return self.mechanic.step(self.game_data.my_car, target_loc, target_dt)
