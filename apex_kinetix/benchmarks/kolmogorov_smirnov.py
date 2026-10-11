"""
Two-Sample Kolmogorov-Smirnov (KS) Test Engine.
Tests the null hypothesis that two empirical samples are drawn from the same continuous distribution.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import math
from typing import List, Tuple


class KolmogorovSmirnovTest:
    """
    Computes D_KS statistic and asymptotic p-value for two independent empirical samples.
    """

    @staticmethod
    def calculate_2sample(
        sample1: List[float], sample2: List[float]
    ) -> Tuple[float, float]:
        """
        Calculates (D_statistic, p_value).
        Null hypothesis: sample1 and sample2 come from identical distributions.
        A p-value > 0.05 indicates failure to reject the null (statistically indistinguishable).
        """
        n1 = len(sample1)
        n2 = len(sample2)
        if n1 == 0 or n2 == 0:
            return 0.0, 1.0

        s1 = sorted(sample1)
        s2 = sorted(sample2)

        # Merge sorted lists to compute maximum CDF discrepancy
        all_vals = sorted(set(s1 + s2))

        d_max = 0.0
        i1 = 0
        i2 = 0

        for val in all_vals:
            while i1 < n1 and s1[i1] <= val:
                i1 += 1
            while i2 < n2 and s2[i2] <= val:
                i2 += 1

            cdf1 = i1 / float(n1)
            cdf2 = i2 / float(n2)
            diff = abs(cdf1 - cdf2)
            if diff > d_max:
                d_max = diff

        # Asymptotic p-value approximation via Kolmogorov distribution
        en = math.sqrt((n1 * n2) / float(n1 + n2))
        lambda_val = (en + 0.12 + 0.11 / en) * d_max

        if lambda_val <= 0.0:
            p_value = 1.0
        else:
            # Kolmogorov distribution series: 2 * sum_{k=1}^infinity (-1)^(k-1) * exp(-2*k^2*lambda^2)
            p_sum = 0.0
            for k in range(1, 101):
                term = 2.0 * ((-1) ** (k - 1)) * math.exp(-2.0 * (k ** 2) * (lambda_val ** 2))
                p_sum += term
                if abs(term) < 1e-8:
                    break
            p_value = max(0.0, min(1.0, p_sum))

        return d_max, p_value
