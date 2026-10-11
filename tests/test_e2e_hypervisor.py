"""
Comprehensive End-to-End (E2E) Integration Tests for APEX_KINETIX.
Validates complete closed-loop execution: trajectory planning, outside-in dispatch,
keystroke typing, transactional safety, and MAP-Elites archive illumination.
Governed by Apex Growth Systems LLC.
"""

import unittest
from apex_kinetix.core.types import ActionStatus, Point2D, TargetBounds
from apex_kinetix.hypervisor import KinetixHypervisor
from apex_kinetix.virtual_hid.mock_hid import MockVirtualHIDDriver


class TestE2EHypervisor(unittest.TestCase):
    def setUp(self):
        self.mock_driver = MockVirtualHIDDriver()
        self.hypervisor = KinetixHypervisor(driver=self.mock_driver, sample_hz=125.0)

    def test_e2e_click_execution(self):
        origin = Point2D(200.0, 150.0)
        target = TargetBounds(center=Point2D(750.0, 480.0), width=80.0, height=35.0)

        tx = self.hypervisor.click_target(origin, target, simulate_timing=False)

        # 1. Assert transaction committed
        self.assertEqual(tx.status, ActionStatus.COMMITTED)

        # 2. Assert events recorded in mock hardware driver
        events = self.mock_driver.events
        self.assertGreater(len(events), 50)

        # Check move events
        move_events = [e for e in events if e[0] == "move"]
        self.assertGreater(len(move_events), 40)
        # Verify first and last move coordinates
        self.assertAlmostEqual(move_events[0][1], origin.x, delta=1.5)
        self.assertAlmostEqual(move_events[0][2], origin.y, delta=1.5)
        self.assertAlmostEqual(move_events[-1][1], target.center.x, delta=1.5)
        self.assertAlmostEqual(move_events[-1][2], target.center.y, delta=1.5)

        # Check mouse down and mouse up events
        mouse_down_events = [e for e in events if e[0] == "mouse_down"]
        mouse_up_events = [e for e in events if e[0] == "mouse_up"]
        self.assertEqual(len(mouse_down_events), 1)
        self.assertEqual(len(mouse_up_events), 1)

    def test_e2e_typing_execution(self):
        text = "Hello Apex Sovereign Systems!"
        self.hypervisor.type_text(text, simulate_timing=False)

        events = self.mock_driver.events
        key_downs = [e for e in events if e[0] == "key_down"]
        key_ups = [e for e in events if e[0] == "key_up"]

        self.assertEqual(len(key_downs), len(text))
        self.assertEqual(len(key_ups), len(text))
        self.assertEqual(len(self.mock_driver.pressed_keys), 0)

    def test_e2e_transactional_rollback(self):
        origin = Point2D(100.0, 100.0)
        target = TargetBounds(center=Point2D(600.0, 400.0), width=50.0, height=30.0)

        rollback_triggered = False

        def on_rollback():
            nonlocal rollback_triggered
            rollback_triggered = True
            return True

        # Synthesize points
        points = self.hypervisor.plan_motion(origin, target)
        # Deliberately distort final point outside target bounds to simulate perturbation / miss
        points[-1].x = 10.0
        points[-1].y = 10.0

        tx = self.hypervisor.execute_trajectory(points, target, rollback_handler=on_rollback)

        # Postcondition should detect miss and execute rollback
        self.assertEqual(tx.status, ActionStatus.ROLLED_BACK)
        self.assertTrue(rollback_triggered)

    def test_e2e_map_elites_illumination(self):
        origin = Point2D(100.0, 100.0)
        # Execute 15 successive diverse clicks to illuminate behavioral archive
        for i in range(15):
            target = TargetBounds(
                center=Point2D(300.0 + i * 40.0, 200.0 + i * 25.0),
                width=50.0,
                height=30.0,
            )
            self.hypervisor.click_target(origin, target, simulate_timing=False)

        diag = self.hypervisor.get_biometric_diagnostics()
        self.assertGreater(diag["archive_illuminated_niches"], 1)
        self.assertGreater(diag["history_transactions"], 10)


if __name__ == "__main__":
    unittest.main()
