from rlbot.agents.base_agent import SimpleControllerState

from mechanic.base_mechanic import BaseMechanic
from mechanic.drive_arrive_in_time import DriveArriveInTime
from skeleton.util.structure import Player

from util.linear_algebra import norm
from util.path_finder import find_fastest_path, first_target

import numpy as np


class DriveNavigateBoost(BaseMechanic):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mechanic = DriveArriveInTime(self.agent, self.rendering_enabled)

    def get_controls(self, car: Player, boost_pads, target_loc, target_dt=0, target_dir=None) -> SimpleControllerState:
        target_loc = target_loc.copy()
        target_loc[2] = 0
        target_dir = np.array([0.0, 0.0, 0.0]) if target_dir is None else target_dir
        path = find_fastest_path(boost_pads, car.location, target_loc, car.velocity, car.boost, target_dir)
        target = first_target(boost_pads, target_loc, path)

        time = target_dt if (target == target_loc).all() else 0

        # updating status
        if norm(car.location - target_loc) < 25 and abs(target_dt) < 0.05:
            self.finished = True
        else:
            self.finished = False

        return self.mechanic.get_controls(car, target, time)
