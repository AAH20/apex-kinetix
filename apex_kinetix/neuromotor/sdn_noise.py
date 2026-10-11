"""
Harris and Wolpert (1998) Signal-Dependent Noise (SDN) Injector.
Models multiplicative motor noise proportional to control signal magnitude.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import math
import random
from typing import List
from apex_kinetix.core.types import TrajectoryPoint, BehavioralGenome


class SignalDependentNoiseInjector:
    """
    Injects biological motor variance that peaks during rapid ballistic execution
    and attenuates to zero at start and target docking endpoints.
    """

    @classmethod
    def inject_noise(
        cls,
        points: List[TrajectoryPoint],
        genome: BehavioralGenome,
    ) -> List[TrajectoryPoint]:
        if len(points) < 3:
            return points

        duration = points[-1].timestamp
        if duration <= 0.0:
            return points

        result: List[TrajectoryPoint] = []
        cum_dx = 0.0
        cum_dy = 0.0

        for i, p in enumerate(points):
            tau = p.timestamp / duration
            # Boundary taper window: 4 * tau * (1 - tau) peaks at 1.0 in center and vanishes at 0, 1
            taper = 4.0 * tau * (1.0 - tau)
            taper = max(0.0, min(1.0, taper))

            speed_sq = p.vx * p.vx + p.vy * p.vy
            sigma_sdn = math.sqrt(max(0.0, genome.sdn_k * speed_sq)) * taper

            if sigma_sdn > 0.001 and i > 0 and i < len(points) - 1:
                dx = random.gauss(0.0, sigma_sdn)
                dy = random.gauss(0.0, sigma_sdn)
                cum_dx += dx * 0.15
                cum_dy += dy * 0.15
            else:
                cum_dx *= 0.8
                cum_dy *= 0.8

            new_x = p.x + cum_dx * taper
            new_y = p.y + cum_dy * taper

            result.append(
                TrajectoryPoint(
                    timestamp=p.timestamp,
                    x=new_x,
                    y=new_y,
                    vx=p.vx,
                    vy=p.vy,
                    ax=p.ax,
                    ay=p.ay,
                    jerk=p.jerk,
                    curvature=p.curvature,
                )
            )

        # Smooth velocities and accelerations to reflect perturbed trajectory
        for i in range(1, len(result)):
            dt = result[i].timestamp - result[i - 1].timestamp
            if dt > 1e-6:
                result[i].vx = (result[i].x - result[i - 1].x) / dt
                result[i].vy = (result[i].y - result[i - 1].y) / dt
                if i > 1:
                    result[i].ax = (result[i].vx - result[i - 1].vx) / dt
                    result[i].ay = (result[i].vy - result[i - 1].vy) / dt

        return result
