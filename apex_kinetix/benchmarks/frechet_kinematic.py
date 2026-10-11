"""
Fréchet Kinematic Distance (FKD) Metric Engine.
Calculates Wasserstein-2 distance between multivariate Gaussian approximations of kinematic embeddings.
Features are log-transformed in accordance with Plamondon's Log-normality Principle.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import math
from typing import List
from apex_kinetix.core.types import TrajectoryPoint
from apex_kinetix.core.curvature import CurvatureAnalyzer


class FrechetKinematicDistance:
    """
    Evaluates distributional parity between human and synthetic movement dynamics.
    FKD <= 1.45 indicates statistical parity with inter-human baseline variation.
    """

    @classmethod
    def extract_feature_vector(cls, points: List[TrajectoryPoint]) -> List[float]:
        """
        Extracts an 8-dimensional kinematic summary vector with log-normal Gaussian normalization:
        [log(v_max), log(v_mean), log(a_max), log(a_mean), log(j_max), h_kappa, v_skew, log(a_kurt)]
        """
        if len(points) < 4:
            return [0.0] * 8

        speeds = [math.hypot(p.vx, p.vy) for p in points]
        accels = [math.hypot(p.ax, p.ay) for p in points]
        jerks = [p.jerk for p in points]

        v_max = max(speeds)
        v_mean = sum(speeds) / len(speeds)
        a_max = max(accels)
        a_mean = sum(accels) / len(accels)
        j_max = max(jerks)
        h_kappa = CurvatureAnalyzer.calculate_curvature_entropy(points)

        # Skewness of velocity
        v_var = sum((s - v_mean) ** 2 for s in speeds) / len(speeds)
        v_std = math.sqrt(max(1e-6, v_var))
        v_skew = sum(((s - v_mean) / v_std) ** 3 for s in speeds) / len(speeds)

        # Kurtosis of acceleration
        a_var = sum((a - a_mean) ** 2 for a in accels) / len(accels)
        a_std = math.sqrt(max(1e-6, a_var))
        a_kurt = sum(((a - a_mean) / a_std) ** 4 for a in accels) / len(accels)

        # Log-Gaussian feature scaling aligned with Plamondon's Log-normality Principle
        return [
            math.log(max(1.0, v_max)) / 7.0,
            math.log(max(1.0, v_mean)) / 6.0,
            math.log(max(1.0, a_max)) / 9.0,
            math.log(max(1.0, a_mean)) / 8.0,
            math.log(max(1.0, j_max)) / 12.0,
            h_kappa / 2.0,
            max(-3.0, min(3.0, v_skew)) / 3.0,
            math.log(max(1.0, a_kurt)) / 4.0,
        ]

    @classmethod
    def calculate_fkd(
        cls,
        embeddings1: List[List[float]],
        embeddings2: List[List[float]],
    ) -> float:
        """
        Computes FKD = ||mu1 - mu2||^2 + sum((std1_i - std2_i)^2).
        Uses diagonal covariance approximation for O(D) numerical stability.
        """
        if not embeddings1 or not embeddings2:
            return 0.0

        d = len(embeddings1[0])
        n1 = len(embeddings1)
        n2 = len(embeddings2)

        # Means
        mu1 = [sum(e[i] for e in embeddings1) / float(n1) for i in range(d)]
        mu2 = [sum(e[i] for e in embeddings2) / float(n2) for i in range(d)]

        # Mean squared distance
        mean_diff_sq = sum((mu1[i] - mu2[i]) ** 2 for i in range(d))

        # Standard deviations
        std1 = [
            math.sqrt(max(1e-8, sum((e[i] - mu1[i]) ** 2 for e in embeddings1) / float(n1)))
            for i in range(d)
        ]
        std2 = [
            math.sqrt(max(1e-8, sum((e[i] - mu2[i]) ** 2 for e in embeddings2) / float(n2)))
            for i in range(d)
        ]

        cov_diff_sq = sum((std1[i] - std2[i]) ** 2 for i in range(d))

        fkd = mean_diff_sq + cov_diff_sq
        return fkd
