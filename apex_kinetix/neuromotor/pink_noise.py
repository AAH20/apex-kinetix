"""
Voss-McCartney 1/f Fractional Pink Noise Generator.
Produces authentic pink noise where power spectral density S(f) is proportional to 1/f.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import math
import random
from typing import List
from apex_kinetix.core.types import TrajectoryPoint


class VossMcCartneyPinkNoise:
    """
    Simulates 1/f pink noise with Welch spectral slope alpha ~ 1.0.
    Uses K octave generators updated via trailing bit positions.
    """

    def __init__(self, num_octaves: int = 16):
        self.num_octaves = num_octaves
        self.octaves = [random.gauss(0.0, 1.0) for _ in range(num_octaves)]
        self.counter = 0

    def sample(self) -> float:
        """
        Generates the next 1/f noise sample in O(1) amortized time.
        """
        self.counter += 1
        n = self.counter

        # Find trailing zeros: which octave to refresh
        trailing_zeros = (n & -n).bit_length() - 1
        octave_idx = trailing_zeros % self.num_octaves

        self.octaves[octave_idx] = random.gauss(0.0, 1.0)
        total = sum(self.octaves)
        # Normalize so variance is roughly 1.0
        return total / math.sqrt(float(self.num_octaves))

    @classmethod
    def inject_pink_noise(
        cls,
        points: List[TrajectoryPoint],
        scale: float = 0.40,
    ) -> List[TrajectoryPoint]:
        """
        Superimposes 1/f pink noise residuals onto trajectory positions.
        """
        if len(points) < 3:
            return points

        duration = points[-1].timestamp
        if duration <= 0.0:
            return points

        gen_x = cls()
        gen_y = cls()

        result: List[TrajectoryPoint] = []
        for p in points:
            tau = p.timestamp / duration
            # Taper at edges
            taper = math.sin(tau * math.pi)

            dx = gen_x.sample() * scale * taper
            dy = gen_y.sample() * scale * taper

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

        # Smooth velocity estimates
        for i in range(1, len(result)):
            dt = result[i].timestamp - result[i - 1].timestamp
            if dt > 1e-6:
                result[i].vx = (result[i].x - result[i - 1].x) / dt
                result[i].vy = (result[i].y - result[i - 1].y) / dt

        return result
