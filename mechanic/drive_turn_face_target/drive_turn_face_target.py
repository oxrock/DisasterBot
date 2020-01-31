import math
import numpy as np
from rlbot.agents.base_agent import SimpleControllerState
from mechanic.base_mechanic import BaseMechanic
from util.numerics import clip, sign

PI = math.pi


class DriveTurnFaceTarget(BaseMechanic):

    def step(self, car, target_loc) -> SimpleControllerState:

        target_in_local_coords = (target_loc - car.location).dot(car.rotation_matrix)
        car_local_velocity = car.velocity.dot(car.rotation_matrix)

        # PD for steer
        yaw_angle_to_target = math.atan2(target_in_local_coords[1], target_in_local_coords[0])
        car_ang_vel_local_coords = np.dot(car.angular_velocity, car.rotation_matrix)
        car_yaw_ang_vel = car_ang_vel_local_coords[2]

        proportional_steer = 11 * yaw_angle_to_target
        derivative_steer = -1 / 3 * car_yaw_ang_vel

        if yaw_angle_to_target >= 0:
            if yaw_angle_to_target - car_yaw_ang_vel / 3 > PI / 5:
                self.controls.handbrake = True
            else:
                self.controls.handbrake = False
        elif yaw_angle_to_target < 0:
            if yaw_angle_to_target - car_yaw_ang_vel / 3 < -PI / 5:
                self.controls.handbrake = True
            else:
                self.controls.handbrake = False

        self.controls.steer = clip(proportional_steer + derivative_steer)
        self.controls.throttle = 1
        self.controls.boost = not self.controls.handbrake

        # This makes sure we're not powersliding
        # if the car is spinning the opposite way we're steering towards
        if car_ang_vel_local_coords[2] * self.controls.steer < 0:
            self.controls.handbrake = False
        # and also not boosting if we're sliding the opposite way we're throttling towards.
        if car_local_velocity[0] * self.controls.throttle < 0:
            self.controls.handbrake = False

        # rendering
        strings = [f"yaw_angle_to_target : {yaw_angle_to_target:.2}",
                   f"car_yaw_ang_vel : {car_yaw_ang_vel:.2}",
                   f"steer : {self.controls.steer:.2f}"]

        self.agent.renderer.begin_rendering()
        for i, string in enumerate(strings):
            self.agent.renderer.draw_string_2d(20, 150 + i * 40, 2, 2, string,
                                               self.agent.renderer.white())
        self.agent.renderer.draw_rect_3d(target_loc, 20, 20, True, self.agent.renderer.red())
        self.agent.renderer.end_rendering()

        # updating status
        error = abs(car_yaw_ang_vel) + abs(yaw_angle_to_target)

        if error < 0.01:
            self.finished = True
        else:
            self.finished = False

        return self.controls
