"""
Phenotypic Behavioral Descriptor Extractor.
Extracts 4-dimensional behavioral vectors for MAP-Elites archive illumination.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import math
from typing import List
from apex_kinetix.core.types import TrajectoryPoint, PhenotypicDescriptor
from apex_kinetix.core.curvature import CurvatureAnalyzer


class BehavioralDescriptorExtractor:
    """
    Extracts phenotypic coordinates:
    b1: Mean velocity (px/s)
    b2: Curvature entropy H_kappa
    b3: Corrective submovement ratio
    b4: Fitts's Law residual deviation
    """

    @classmethod
    def extract(
        cls,
        points: List[TrajectoryPoint],
        expected_fitts_mt: float,
    ) -> PhenotypicDescriptor:
        if len(points) < 3:
            return PhenotypicDescriptor(
                mean_velocity=500.0,
                curvature_entropy=1.2,
                submovement_ratio=0.15,
                fitts_id_deviation=0.05,
            )

        # 1. Mean velocity
        speeds = [math.hypot(p.vx, p.vy) for p in points]
        mean_v = sum(speeds) / len(speeds)

        # 2. Curvature entropy
        h_kappa = CurvatureAnalyzer.calculate_curvature_entropy(points)

        # 3. Submovement ratio: check for velocity peaks in the deceleration phase (> 50% time)
        n = len(points)
        mid_idx = n // 2
        decel_speeds = speeds[mid_idx:]

        local_peaks = 0
        for i in range(1, len(decel_speeds) - 1):
            if (
                decel_speeds[i] > decel_speeds[i - 1]
                and decel_speeds[i] > decel_speeds[i + 1]
                and decel_speeds[i] > 15.0
            ):
                local_peaks += 1

        submovement_ratio = min(0.50, local_peaks * 0.12)

        # 4. Fitts ID deviation
        actual_mt = points[-1].timestamp
        if expected_fitts_mt > 0:
            fitts_dev = abs(actual_mt - expected_fitts_mt) / expected_fitts_mt
        else:
            fitts_dev = 0.0

        fitts_dev = min(0.50, fitts_dev)

        return PhenotypicDescriptor(
            mean_velocity=mean_v,
            curvature_entropy=h_kappa,
            submovement_ratio=submovement_ratio,
            fitts_id_deviation=fitts_dev,
        )
