"""
Multi-Dimensional Archive of Phenotypic Elites (MAP-Elites).
Quality-Diversity evolutionary algorithm maintaining diverse high-performing motor genomes.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import math
import random
from typing import Dict, List, Optional, Tuple
from apex_kinetix.core.types import BehavioralGenome, PhenotypicDescriptor


class MAPElitesArchive:
    """
    4D Quality-Diversity behavioral grid archive.
    Discretizes phenotypic behavior space to prevent mode collapse and fingerprinting.
    """

    def __init__(
        self,
        bins: Tuple[int, int, int, int] = (20, 20, 15, 10),
        ranges: Tuple[
            Tuple[float, float],
            Tuple[float, float],
            Tuple[float, float],
            Tuple[float, float],
        ] = (
            (150.0, 2400.0),  # Mean velocity (px/s)
            (0.2, 3.2),       # Curvature entropy
            (0.0, 0.5),       # Submovement ratio
            (0.0, 0.3),       # Fitts ID deviation
        ),
    ):
        self.bins = bins
        self.ranges = ranges
        # Archive dictionary: grid_index -> (fitness, genome)
        self.archive: Dict[Tuple[int, int, int, int], Tuple[float, BehavioralGenome]] = {}

    def get_grid_index(self, descriptor: PhenotypicDescriptor) -> Tuple[int, int, int, int]:
        """
        Maps a 4D continuous phenotypic coordinate to discrete bin indices in O(1).
        """
        vals = (
            descriptor.mean_velocity,
            descriptor.curvature_entropy,
            descriptor.submovement_ratio,
            descriptor.fitts_id_deviation,
        )

        indices: List[int] = []
        for i in range(4):
            low, high = self.ranges[i]
            val = max(low, min(high, vals[i]))
            span = max(1e-5, high - low)
            num_b = self.bins[i]
            idx = int(((val - low) / span) * num_b)
            if idx >= num_b:
                idx = num_b - 1
            indices.append(idx)

        return (indices[0], indices[1], indices[2], indices[3])

    def add(
        self,
        genome: BehavioralGenome,
        descriptor: PhenotypicDescriptor,
        fitness: float,
    ) -> bool:
        """
        Attempts to insert genome into the archive.
        Returns True if a new niche was illuminated or if it replaced an inferior elite.
        """
        key = self.get_grid_index(descriptor)
        if key not in self.archive:
            self.archive[key] = (fitness, genome)
            return True

        curr_fitness, _ = self.archive[key]
        if fitness > curr_fitness:
            self.archive[key] = (fitness, genome)
            return True

        return False

    def get_elite(self, descriptor: PhenotypicDescriptor) -> Optional[BehavioralGenome]:
        """
        Retrieves the elite genome residing at the specified behavioral coordinate.
        Falls back to nearest neighbor if cell is empty.
        """
        key = self.get_grid_index(descriptor)
        if key in self.archive:
            return self.archive[key][1]

        if not self.archive:
            return None

        # Nearest neighbor search in grid space
        best_dist = float("inf")
        best_genome: Optional[BehavioralGenome] = None

        for existing_key, (_, genome) in self.archive.items():
            dist = sum((existing_key[i] - key[i]) ** 2 for i in range(4))
            if dist < best_dist:
                best_dist = dist
                best_genome = genome

        return best_genome

    def sample_random_elite(self) -> BehavioralGenome:
        """
        Samples a random elite from the populated archive.
        """
        if not self.archive:
            return BehavioralGenome()
        _, genome = random.choice(list(self.archive.values()))
        return genome

    @staticmethod
    def mutate_genome(genome: BehavioralGenome, mutation_rate: float = 0.25) -> BehavioralGenome:
        """
        Applies polynomial perturbation within biological validity bounds.
        """
        vec = genome.to_vector()
        new_vec: List[float] = []

        # Parameter valid physiological bounds (min, max)
        bounds = [
            (0.080, 0.240),   # fitts_a
            (0.110, 0.280),   # fitts_b
            (0.00005, 0.0005),# sdn_k
            (0.30, 2.20),     # tremor_amp
            (7.5, 12.5),      # tremor_freq
            (-0.90, -0.40),   # stroke_mu
            (0.20, 0.55),     # stroke_sigma
            (0.65, 0.95),     # stroke_ratio
            (3.80, 5.20),     # dwell_mu
            (0.12, 0.38),     # dwell_sigma
            (4.10, 5.60),     # flight_mu
            (0.15, 0.45),     # flight_sigma
        ]

        for i, val in enumerate(vec):
            if random.random() < mutation_rate:
                low, high = bounds[i]
                span = high - low
                delta = random.gauss(0.0, span * 0.10)
                perturbed = max(low, min(high, val + delta))
                new_vec.append(perturbed)
            else:
                new_vec.append(val)

        return BehavioralGenome.from_vector(new_vec)

    @staticmethod
    def crossover(parent1: BehavioralGenome, parent2: BehavioralGenome) -> BehavioralGenome:
        """
        Simulated Binary Crossover (SBX) between two elite parents.
        """
        v1 = parent1.to_vector()
        v2 = parent2.to_vector()
        child_v: List[float] = []

        eta = 2.0  # Distribution index
        for i in range(len(v1)):
            if random.random() < 0.5:
                u = random.random()
                if u <= 0.5:
                    beta = (2.0 * u) ** (1.0 / (eta + 1.0))
                else:
                    beta = (1.0 / (2.0 * (1.0 - u))) ** (1.0 / (eta + 1.0))

                c1 = 0.5 * ((1.0 + beta) * v1[i] + (1.0 - beta) * v2[i])
                child_v.append(c1)
            else:
                child_v.append(v1[i])

        return BehavioralGenome.from_vector(child_v)

    def total_niches(self) -> int:
        return self.bins[0] * self.bins[1] * self.bins[2] * self.bins[3]

    def illuminated_count(self) -> int:
        return len(self.archive)

    def coverage_ratio(self) -> float:
        total = self.total_niches()
        return len(self.archive) / float(total) if total > 0 else 0.0
