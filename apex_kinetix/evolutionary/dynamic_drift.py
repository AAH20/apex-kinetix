"""
Ornstein-Uhlenbeck Session Drift Engine.
Simulates human session-level cognitive dynamics: fatigue, focus modulation, and inter-trial jitter.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import math
import random
from typing import Tuple
from apex_kinetix.core.types import PhenotypicDescriptor


class OrnsteinUhlenbeckSessionDrift:
    """
    Continuous mean-reverting stochastic process operating over 4D behavioral descriptors.
    Prevents static parameter fingerprinting over long sessions.
    """

    def __init__(
        self,
        mean_state: PhenotypicDescriptor = PhenotypicDescriptor(
            mean_velocity=650.0,
            curvature_entropy=1.45,
            submovement_ratio=0.18,
            fitts_id_deviation=0.06,
        ),
        theta: float = 0.15,      # Mean reversion speed
        sigma: Tuple[float, float, float, float] = (45.0, 0.12, 0.03, 0.015),
    ):
        self.mean_state = mean_state
        self.theta = theta
        self.sigma = sigma
        self.current_state = mean_state

    def step(self, dt: float = 1.0) -> PhenotypicDescriptor:
        """
        Advances the stochastic session state by dt seconds.
        Returns the updated PhenotypicDescriptor.
        """
        # Velocity
        dv = (
            self.theta * (self.mean_state.mean_velocity - self.current_state.mean_velocity) * dt
            + self.sigma[0] * math.sqrt(dt) * random.gauss(0.0, 1.0)
        )
        new_v = max(200.0, min(1800.0, self.current_state.mean_velocity + dv))

        # Curvature entropy
        dh = (
            self.theta * (self.mean_state.curvature_entropy - self.current_state.curvature_entropy) * dt
            + self.sigma[1] * math.sqrt(dt) * random.gauss(0.0, 1.0)
        )
        new_h = max(0.4, min(2.8, self.current_state.curvature_entropy + dh))

        # Submovement ratio
        ds = (
            self.theta * (self.mean_state.submovement_ratio - self.current_state.submovement_ratio) * dt
            + self.sigma[2] * math.sqrt(dt) * random.gauss(0.0, 1.0)
        )
        new_s = max(0.02, min(0.45, self.current_state.submovement_ratio + ds))

        # Fitts ID deviation
        df = (
            self.theta * (self.mean_state.fitts_id_deviation - self.current_state.fitts_id_deviation) * dt
            + self.sigma[3] * math.sqrt(dt) * random.gauss(0.0, 1.0)
        )
        new_f = max(0.01, min(0.25, self.current_state.fitts_id_deviation + df))

        self.current_state = PhenotypicDescriptor(
            mean_velocity=new_v,
            curvature_entropy=new_h,
            submovement_ratio=new_s,
            fitts_id_deviation=new_f,
        )
        return self.current_state
