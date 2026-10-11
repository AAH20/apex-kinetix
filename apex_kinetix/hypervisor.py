"""
APEX_KINETIX Master Behavioral Hypervisor.
Orchestrates neuromotor trajectory synthesis, Quality-Diversity MAP-Elites archives,
and outside-in Virtual HID event dispatch.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import platform
import time
from typing import Any, Callable, Dict, List, Optional
from apex_kinetix.core.types import (
    ActionStatus,
    ActionTransaction,
    BehavioralGenome,
    PhenotypicDescriptor,
    PlatformType,
    Point2D,
    TargetBounds,
    TrajectoryPoint,
)
from apex_kinetix.core.fitts import FittsModel
from apex_kinetix.neuromotor.plamondon_sigma import PlamondonEngine
from apex_kinetix.neuromotor.sdn_noise import SignalDependentNoiseInjector
from apex_kinetix.neuromotor.tremor import PhysiologicalTremorGenerator
from apex_kinetix.neuromotor.pink_noise import VossMcCartneyPinkNoise
from apex_kinetix.neuromotor.keystroke_dynamics import KeystrokeDynamicsModel
from apex_kinetix.evolutionary.behavioral_descriptors import BehavioralDescriptorExtractor
from apex_kinetix.evolutionary.map_elites import MAPElitesArchive
from apex_kinetix.evolutionary.dynamic_drift import OrnsteinUhlenbeckSessionDrift
from apex_kinetix.safety.transaction import TransactionManager
from apex_kinetix.safety.rollback_journal import RollbackJournal
from apex_kinetix.virtual_hid.base import VirtualHIDDriver
from apex_kinetix.virtual_hid.darwin_cg import DarwinCoreGraphicsDriver
from apex_kinetix.virtual_hid.linux_uinput import LinuxUInputDriver
from apex_kinetix.virtual_hid.mock_hid import MockVirtualHIDDriver


class KinetixHypervisor:
    """
    Sovereign Biomimetic Kinematics and Evolutionary Behavioral Hypervisor.
    """

    def __init__(
        self,
        driver: Optional[VirtualHIDDriver] = None,
        archive: Optional[MAPElitesArchive] = None,
        sample_hz: float = 125.0,
    ):
        self.sample_hz = sample_hz
        self.archive = archive or MAPElitesArchive()
        self.session_drift = OrnsteinUhlenbeckSessionDrift()
        self.rollback_journal = RollbackJournal()

        # Seed initial archive with baseline genome
        base_genome = BehavioralGenome()
        base_desc = PhenotypicDescriptor(
            mean_velocity=600.0,
            curvature_entropy=1.40,
            submovement_ratio=0.18,
            fitts_id_deviation=0.05,
        )
        self.archive.add(base_genome, base_desc, fitness=0.95)

        # Initialize hardware driver
        if driver is not None:
            self.driver = driver
        else:
            sys_plat = platform.system().lower()
            if sys_plat == "darwin":
                self.driver = DarwinCoreGraphicsDriver()
            elif sys_plat == "linux":
                self.driver = LinuxUInputDriver()
            else:
                self.driver = MockVirtualHIDDriver()

    def plan_motion(
        self,
        origin: Point2D,
        target: TargetBounds,
    ) -> List[TrajectoryPoint]:
        """
        Synthesizes a biological-grade point-to-point trajectory to target center.
        Integrates Fitts duration, MAP-Elites genome, Sigma-Lognormal strokes,
        Signal-Dependent Noise, physiological tremor, and 1/f pink noise.
        """
        # 1. Advance session drift
        drift_desc = self.session_drift.step(dt=0.5)

        # 2. Select elite genome from MAP-Elites archive
        genome = self.archive.get_elite(drift_desc)
        if genome is None:
            genome = self.archive.sample_random_elite()

        # 3. Compute Fitts's movement duration
        mt, id_bits = FittsModel.calculate_movement_time(origin, target, genome)

        # 4. Generate Sigma-Lognormal multi-stroke trajectory
        points = PlamondonEngine.synthesize_point_to_point(
            origin=origin,
            destination=target.center,
            duration=mt,
            genome=genome,
            sample_hz=self.sample_hz,
        )

        # 5. Inject Harris-Wolpert Signal-Dependent Noise
        points = SignalDependentNoiseInjector.inject_noise(points, genome)

        # 6. Inject 8-12 Hz physiological micro-tremor
        points = PhysiologicalTremorGenerator.inject_tremor(points, genome)

        # 7. Superimpose 1/f pink noise residuals
        points = VossMcCartneyPinkNoise.inject_pink_noise(points, scale=0.35)

        # 8. Biological Hermite smoothstep docking anchor into target center
        n = len(points)
        if n >= 4:
            dock_steps = max(3, int(n * 0.08))
            target_c = target.center
            for k in range(dock_steps):
                idx = n - dock_steps + k
                alpha = (k + 1) / float(dock_steps)
                # Hermite smoothstep: 3*alpha^2 - 2*alpha^3
                smooth_alpha = 3.0 * (alpha ** 2) - 2.0 * (alpha ** 3)
                points[idx].x = (1.0 - smooth_alpha) * points[idx].x + smooth_alpha * target_c.x
                points[idx].y = (1.0 - smooth_alpha) * points[idx].y + smooth_alpha * target_c.y

            for i in range(n - dock_steps, n):
                dt = points[i].timestamp - points[i - 1].timestamp
                if dt > 1e-6:
                    points[i].vx = (points[i].x - points[i - 1].x) / dt
                    points[i].vy = (points[i].y - points[i - 1].y) / dt

            points[0].vx = 0.0
            points[0].vy = 0.0
            points[0].ax = 0.0
            points[0].ay = 0.0
            points[-1].x = target_c.x
            points[-1].y = target_c.y
            points[-1].vx = 0.0
            points[-1].vy = 0.0
            points[-1].ax = 0.0
            points[-1].ay = 0.0

        # 9. Extract empirical phenotype and update MAP-Elites
        actual_desc = BehavioralDescriptorExtractor.extract(points, expected_fitts_mt=mt)
        # Fitness: reward close Fitts alignment and high curvature entropy
        fitness = max(0.1, 1.0 - (actual_desc.fitts_id_deviation * 1.5))
        self.archive.add(genome, actual_desc, fitness)

        return points

    def execute_trajectory(
        self,
        points: List[TrajectoryPoint],
        target: TargetBounds,
        rollback_handler: Optional[Callable[[], bool]] = None,
        simulate_timing: bool = False,
    ) -> ActionTransaction:
        """
        Dispatches trajectory points outside-in through the OS kernel Virtual HID.
        Manages transactional rollback invariants.
        """
        if not points:
            tx = TransactionManager.create_transaction(target, rollback_handler)
            tx.status = ActionStatus.FAILED
            return tx

        origin = Point2D(points[0].x, points[0].y)
        tx = TransactionManager.create_transaction(target, rollback_handler)

        # Check Pre-condition
        if not TransactionManager.verify_precondition(origin, target):
            tx.status = ActionStatus.FAILED
            return tx

        self.rollback_journal.record_transaction(tx)

        # Stream points to Virtual HID driver
        prev_t = 0.0
        for p in points:
            if simulate_timing and p.timestamp > prev_t:
                sleep_sec = p.timestamp - prev_t
                time.sleep(min(0.010, sleep_sec))
                prev_t = p.timestamp

            self.driver.move_to(p.x, p.y)

        # Check Post-condition: did cursor arrive inside target bounding box?
        final_p = Point2D(points[-1].x, points[-1].y)
        if TransactionManager.verify_postcondition(final_p, target):
            self.rollback_journal.commit_transaction(tx.transaction_id)
            tx.status = ActionStatus.COMMITTED
        else:
            # Postcondition failed -> trigger automatic rollback
            self.rollback_journal.rollback_latest()
            tx.status = ActionStatus.ROLLED_BACK

        return tx

    def click_target(
        self,
        origin: Point2D,
        target: TargetBounds,
        rollback_handler: Optional[Callable[[], bool]] = None,
        simulate_timing: bool = False,
    ) -> ActionTransaction:
        """
        Full end-to-end atomic click operation:
        Plan -> Move -> Dwell -> MouseDown -> Dwell -> MouseUp -> Commit
        """
        points = self.plan_motion(origin, target)
        tx = self.execute_trajectory(points, target, rollback_handler, simulate_timing)

        if tx.status == ActionStatus.COMMITTED:
            genome = self.archive.sample_random_elite()
            dwell_sec = KeystrokeDynamicsModel.sample_click_dwell(genome)

            # Hardware Mouse Down
            self.driver.mouse_down(button=1)
            if simulate_timing:
                time.sleep(dwell_sec)

            # Hardware Mouse Up
            self.driver.mouse_up(button=1)

        return tx

    def type_text(
        self,
        text: str,
        simulate_timing: bool = False,
    ) -> None:
        """
        Types text using digraph-conditioned bivariate lognormal dynamics.
        """
        genome = self.archive.sample_random_elite()
        keystrokes = KeystrokeDynamicsModel.sample_keystroke_sequence(text, genome)

        for char, dwell_sec, flight_sec in keystrokes:
            key_code = ord(char)
            self.driver.send_key(key_code, is_down=True)
            if simulate_timing:
                time.sleep(dwell_sec)
            self.driver.send_key(key_code, is_down=False)
            if simulate_timing and flight_sec > 0.0:
                time.sleep(flight_sec)

    def rollback_latest(self) -> bool:
        return self.rollback_journal.rollback_latest()

    def rollback_all(self) -> int:
        return self.rollback_journal.rollback_all()

    def get_biometric_diagnostics(self) -> Dict[str, Any]:
        """
        Returns real-time status of the MAP-Elites archive and transaction journal.
        """
        return {
            "platform": self.driver.platform.value,
            "archive_total_niches": self.archive.total_niches(),
            "archive_illuminated_niches": self.archive.illuminated_count(),
            "archive_coverage_ratio": self.archive.coverage_ratio(),
            "pending_transactions": self.rollback_journal.pending_count(),
            "history_transactions": self.rollback_journal.history_count(),
        }
