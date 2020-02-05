import math
from collections import namedtuple

from numba import vectorize, float64, jit

THROTTLE_ACCELERATION_0 = 1600.
THROTTLE_ACCELERATION_1400 = 160.
THROTTLE_MID_SPEED = 1400.

BOOST_ACCELERATION = 991.6667
BREAK_ACCELERATION = 3500.

MAX_CAR_SPEED = 2300.

BOOST_CONSUMPTION_RATE = 33.3  # per second

# constants of the acceleration between 0 to 1400 velocity: acceleration = a * velocity + b
a = - (THROTTLE_ACCELERATION_0 - THROTTLE_ACCELERATION_1400) / THROTTLE_MID_SPEED
b = THROTTLE_ACCELERATION_0

fast_jit = jit(nopython=True, fastmath=True)


State = namedtuple('State', ['vel', 'boost', 'time', 'dist'])


class VelocityRange:
    max_speed = None
    use_boost = None

    @staticmethod
    def distance_traveled(t: float, v0: float) -> float:
        raise NotImplementedError

    @staticmethod
    def velocity_reached(t: float, v0: float) -> float:
        raise NotImplementedError

    @staticmethod
    def time_reach_velocity(v: float, v0: float) -> float:
        raise NotImplementedError

    @classmethod
    def wrap_distance_state_step(cls):
        """Advances the state to the soonest phase end."""

        cls_max_speed = cls.max_speed
        cls_distance_traveled = cls.distance_traveled
        cls_velocity_reached = cls.velocity_reached
        cls_time_reach_velocity = cls.time_reach_velocity

        if cls.use_boost:
            def distance_state_step(state: State) -> State:
                if cls_max_speed <= state.vel or state.time == 0.:
                    return state

                t_boost = state.boost / BOOST_CONSUMPTION_RATE
                t_vel = cls_time_reach_velocity(cls_max_speed, state.vel)

                if state.time <= t_boost and state.time <= t_vel:
                    dist = state.dist + cls_distance_traveled(state.time, state.vel)
                    return State(0., 0., 0., dist)

                if t_boost < t_vel:
                    t = t_boost
                    vel = cls_velocity_reached(t_boost, state.vel)
                    boost = 0.
                else:
                    t = t_vel
                    vel = cls_max_speed
                    boost = state.boost - t * BOOST_CONSUMPTION_RATE

                dist = state.dist + cls_distance_traveled(t, state.vel)
                time = state.time - t

                return State(vel, boost, time, dist)
        else:
            def distance_state_step(state: State) -> State:
                if cls_max_speed <= state.vel or state.time == 0.:
                    return state

                t = cls_time_reach_velocity(cls_max_speed, state.vel)

                if state.time <= t:
                    dist = state.dist + cls_distance_traveled(state.time, state.vel)
                    return State(0., 0., 0., dist)

                dist = state.dist + cls_distance_traveled(t, state.vel)
                time = state.time - t

                return State(cls_max_speed, state.boost, time, dist)

        return fast_jit(distance_state_step)


class Velocity0To1400(VelocityRange):
    max_speed = THROTTLE_MID_SPEED
    use_boost = False

    @staticmethod
    @fast_jit
    def distance_traveled(t: float, v0: float) -> float:
        return (b * (-a * t + math.expm1(a * t)) + a * v0 * math.expm1(a * t)) / (a * a)

    @staticmethod
    @fast_jit
    def velocity_reached(t: float, v0: float) -> float:
        return (b * math.expm1(a * t)) / a + v0 * math.exp(a * t)

    @staticmethod
    @fast_jit
    def time_reach_velocity(v: float, v0: float) -> float:
        return math.log((a * v + b) / (a * v0 + b)) / a


