import time
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from skeleton.util.structure.game_data import GameData


class SkeletonAgent(BaseAgent):

    """Base class inheriting from BaseAgent that manages data provided by the rlbot framework,
    and converts it into our internal data structure, and extracts further useful info."""

    def __init__(self, name: str = 'skeleton', team: int = 0, index: int = 0):

        super(SkeletonAgent, self).__init__(name, team, index)

        self.game_data = GameData(self.name, self.team, self.index)
        self.controls = SimpleControllerState()

    def get_output(self, game_tick_packet: GameTickPacket) -> SimpleControllerState:
        """Overriding this function is not advised, use get_controls() instead."""

        chrono_start = time.time()

        self.pre_process(game_tick_packet)

        self.controls = self.get_controls()

        self.feedback()

        delta_time = time.time() - chrono_start

        if delta_time > 1 / 120:
            self.logger.warn(f"Took too long to execute: {round(delta_time, 5)} seconds.")

        return self.controls

    def pre_process(self, game_tick_packet: GameTickPacket):
        """First thing executed in get_output()."""

        self.game_data.read_field_info(self.get_field_info())
        self.game_data.read_game_tick_packet(game_tick_packet)
        self.game_data.read_ball_prediction_struct(self.get_ball_prediction_struct())
        self.game_data.update_extra_game_data()

    def feedback(self):
        """Last thing executed in get_output() before return statement."""

        self.game_data.feedback(self.controls)

    def get_controls(self) -> SimpleControllerState:
        """Function to override by inheriting classes"""
        return self.controls
