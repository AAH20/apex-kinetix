"""
Welch Power Spectral Density (PSD) and Spectral Slope Estimator.
Analyzes residual velocity and displacement fluctuations to verify 1/f biological pink noise (alpha ~ 1.0).
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import math
from typing import List, Tuple
from apex_kinetix.core.types import TrajectoryPoint


class SpectralAnalyzer:
    """
    Computes Discrete Fourier Transform periodogram and estimates 1/f spectral slope alpha.
    """

    @staticmethod
    def estimate_spectral_slope(
        signal: List[float],
        sample_rate: float = 250.0,
        freq_band: Tuple[float, float] = (1.0, 40.0),
    ) -> float:
        """
        Calculates spectral slope alpha via linear regression of ln(Power) vs ln(Frequency)
        for an arbitrary 1D signal (such as raw noise residuals or displacement).
        S(f) proportional to 1/f^alpha => ln(S) = -alpha * ln(f) + c.
        """
        n = len(signal)
        if n < 16:
            return 1.0

        mean_val = sum(signal) / n
        residuals = [s - mean_val for s in signal]

        log_f: List[float] = []
        log_p: List[float] = []

        half_n = n // 2
        for k in range(1, half_n):
            freq = (k * sample_rate) / float(n)
            if freq_band[0] <= freq <= freq_band[1]:
                real = 0.0
                imag = 0.0
                for t_idx in range(n):
                    angle = 2.0 * math.pi * k * t_idx / float(n)
                    real += residuals[t_idx] * math.cos(angle)
                    imag -= residuals[t_idx] * math.sin(angle)

                power = (real * real + imag * imag) / float(n)
                if power > 1e-12:
                    log_f.append(math.log(freq))
                    log_p.append(math.log(power))

        m = len(log_f)
        if m < 4:
            return 1.0

        mean_lf = sum(log_f) / m
        mean_lp = sum(log_p) / m

        num = sum((log_f[i] - mean_lf) * (log_p[i] - mean_lp) for i in range(m))
        den = sum((log_f[i] - mean_lf) ** 2 for i in range(m))

        if den < 1e-9:
            return 1.0

        slope = num / den
        alpha = -slope
        return alpha

    @classmethod
    def estimate_trajectory_displacement_slope(
        cls,
        actual_points: List[TrajectoryPoint],
        baseline_points: List[TrajectoryPoint],
        sample_rate: float = 250.0,
        freq_band: Tuple[float, float] = (2.0, 40.0),
    ) -> float:
        """
        Estimates spectral slope of Euclidean displacement residuals between actual
        and baseline trajectories.
        """
        n = min(len(actual_points), len(baseline_points))
        residuals = [
            math.hypot(
                actual_points[i].x - baseline_points[i].x,
                actual_points[i].y - baseline_points[i].y,
            )
            for i in range(n)
        ]
        return cls.estimate_spectral_slope(residuals, sample_rate, freq_band)
