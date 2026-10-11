"""
Physiological Micro-Tremor Generator.
Models 8-12 Hz neuromuscular oscillations inherent to human hand-arm motor units.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import math
import random
from typing import List
from apex_kinetix.core.types import TrajectoryPoint, BehavioralGenome


class PhysiologicalTremorGenerator:
    """
    Superimposes 8-12 Hz biological oscillatory micro-tremor on cursor positions.
    """

    @classmethod
    def inject_tremor(
        cls,
        points: List[TrajectoryPoint],
        genome: BehavioralGenome,
    ) -> List[TrajectoryPoint]:
        if len(points) < 3:
            return points

        duration = points[-1].timestamp
        if duration <= 0.0:
            return points

        phi_x = random.uniform(0.0, 2.0 * math.pi)
        phi_y = random.uniform(0.0, 2.0 * math.pi)
        freq_rad = 2.0 * math.pi * genome.tremor_freq

        result: List[TrajectoryPoint] = []
        for p in points:
            tau = p.timestamp / duration
            # Taper so tremor is subtle at edges and present throughout flight
            taper = math.sin(tau * math.pi)

            dx = genome.tremor_amp * math.sin(freq_rad * p.timestamp + phi_x) * taper
            dy = genome.tremor_amp * math.cos(freq_rad * p.timestamp + phi_y) * taper

            result.append(
                TrajectoryPoint(
                    timestamp=p.timestamp,
                    x=p.x + dx,
                    y=p.y + dy,
                    vx=p.vx,
                    vy=p.vy,
                    ax=p.ax,
                    ay=p.ay,
                    jerk=p.jerk,
                    curvature=p.curvature,
                )
            )

        # Re-derive velocities
        for i in range(1, len(result)):
            dt = result[i].timestamp - result[i - 1].timestamp
            if dt > 1e-6:
                result[i].vx = (result[i].x - result[i - 1].x) / dt
                result[i].vy = (result[i].y - result[i - 1].y) / dt

        return result
