"""
Fitts's Law Motor Control Model.
Implements the Shannon formulation (MacKenzie 1992) for ballistic target acquisition.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import math
import random
from typing import Tuple
from apex_kinetix.core.types import Point2D, TargetBounds, BehavioralGenome


class FittsModel:
    """
    Computes Index of Difficulty (ID) and human movement time (MT).
    """

    @staticmethod
    def index_of_difficulty(distance: float, target_width: float) -> float:
        """
        Calculates Shannon formulation ID = log2(D / W + 1).
        Guarantees non-negative ID even for overlapping targets.
        """
        if distance < 0.0 or target_width <= 0.0:
            return 0.0
        return math.log2((distance / target_width) + 1.0)

    @classmethod
    def calculate_movement_time(
        cls,
        origin: Point2D,
        target: TargetBounds,
        genome: BehavioralGenome,
        inject_noise: bool = True,
    ) -> Tuple[float, float]:
        """
        Calculates expected movement duration T in seconds and ID in bits.
        Returns: (movement_time_seconds, index_of_difficulty_bits).
        """
        dist = origin.distance_to(target.center)
        # Use target width along motion axis; conservative effective width
        effective_w = min(target.width, target.height)
        if effective_w <= 0:
            effective_w = 20.0

        id_bits = cls.index_of_difficulty(dist, effective_w)
        mean_mt = genome.fitts_a + (genome.fitts_b * id_bits)

        if inject_noise:
            # Human execution noise scales mildly with movement duration
            noise_std = max(0.015, mean_mt * 0.08)
            mt = random.gauss(mean_mt, noise_std)
        else:
            mt = mean_mt

        # Bound by biological physiological minimum (120ms) and maximum (4500ms)
        clamped_mt = max(0.120, min(4.500, mt))
        return clamped_mt, id_bits
