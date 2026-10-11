"""
Unit tests for Voss-McCartney Pink Noise and Physiological Tremor.
Governed by Apex Growth Systems LLC.
"""

import unittest
from apex_kinetix.core.types import Point2D, BehavioralGenome
from apex_kinetix.core.minimum_jerk import MinimumJerkPlanner
from apex_kinetix.neuromotor.tremor import PhysiologicalTremorGenerator
from apex_kinetix.neuromotor.pink_noise import VossMcCartneyPinkNoise
from apex_kinetix.benchmarks.spectral_psd import SpectralAnalyzer


class TestNoiseSpectrum(unittest.TestCase):
    def test_pink_noise_generator(self):
        gen = VossMcCartneyPinkNoise(num_octaves=16)
        samples = [gen.sample() for _ in range(500)]
        self.assertEqual(len(samples), 500)
        # Verify finite variance
        variance = sum(s * s for s in samples) / len(samples)
        self.assertGreater(variance, 0.1)
        self.assertLess(variance, 10.0)

    def test_spectral_slope_pink_noise(self):
        origin = Point2D(100.0, 100.0)
        dest = Point2D(800.0, 600.0)
        duration = 1.2
        points = MinimumJerkPlanner.generate_trajectory(origin, dest, duration, sample_hz=250.0)

        # Superimpose pink noise
        pink_points = VossMcCartneyPinkNoise.inject_pink_noise(points, scale=0.50)
        alpha = SpectralAnalyzer.estimate_trajectory_displacement_slope(
            pink_points, points, sample_rate=250.0, freq_band=(2.0, 40.0)
        )

        # Alpha should be in the biological pink noise neighborhood [0.70, 1.45]
        self.assertGreater(alpha, 0.70)
        self.assertLess(alpha, 1.45)

    def test_raw_noise_slope(self):
        gen = VossMcCartneyPinkNoise(num_octaves=16)
        samples = [gen.sample() for _ in range(1024)]
        alpha = SpectralAnalyzer.estimate_spectral_slope(samples, sample_rate=250.0, freq_band=(2.0, 40.0))
        # Direct generator alpha must be close to 1.0
        self.assertGreater(alpha, 0.75)
        self.assertLess(alpha, 1.40)

    def test_tremor_injection(self):
        origin = Point2D(50.0, 50.0)
        dest = Point2D(400.0, 300.0)
        duration = 0.8
        points = MinimumJerkPlanner.generate_trajectory(origin, dest, duration, sample_hz=125.0)

        genome = BehavioralGenome(tremor_amp=1.2, tremor_freq=10.0)
        tremor_points = PhysiologicalTremorGenerator.inject_tremor(points, genome)

        self.assertEqual(len(tremor_points), len(points))
        # Tremor should introduce micro-variations
        diffs = [abs(tremor_points[i].x - points[i].x) for i in range(len(points))]
        self.assertGreater(max(diffs), 0.1)


if __name__ == "__main__":
    unittest.main()
