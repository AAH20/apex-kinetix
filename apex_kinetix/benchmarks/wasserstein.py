"""
1-Wasserstein (Earth Mover's Distance) Computation Engine.
Measures metric distance between empirical distributions in O(N log N) time.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from typing import List


class WassersteinMetric:
    """
    Computes the 1-Wasserstein distance W_1(U, V) = integral |F_U(x) - F_V(x)| dx.
    """

    @staticmethod
    def calculate_1d(sample_u: List[float], sample_v: List[float]) -> float:
        """
        Calculates 1-Wasserstein distance between two 1D empirical samples.
        Resamples both distributions to equal quantiles and computes average absolute difference.
        """
        if not sample_u or not sample_v:
            return 0.0

        sorted_u = sorted(sample_u)
        sorted_v = sorted(sample_v)

        n_u = len(sorted_u)
        n_v = len(sorted_v)

        # Resample to 200 uniform quantiles
        num_quantiles = 200
        quantiles_u: List[float] = []
        quantiles_v: List[float] = []

        for i in range(num_quantiles):
            alpha = (i + 0.5) / float(num_quantiles)
            idx_u = min(n_u - 1, int(alpha * n_u))
            idx_v = min(n_v - 1, int(alpha * n_v))
            quantiles_u.append(sorted_u[idx_u])
            quantiles_v.append(sorted_v[idx_v])

        # Sum of absolute differences between quantiles
        w1 = sum(abs(quantiles_u[i] - quantiles_v[i]) for i in range(num_quantiles)) / float(
            num_quantiles
        )
        return w1