class Velocity0To1400Boost(VelocityRange):
    max_speed = THROTTLE_MID_SPEED
    use_boost = True

    @staticmethod
    @fast_jit
    def distance_traveled(t: float, v0: float) -> float:
        b = THROTTLE_ACCELERATION_0 + BOOST_ACCELERATION
        return (b * (-a * t + math.expm1(a * t)) + a * v0 * math.expm1(a * t)) / (a * a)

    @staticmethod
    @fast_jit
    def velocity_reached(t: float, v0: float) -> float:
        b = THROTTLE_ACCELERATION_0 + BOOST_ACCELERATION
        return (b * math.expm1(a * t)) / a + v0 * math.exp(a * t)

    @staticmethod
    @fast_jit
    def time_reach_velocity(v: float, v0: float) -> float:
        b = THROTTLE_ACCELERATION_0 + BOOST_ACCELERATION
        return math.log((a * v + b) / (a * v0 + b)) / a


# for when the only acceleration that applies is from boost.
class Velocity1400To2300(Velocity0To1400):
    max_speed = MAX_CAR_SPEED
    use_boost = True

    @staticmethod
    @fast_jit
    def distance_traveled(t: float, v0: float) -> float:
        return t * (BOOST_ACCELERATION * t + 2 * v0) / 2

    @staticmethod
    @fast_jit
    def velocity_reached(t: float, v0: float) -> float:
        return BOOST_ACCELERATION * t + v0

    @staticmethod
    @fast_jit
    def time_reach_velocity(v: float, v0: float) -> float:
        return (v - v0) / BOOST_ACCELERATION


# for when the velocity is opposite the throttle direction,
# only the breaking acceleration applies, boosting has no effect.
# assuming throttle is positive, flip velocity signs if otherwise.
class VelocityNegative(VelocityRange):
    max_speed = 0.
    use_boost = False

    @staticmethod
    @fast_jit
    def distance_traveled(t: float, v0: float) -> float:
        return t * (BREAK_ACCELERATION * t + 2 * v0) / 2

    @staticmethod
    @fast_jit
    def velocity_reached(t: float, v0: float) -> float:
        return BREAK_ACCELERATION * t + v0

    @staticmethod
    @fast_jit
    def time_reach_velocity(v: float, v0: float) -> float:
        return (v - v0) / BREAK_ACCELERATION


step1 = VelocityNegative.wrap_distance_state_step()
step2 = Velocity0To1400Boost.wrap_distance_state_step()
step3 = Velocity0To1400.wrap_distance_state_step()
step4 = Velocity1400To2300.wrap_distance_state_step()


@jit(float64(float64, float64, float64), nopython=True, fastmath=True)
def distance_traveled(t: float, v0: float, boost_amount: float) -> float:
    """Returns the max distance driven forward using boost, this allows any starting velocity
    assuming we're not using boost when going backwards and using it otherwise."""
    state = State(v0, boost_amount, t, 0.)

    state = step1(state)
    state = step2(state)
    state = step3(state)
    state = step4(state)

    return state.dist + state.time * state.vel


distance_traveled_vectorized = vectorize(
    [float64(float64, float64, float64)], nopython=True)(distance_traveled)


def main():

    from timeit import timeit
    import numpy as np

    time = np.linspace(0.1, 6, 360)
    initial_velocity = np.linspace(-2300, 2300, 360)
    boost_amount = np.linspace(0, 100, 360)

    def test_function():
        return distance_traveled_vectorized(time, initial_velocity, boost_amount)

    print(test_function())

    fps = 120
    n_times = 10000
    time_taken = timeit(test_function, number=n_times)
    percentage = round(time_taken * fps / n_times * 100, 5)

    print(f"Took {time_taken} seconds to run {n_times} times.")
    print(f"That's {percentage} % of our time budget.")


if __name__ == '__main__':
    main()

    from drive_physics_experimental import distance_traveled as distance_traveled2

    for time in range(0, 100):
        time = time / 10
        print(time)
        for initial_velocity in range(0, 2300, 100):
            for boost_amount in range(0, 100, 10):
                res1 = distance_traveled(time, initial_velocity, boost_amount)
                res2 = distance_traveled2(time, initial_velocity, boost_amount)
                if abs(res1 - res2) > 0.0001:
                    print(time, initial_velocity, boost_amount, ' : ', res1, res2)
                    quit()
