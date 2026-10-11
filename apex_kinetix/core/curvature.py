"""
Differential Geometry and Curvature Entropy Analysis.
Implements Frenet-Serret frame calculations and Shannon entropy over trajectory curvature.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import math
from typing import List
from apex_kinetix.core.types import TrajectoryPoint


class CurvatureAnalyzer:
    """
    Computes path curvature, curvature entropy, and 2/3-power law compliance.
    """

    @staticmethod
    def compute_instantaneous_curvature(vx: float, vy: float, ax: float, ay: float) -> float:
        """
        Calculates kappa = |vx*ay - vy*ax| / (vx^2 + vy^2)^(3/2).
        """
        speed_sq = vx * vx + vy * vy
        if speed_sq < 1e-6:
            return 0.0
        numerator = abs(vx * ay - vy * ax)
        denominator = speed_sq * math.sqrt(speed_sq)
        return numerator / denominator

    @classmethod
    def calculate_curvature_entropy(
        cls, points: List[TrajectoryPoint], num_bins: int = 20
    ) -> float:
        """
        Computes Shannon entropy H_kappa = -sum(p_i * ln(p_i)) of the curvature distribution.
        Measures the geometric complexity and tortuosity of the motion.
        """
        if len(points) < 3:
            return 0.0

        curvatures = [p.curvature for p in points if p.curvature > 0.0]
        if not curvatures:
            return 0.0

        max_c = max(curvatures)
        min_c = min(curvatures)
        if max_c <= min_c:
            return 0.0

        bin_width = (max_c - min_c) / float(num_bins)
        counts = [0] * num_bins

        for c in curvatures:
            idx = int((c - min_c) / bin_width)
            if idx >= num_bins:
                idx = num_bins - 1
            counts[idx] += 1

        total = float(len(curvatures))
        entropy = 0.0
        for count in counts:
            if count > 0:
                p = count / total
                entropy -= p * math.log(p)

        return entropy

    @classmethod
    def calculate_power_law_index(cls, points: List[TrajectoryPoint]) -> float:
        """
        Estimates the Two-Thirds Power Law exponent beta in v = gamma * kappa^(-beta).
        Biological human planar motions exhibit beta ~ 0.33 (1/3).
        Returns beta via linear regression on ln(v) vs ln(kappa).
        """
        log_v: List[float] = []
        log_k: List[float] = []

        for p in points:
            speed = math.hypot(p.vx, p.vy)
            if speed > 10.0 and p.curvature > 0.001:
                log_v.append(math.log(speed))
                log_k.append(math.log(p.curvature))

        n = len(log_v)
        if n < 5:
            return 0.33  # Default biological constant

        mean_k = sum(log_k) / n
        mean_v = sum(log_v) / n

        num = sum((log_k[i] - mean_k) * (log_v[i] - mean_v) for i in range(n))
        den = sum((log_k[i] - mean_k) ** 2 for i in range(n))

        if den < 1e-9:
            return 0.33

        slope = num / den
        # Since v = gamma * kappa^(-beta), slope is -beta, so beta = -slope
        beta = -slope
        return beta
