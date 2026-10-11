"""
Unit tests for Plamondon Sigma-Lognormal Stroke Engine.
Governed by Apex Growth Systems LLC.
"""

import unittest
from apex_kinetix.core.types import Point2D, BehavioralGenome
from apex_kinetix.neuromotor.plamondon_sigma import PlamondonEngine, SigmaStroke


class TestPlamondonSigma(unittest.TestCase):
    def test_single_stroke_asymmetry(self):
        stroke = SigmaStroke(
            t0=0.010,
            amplitude=100.0,
            mu=-0.65,
            sigma=0.35,
            theta_start=0.0,
            theta_end=0.0,
        )
        # Evaluates speed across time
        speeds = [stroke.evaluate_velocity(t)[0] for t in [0.05, 0.15, 0.25, 0.50, 0.80]]
        # Confirm velocity rises and falls
        max_speed = max(speeds)
        self.assertGreater(max_speed, 0.0)
        self.assertLess(speeds[-1], max_speed)

    def test_point_to_point_synthesis(self):
        origin = Point2D(120.0, 150.0)
        dest = Point2D(720.0, 550.0)
        duration = 0.65
        genome = BehavioralGenome()

        points = PlamondonEngine.synthesize_point_to_point(
            origin=origin,
            destination=dest,
            duration=duration,
            genome=genome,
            sample_hz=125.0,
        )

        self.assertGreater(len(points), 50)
        # Verify exact docking at start and endpoint
        self.assertAlmostEqual(points[0].x, origin.x, delta=1.0)
        self.assertAlmostEqual(points[0].y, origin.y, delta=1.0)
        self.assertAlmostEqual(points[-1].x, dest.x, delta=1.0)
        self.assertAlmostEqual(points[-1].y, dest.y, delta=1.0)


if __name__ == "__main__":
    unittest.main()
