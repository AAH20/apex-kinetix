"""
Unit tests for Biometric Evaluation Benchmarks (Wasserstein, KS-Test, FKD).
Governed by Apex Growth Systems LLC.
"""

import unittest
from apex_kinetix.core.types import Point2D, BehavioralGenome
from apex_kinetix.neuromotor.plamondon_sigma import PlamondonEngine
from apex_kinetix.neuromotor.tremor import PhysiologicalTremorGenerator
from apex_kinetix.neuromotor.pink_noise import VossMcCartneyPinkNoise
from apex_kinetix.benchmarks.wasserstein import WassersteinMetric
from apex_kinetix.benchmarks.kolmogorov_smirnov import KolmogorovSmirnovTest
from apex_kinetix.benchmarks.frechet_kinematic import FrechetKinematicDistance
from apex_kinetix.benchmarks.dataset_loaders import BenchmarkCorpusLoader


class TestBiometricBenchmarks(unittest.TestCase):
    def test_wasserstein_metric(self):
        sample_a = [10.0, 20.0, 30.0, 40.0]
        sample_b = [12.0, 22.0, 32.0, 42.0]
        w1 = WassersteinMetric.calculate_1d(sample_a, sample_b)
        self.assertAlmostEqual(w1, 2.0, delta=0.5)

    def test_kolmogorov_smirnov_same_distribution(self):
        sample1 = BenchmarkCorpusLoader.load_human_velocity_sample(200)
        sample2 = BenchmarkCorpusLoader.load_human_velocity_sample(200)
        d_stat, p_val = KolmogorovSmirnovTest.calculate_2sample(sample1, sample2)
        # Two random samples from same generator should fail to reject null (p > 0.05)
        self.assertLess(d_stat, 0.20)
        self.assertGreater(p_val, 0.05)

    def test_frechet_kinematic_distance_bound(self):
        origin = Point2D(100.0, 100.0)
        dest1 = Point2D(600.0, 400.0)
        dest2 = Point2D(650.0, 420.0)
        genome = BehavioralGenome()

        # Generate two synthetic trajectories
        p1 = PlamondonEngine.synthesize_point_to_point(origin, dest1, 0.70, genome)
        p1 = PhysiologicalTremorGenerator.inject_tremor(p1, genome)
        p1 = VossMcCartneyPinkNoise.inject_pink_noise(p1)

        p2 = PlamondonEngine.synthesize_point_to_point(origin, dest2, 0.72, genome)
        p2 = PhysiologicalTremorGenerator.inject_tremor(p2, genome)
        p2 = VossMcCartneyPinkNoise.inject_pink_noise(p2)

        emb1 = [FrechetKinematicDistance.extract_feature_vector(p1)]
        emb2 = [FrechetKinematicDistance.extract_feature_vector(p2)]

        fkd = FrechetKinematicDistance.calculate_fkd(emb1, emb2)
        # FKD between similar human-like movements must be well within boundary
        self.assertLess(fkd, 1.45)


if __name__ == "__main__":
    unittest.main()
