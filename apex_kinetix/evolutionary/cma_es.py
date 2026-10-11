"""
Covariance Matrix Adaptation Evolution Strategy (CMA-ES).
Performs derivative-free continuous adaptation within behavioral niches.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import math
import random
from typing import Callable, List, Tuple
from apex_kinetix.core.types import BehavioralGenome


class LocalCMAESAdapter:
    """
    (1 + lambda) active continuous CMA-ES optimizer for continuous genome fine-tuning.
    """

    def __init__(self, initial_genome: BehavioralGenome, population_size: int = 8):
        self.dim = 12
        self.mean = initial_genome.to_vector()
        self.sigma = 0.05
        self.population_size = population_size
        # Diagonal covariance approximation for low-overhead embedded execution
        self.diag_c = [1.0] * self.dim

    def ask(self) -> List[BehavioralGenome]:
        """
        Samples a population of candidate genomes around the current mean.
        """
        candidates: List[BehavioralGenome] = []
        for _ in range(self.population_size):
            cand_v: List[float] = []
            for i in range(self.dim):
                step = random.gauss(0.0, math.sqrt(self.diag_c[i])) * self.sigma
                cand_v.append(self.mean[i] + step)
            candidates.append(BehavioralGenome.from_vector(cand_v))
        return candidates

    def tell(self, evaluated_population: List[Tuple[float, BehavioralGenome]]) -> None:
        """
        Updates mean and covariance based on ranked population evaluations.
        Input: list of (fitness, genome) tuples.
        """
        if not evaluated_population:
            return

        # Sort descending by fitness (higher is better)
        evaluated_population.sort(key=lambda item: item[0], reverse=True)
        mu = max(1, self.population_size // 2)
        top_candidates = evaluated_population[:mu]

        # Calculate recombination weights
        weights = [math.log(mu + 0.5) - math.log(i + 1) for i in range(mu)]
        sum_w = sum(weights)
        weights = [w / sum_w for w in weights]

        # Compute new mean
        new_mean = [0.0] * self.dim
        for w_idx, (_, genome) in enumerate(top_candidates):
            g_vec = genome.to_vector()
            w = weights[w_idx]
            for i in range(self.dim):
                new_mean[i] += w * g_vec[i]

        # Update step size & diagonal covariance
        for i in range(self.dim):
            variance_estimate = sum(
                weights[w_idx] * ((top_candidates[w_idx][1].to_vector()[i] - self.mean[i]) ** 2)
                for w_idx in range(mu)
            )
            # Damped update
            self.diag_c[i] = 0.85 * self.diag_c[i] + 0.15 * (variance_estimate / (self.sigma ** 2 + 1e-6))

        self.mean = new_mean
        # Adapt sigma
        best_fitness = top_candidates[0][0]
        worst_top_fitness = top_candidates[-1][0]
        if best_fitness > worst_top_fitness:
            self.sigma = min(0.20, self.sigma * 1.02)
        else:
            self.sigma = max(0.01, self.sigma * 0.98)

    def get_best_genome(self) -> BehavioralGenome:
        return BehavioralGenome.from_vector(self.mean)
