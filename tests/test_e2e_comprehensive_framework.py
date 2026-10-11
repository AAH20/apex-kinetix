"""
Comprehensive End-to-End (E2E) Testing Framework for APEX_KINETIX.
Stress tests multi-step workflows, adversarial geometric boundaries,
endurance session drift, and adversarial anti-bot classifier resistance.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import math
import random
import unittest
from typing import List, Dict, Any

from apex_kinetix.core.types import (
    ActionStatus,
    Point2D,
    TargetBounds,
    TrajectoryPoint,
    BehavioralGenome,
)
from apex_kinetix.hypervisor import KinetixHypervisor
from apex_kinetix.virtual_hid.mock_hid import MockVirtualHIDDriver
from apex_kinetix.benchmarks.spectral_psd import SpectralAnalyzer
from apex_kinetix.benchmarks.frechet_kinematic import FrechetKinematicDistance


class SyntheticAntiBotClassifier:
    """
    Simulates a production-grade behavioral biometrics classifier (Cloudflare/DataDome style).
    Extracts statistical features and applies heuristic + rule thresholds to detect bots.
    """

    @classmethod
    def classify_trajectory(cls, points: List[TrajectoryPoint]) -> Dict[str, Any]:
        """
        Classifies a single trajectory.
        Returns: {"is_bot": bool, "flags": List[str], "confidence": float}
        """
        flags: List[str] = []

        if len(points) < 5:
            return {"is_bot": True, "flags": ["insufficient_points"], "confidence": 1.0}

        speeds = [math.hypot(p.vx, p.vy) for p in points]
        jerks = [p.jerk for p in points]

        # 1. Check for mechanical zero-acceleration or constant velocity
        speed_std = math.sqrt(sum((s - (sum(speeds) / len(speeds))) ** 2 for s in speeds) / len(speeds))
        if speed_std < 5.0:
            flags.append("constant_velocity_linear_bot")

        # 2. Check for missing start/end deceleration
        if speeds[0] > 100.0 or speeds[-1] > 100.0:
            flags.append("teleportation_abrupt_boundary")

        # 3. Check for perfectly identical inter-point steps (linear interpolation)
        diffs = [abs(points[i].x - points[i - 1].x) for i in range(1, len(points))]
        diff_variance = sum((d - (sum(diffs) / len(diffs))) ** 2 for d in diffs) / len(diffs)
        if diff_variance < 1e-4:
            flags.append("deterministic_linear_interpolation")

        # 4. Check for zero jerk variance (Bezier spline without neuromuscular tremor)
        jerk_std = math.sqrt(sum((j - (sum(jerks) / len(jerks))) ** 2 for j in jerks) / len(jerks))
        if jerk_std < 1.0:
            flags.append("unrealistic_zero_jerk_synthetic_spline")

        is_bot = len(flags) > 0
        confidence = 0.95 if is_bot else 0.05
        return {"is_bot": is_bot, "flags": flags, "confidence": confidence}

    @classmethod
    def classify_keystroke_stream(cls, dwells: List[float], flights: List[float]) -> Dict[str, Any]:
        """
        Classifies typing cadence for mechanical timing regularity.
        """
        flags: List[str] = []
        if len(dwells) >= 5:
            dwell_std = math.sqrt(sum((d - (sum(dwells) / len(dwells))) ** 2 for d in dwells) / len(dwells))
            if dwell_std < 0.002:  # Less than 2ms std dev
                flags.append("robotic_fixed_keystroke_dwell")

        if len(flights) >= 5:
            flight_std = math.sqrt(sum((f - (sum(flights) / len(flights))) ** 2 for f in flights) / len(flights))
            if flight_std < 0.002:
                flags.append("robotic_fixed_keystroke_flight")

        is_bot = len(flags) > 0
        return {"is_bot": is_bot, "flags": flags, "confidence": 0.90 if is_bot else 0.05}


class TestComprehensiveE2EFramework(unittest.TestCase):
    def setUp(self):
        self.mock_driver = MockVirtualHIDDriver()
        self.hypervisor = KinetixHypervisor(driver=self.mock_driver, sample_hz=125.0)

    def test_e2e_multi_step_form_workflow(self):
        """
        Scenario: Complete synthetic form submission workflow:
        1. Click username field -> Type username
        2. Click password field -> Type password
        3. Click submit button -> Confirm transaction
        """
        user_field = TargetBounds(center=Point2D(400.0, 250.0), width=180.0, height=35.0)
        pass_field = TargetBounds(center=Point2D(400.0, 320.0), width=180.0, height=35.0)
        submit_btn = TargetBounds(center=Point2D(400.0, 400.0), width=120.0, height=40.0)

        cursor = Point2D(100.0, 100.0)

        # Step 1: Username
        tx1 = self.hypervisor.click_target(cursor, user_field)
        self.assertEqual(tx1.status, ActionStatus.COMMITTED)
        self.hypervisor.type_text("apex_operator")
        cursor = user_field.center

        # Step 2: Password
        tx2 = self.hypervisor.click_target(cursor, pass_field)
        self.assertEqual(tx2.status, ActionStatus.COMMITTED)
        self.hypervisor.type_text("SovereignSystems2026!")
        cursor = pass_field.center

        # Step 3: Submit
        tx3 = self.hypervisor.click_target(cursor, submit_btn)
        self.assertEqual(tx3.status, ActionStatus.COMMITTED)

        # Verify all events recorded in hardware stream
        events = self.mock_driver.events
        moves = [e for e in events if e[0] == "move"]
        downs = [e for e in events if e[0] == "mouse_down"]
        ups = [e for e in events if e[0] == "mouse_up"]
        keys = [e for e in events if e[0] == "key_down"]

        self.assertGreater(len(moves), 120)
        self.assertEqual(len(downs), 3)
        self.assertEqual(len(ups), 3)
        self.assertEqual(len(keys), len("apex_operator") + len("SovereignSystems2026!"))

    def test_e2e_drag_and_drop_trajectory(self):
        """
        Scenario: Drag-and-drop file transfer or UI slider operation:
        Move -> MouseDown -> Plan smooth loaded trajectory -> MouseUp
        """
        start_point = Point2D(250.0, 200.0)
        drag_target = TargetBounds(center=Point2D(850.0, 600.0), width=80.0, height=80.0)

        # 1. Dock to drag origin
        points_dock = self.hypervisor.plan_motion(Point2D(100.0, 100.0), TargetBounds(start_point, 20.0, 20.0))
        self.hypervisor.execute_trajectory(points_dock, TargetBounds(start_point, 20.0, 20.0))

        # 2. MouseDown to engage grab
        self.mock_driver.mouse_down(button=1)
        self.assertTrue(self.mock_driver.is_mouse_down)

        # 3. Move along trajectory to destination
        points_drag = self.hypervisor.plan_motion(start_point, drag_target)
        tx_drag = self.hypervisor.execute_trajectory(points_drag, drag_target)
        self.assertEqual(tx_drag.status, ActionStatus.COMMITTED)

        # 4. MouseUp to release
        self.mock_driver.mouse_up(button=1)
        self.assertFalse(self.mock_driver.is_mouse_down)

    def test_e2e_adversarial_geometric_boundaries(self):
        """
        Scenario: Extreme target geometries:
        - Tiny target (2px x 2px, High Fitts ID > 9 bits)
        - Screen corner targets ((0,0), (3840, 2160))
        - Huge target (1000px x 600px)
        """
        tiny_target = TargetBounds(center=Point2D(1200.0, 800.0), width=2.0, height=2.0)
        corner_target = TargetBounds(center=Point2D(10.0, 10.0), width=20.0, height=20.0)
        huge_target = TargetBounds(center=Point2D(1920.0, 1080.0), width=1000.0, height=600.0)

        # All must synthesize valid finite coordinates without NaN or Inf
        for target in [tiny_target, corner_target, huge_target]:
            points = self.hypervisor.plan_motion(Point2D(500.0, 500.0), target)
            self.assertGreater(len(points), 20)
            for p in points:
                self.assertFalse(math.isnan(p.x))
                self.assertFalse(math.isnan(p.y))
                self.assertFalse(math.isinf(p.x))
                self.assertFalse(math.isinf(p.y))

            # Execute trajectory and verify arrival inside bounds
            tx = self.hypervisor.execute_trajectory(points, target)
            self.assertEqual(tx.status, ActionStatus.COMMITTED)

    def test_e2e_cascading_rollback_depth(self):
        """
        Scenario: Deep Saga LIFO rollback under cascading failures:
        10 consecutive pending transactions rolled back in exact reverse order.
        """
        order_log: List[int] = []

        def make_handler(idx: int):
            return lambda: order_log.append(idx) or True

        for i in range(10):
            target = TargetBounds(center=Point2D(100.0 + i * 20.0, 100.0), width=40.0, height=40.0)
            points = self.hypervisor.plan_motion(Point2D(0.0, 0.0), target)
            # Intentionally miss to leave transaction pending
            tx = self.hypervisor.execute_trajectory(points, target, rollback_handler=make_handler(i))
            # Keep transaction pending in rollback stack manually
            self.hypervisor.rollback_journal.record_transaction(tx)

        pending = self.hypervisor.rollback_journal.pending_count()
        self.assertGreaterEqual(pending, 10)

        # Execute rollback all
        rolled_back = self.hypervisor.rollback_all()
        self.assertGreaterEqual(rolled_back, 10)

        # Verify strict LIFO ordering: 9 down to 0
        self.assertEqual(order_log, list(range(9, -1, -1)))

    def test_e2e_adversarial_classifier_immunity(self):
        """
        Scenario: Evaluate 50 distinct trajectories against the synthetic enterprise anti-bot classifier.
        Target: 0% detection rate (100% classified as human).
        """
        bot_detections = 0
        total_trials = 50

        for i in range(total_trials):
            orig = Point2D(random.uniform(50.0, 300.0), random.uniform(50.0, 300.0))
            dest = Point2D(random.uniform(500.0, 1600.0), random.uniform(400.0, 900.0))
            target = TargetBounds(center=dest, width=60.0, height=30.0)

            points = self.hypervisor.plan_motion(orig, target)
            result = SyntheticAntiBotClassifier.classify_trajectory(points)

            if result["is_bot"]:
                bot_detections += 1

        evasion_rate = (total_trials - bot_detections) / float(total_trials)
        self.assertEqual(bot_detections, 0, f"Detected {bot_detections} trajectories as bots")
        self.assertEqual(evasion_rate, 1.0)

    def test_e2e_session_endurance_stability(self):
        """
        Scenario: 250 sequential actions to verify Ornstein-Uhlenbeck drift stability,
        memory bounds, and MAP-Elites continuous illumination without numerical drift.
        """
        curr = Point2D(200.0, 200.0)
        for i in range(250):
            target = TargetBounds(
                center=Point2D(random.uniform(100.0, 1800.0), random.uniform(100.0, 1000.0)),
                width=50.0,
                height=30.0,
            )
            tx = self.hypervisor.click_target(curr, target)
            self.assertEqual(tx.status, ActionStatus.COMMITTED)
            curr = target.center

        diag = self.hypervisor.get_biometric_diagnostics()
        self.assertGreater(diag["archive_illuminated_niches"], 25)
        self.assertEqual(diag["pending_transactions"], 0)
        self.assertEqual(diag["history_transactions"], 250)


if __name__ == "__main__":
    unittest.main()
