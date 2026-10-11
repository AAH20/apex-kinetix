"""
Unit tests for Flash and Hogan (1985) Minimum Jerk Kinematic Solver.
Governed by Apex Growth Systems LLC.
"""

import unittest
from apex_kinetix.core.types import Point2D
from apex_kinetix.core.minimum_jerk import MinimumJerkPlanner


class TestMinimumJerk(unittest.TestCase):
    def test_boundary_conditions(self):
        origin = Point2D(100.0, 200.0)
        dest = Point2D(600.0, 800.0)
        duration = 1.0

        # t = 0
        pos0, vel0, acc0, jerk0 = MinimumJerkPlanner.evaluate_1d(origin.x, dest.x, duration, 0.0)
        self.assertAlmostEqual(pos0, origin.x, places=4)
        self.assertAlmostEqual(vel0, 0.0, places=4)
        self.assertAlmostEqual(acc0, 0.0, places=4)

        # t = duration
        posT, velT, accT, jerkT = MinimumJerkPlanner.evaluate_1d(origin.x, dest.x, duration, duration)
        self.assertAlmostEqual(posT, dest.x, places=4)
        self.assertAlmostEqual(velT, 0.0, places=4)
        self.assertAlmostEqual(accT, 0.0, places=4)

    def test_peak_velocity_at_midpoint(self):
        duration = 1.0
        # For Flash & Hogan minimum jerk, maximum velocity occurs at tau = 0.5
        _, vel_mid, _, _ = MinimumJerkPlanner.evaluate_1d(0.0, 100.0, duration, 0.5)
        _, vel_early, _, _ = MinimumJerkPlanner.evaluate_1d(0.0, 100.0, duration, 0.25)
        _, vel_late, _, _ = MinimumJerkPlanner.evaluate_1d(0.0, 100.0, duration, 0.75)

        self.assertGreater(vel_mid, vel_early)
        self.assertGreater(vel_mid, vel_late)
        self.assertAlmostEqual(vel_early, vel_late, places=4)

    def test_generate_trajectory_sampling(self):
        origin = Point2D(50.0, 50.0)
        dest = Point2D(450.0, 350.0)
        duration = 0.8
        sample_hz = 125.0

        points = MinimumJerkPlanner.generate_trajectory(origin, dest, duration, sample_hz)
        self.assertGreaterEqual(len(points), 90)
        self.assertAlmostEqual(points[0].x, origin.x, places=2)
        self.assertAlmostEqual(points[-1].x, dest.x, places=2)
        self.assertAlmostEqual(points[0].y, origin.y, places=2)
        self.assertAlmostEqual(points[-1].y, dest.y, places=2)


if __name__ == "__main__":
    unittest.main()
