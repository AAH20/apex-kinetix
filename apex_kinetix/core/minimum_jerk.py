"""
Flash and Hogan (1985) Minimum Jerk Kinematic Trajectory Solver.
Optimizes planar point-to-point movements by minimizing total squared jerk.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import math
from typing import List, Tuple
from apex_kinetix.core.types import Point2D, TrajectoryPoint


class MinimumJerkPlanner:
    """
    Evaluates 5th-order polynomial trajectories that satisfy zero velocity,
    zero acceleration, and minimum jerk boundary conditions.
    """

    @staticmethod
    def evaluate_1d(
        x0: float, xf: float, duration: float, t: float
    ) -> Tuple[float, float, float, float]:
        """
        Evaluates position, velocity, acceleration, and jerk for a 1D coordinate.
        Returns: (position, velocity, acceleration, jerk)
        """
        if duration <= 0.0:
            return xf, 0.0, 0.0, 0.0

        tau = max(0.0, min(1.0, t / duration))
        tau2 = tau * tau
        tau3 = tau2 * tau
        tau4 = tau3 * tau
        tau5 = tau4 * tau

        delta = xf - x0

        # Position: x0 + delta * (10*tau^3 - 15*tau^4 + 6*tau^5)
        pos = x0 + delta * (10.0 * tau3 - 15.0 * tau4 + 6.0 * tau5)

        # Velocity: (delta / T) * (30*tau^2 - 60*tau^3 + 30*tau^4)
        vel = (delta / duration) * (30.0 * tau2 - 60.0 * tau3 + 30.0 * tau4)

        # Acceleration: (delta / T^2) * (60*tau - 180*tau^2 + 120*tau^3)
        acc = (delta / (duration * duration)) * (60.0 * tau - 180.0 * tau2 + 120.0 * tau3)

        # Jerk: (delta / T^3) * (60 - 360*tau + 360*tau^2)
        jerk = (delta / (duration * duration * duration)) * (60.0 - 360.0 * tau + 360.0 * tau2)

        return pos, vel, acc, jerk

    @classmethod
    def generate_trajectory(
        cls,
        origin: Point2D,
        destination: Point2D,
        duration: float,
        sample_hz: float = 125.0,
    ) -> List[TrajectoryPoint]:
        """
        Generates a discrete sequence of TrajectoryPoints at sample_hz (default: 125Hz = 8ms step).
        """
        points: List[TrajectoryPoint] = []
        if duration <= 0.0:
            return [
                TrajectoryPoint(
                    timestamp=0.0,
                    x=destination.x,
                    y=destination.y,
                    vx=0.0,
                    vy=0.0,
                    ax=0.0,
                    ay=0.0,
                    jerk=0.0,
                    curvature=0.0,
                )
            ]

        dt = 1.0 / sample_hz
        num_steps = max(2, int(math.ceil(duration / dt)))

        for i in range(num_steps + 1):
            t = min(duration, i * dt)
            x, vx, ax, jx = cls.evaluate_1d(origin.x, destination.x, duration, t)
            y, vy, ay, jy = cls.evaluate_1d(origin.y, destination.y, duration, t)

            v_mag = math.hypot(vx, vy)
            j_mag = math.hypot(jx, jy)

            # Frenet-Serret curvature: kappa = |vx*ay - vy*ax| / (vx^2 + vy^2)^(3/2)
            if v_mag > 1e-4:
                curvature = abs(vx * ay - vy * ax) / (v_mag * v_mag * v_mag)
            else:
                curvature = 0.0

            points.append(
                TrajectoryPoint(
                    timestamp=t,
                    x=x,
                    y=y,
                    vx=vx,
                    vy=vy,
                    ax=ax,
                    ay=ay,
                    jerk=j_mag,
                    curvature=curvature,
                )
            )

        return points
