"""
Plamondon Kinematic Theory of Rapid Human Movements.
Implements the Sigma-Lognormal (Sigma-Lambda-M) stroke superposition model.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import math
from typing import List, Tuple
from apex_kinetix.core.types import Point2D, TrajectoryPoint, BehavioralGenome


class SigmaStroke:
    """
    A single neuromuscular stroke defined by Plamondon parameters.
    """

    def __init__(
        self,
        t0: float,
        amplitude: float,
        mu: float,
        sigma: float,
        theta_start: float,
        theta_end: float,
    ):
        self.t0 = t0
        self.amplitude = amplitude
        self.mu = mu
        self.sigma = sigma
        self.theta_start = theta_start
        self.theta_end = theta_end

    def evaluate_velocity(self, t: float) -> Tuple[float, float, float]:
        """
        Evaluates (speed, vx, vy) at time t.
        Returns: (magnitude, vx, vy)
        """
        if t <= self.t0:
            return 0.0, 0.0, 0.0

        dt = t - self.t0
        log_dt = math.log(dt)
        diff = log_dt - self.mu

        # Lognormal impulse response: D / (sqrt(2*pi) * sigma * dt) * exp(-diff^2 / (2*sigma^2))
        exponent = -(diff * diff) / (2.0 * self.sigma * self.sigma)
        if exponent < -20.0:
            return 0.0, 0.0, 0.0

        norm_factor = math.sqrt(2.0 * math.pi) * self.sigma * dt
        speed = (self.amplitude / norm_factor) * math.exp(exponent)

        # Angular orientation transition via erf
        erf_arg = diff / (self.sigma * math.sqrt(2.0))
        theta = self.theta_start + ((self.theta_end - self.theta_start) / 2.0) * (
            1.0 + math.erf(erf_arg)
        )

        vx = speed * math.cos(theta)
        vy = speed * math.sin(theta)
        return speed, vx, vy


class PlamondonEngine:
    """
    Synthesizes multi-stroke human planar trajectories.
    Decomposes point-to-point motion into a primary ballistic stroke and a corrective docking stroke.
    """

    @classmethod
    def synthesize_point_to_point(
        cls,
        origin: Point2D,
        destination: Point2D,
        duration: float,
        genome: BehavioralGenome,
        sample_hz: float = 125.0,
    ) -> List[TrajectoryPoint]:
        """
        Generates planar trajectory points using dual-stroke lognormal superposition.
        """
        dist = origin.distance_to(destination)
        if dist < 1.0 or duration <= 0.0:
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

        base_angle = math.atan2(destination.y - origin.y, destination.x - origin.x)

        # Primary stroke: ~82% of total distance
        primary_amp = dist * genome.stroke_ratio
        # Corrective secondary stroke: balance of distance with subtle angular curvature
        secondary_amp = dist * (1.0 - genome.stroke_ratio)

        # Timing: secondary stroke triggers at ~55% of the total duration
        t0_primary = 0.010
        t0_secondary = max(0.050, duration * 0.52)

        stroke1 = SigmaStroke(
            t0=t0_primary,
            amplitude=primary_amp,
            mu=genome.stroke_mu,
            sigma=genome.stroke_sigma,
            theta_start=base_angle - 0.05,
            theta_end=base_angle + 0.03,
        )

        stroke2 = SigmaStroke(
            t0=t0_secondary,
            amplitude=secondary_amp,
            mu=genome.stroke_mu + 0.15,
            sigma=genome.stroke_sigma * 0.90,
            theta_start=base_angle + 0.04,
            theta_end=base_angle,
        )

        dt = 1.0 / sample_hz
        num_steps = max(2, int(math.ceil(duration / dt)))

        raw_points: List[TrajectoryPoint] = []
        curr_x = origin.x
        curr_y = origin.y
        prev_vx = 0.0
        prev_vy = 0.0

        for i in range(num_steps + 1):
            t = min(duration, i * dt)

            s1, v1x, v1y = stroke1.evaluate_velocity(t)
            s2, v2x, v2y = stroke2.evaluate_velocity(t)

            vx = v1x + v2x
            vy = v1y + v2y

            # Numerical integration for position
            if i > 0:
                curr_x += 0.5 * (prev_vx + vx) * dt
                curr_y += 0.5 * (prev_vy + vy) * dt

            # Numerical acceleration
            if i > 0:
                ax = (vx - prev_vx) / dt
                ay = (vy - prev_vy) / dt
            else:
                ax = 0.0
                ay = 0.0

            prev_vx = vx
            prev_vy = vy

            raw_points.append(
                TrajectoryPoint(
                    timestamp=t,
                    x=curr_x,
                    y=curr_y,
                    vx=vx,
                    vy=vy,
                    ax=ax,
                    ay=ay,
                    jerk=0.0,
                    curvature=0.0,
                )
            )

        # Scale and dock exactly to destination to eliminate integration drift
        if raw_points:
            final_p = raw_points[-1]
            scale_x = (destination.x - origin.x) / max(1e-4, (final_p.x - origin.x))
            scale_y = (destination.y - origin.y) / max(1e-4, (final_p.y - origin.y))

            # Apply boundary-safe monotonic endpoint warping
            for p in raw_points:
                alpha = p.timestamp / max(1e-4, duration)
                # Position warp
                p.x = origin.x + (p.x - origin.x) * (1.0 + (scale_x - 1.0) * alpha)
                p.y = origin.y + (p.y - origin.y) * (1.0 + (scale_y - 1.0) * alpha)

            # Recompute jerk and curvature across the trajectory
            for i in range(1, len(raw_points)):
                dt_step = raw_points[i].timestamp - raw_points[i - 1].timestamp
                if dt_step > 1e-6:
                    jx = (raw_points[i].ax - raw_points[i - 1].ax) / dt_step
                    jy = (raw_points[i].ay - raw_points[i - 1].ay) / dt_step
                    raw_points[i].jerk = math.hypot(jx, jy)

                    v_mag = math.hypot(raw_points[i].vx, raw_points[i].vy)
                    if v_mag > 1e-4:
                        raw_points[i].curvature = abs(
                            raw_points[i].vx * raw_points[i].ay
                            - raw_points[i].vy * raw_points[i].ax
                        ) / (v_mag * v_mag * v_mag)

        return raw_points
