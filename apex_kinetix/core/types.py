"""
Core data models and type definitions for APEX_KINETIX.
Governed by Apex Growth Systems LLC.
Zero external dependencies.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Any
import time


class PlatformType(Enum):
    DARWIN = "darwin"
    LINUX = "linux"
    WINDOWS = "windows"
    MOCK = "mock"


class ActionStatus(Enum):
    PENDING = "pending"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass(frozen=True)
class Point2D:
    x: float
    y: float

    def distance_to(self, other: "Point2D") -> float:
        import math
        return math.hypot(self.x - other.x, self.y - other.y)


@dataclass(frozen=True)
class TargetBounds:
    center: Point2D
    width: float
    height: float

    def contains(self, point: Point2D) -> bool:
        half_w = self.width / 2.0
        half_h = self.height / 2.0
        return (
            self.center.x - half_w <= point.x <= self.center.x + half_w
            and self.center.y - half_h <= point.y <= self.center.y + half_h
        )


@dataclass
class TrajectoryPoint:
    timestamp: float          # Relative time from start (seconds)
    x: float                  # X position (pixels)
    y: float                  # Y position (pixels)
    vx: float                 # Velocity X (pixels/second)
    vy: float                 # Velocity Y (pixels/second)
    ax: float                 # Acceleration X (pixels/second^2)
    ay: float                 # Acceleration Y (pixels/second^2)
    jerk: float               # Magnitude of jerk vector (pixels/second^3)
    curvature: float          # Path curvature kappa (1 / radius)


@dataclass
class BehavioralGenome:
    """
    12-dimensional parameter genome characterizing human motor control.
    """
    fitts_a: float = 0.135            # Intercept latency parameter (seconds)
    fitts_b: float = 0.175            # Slope bandwidth parameter (seconds/bit)
    sdn_k: float = 0.00015            # Harris-Wolpert signal dependent noise scale
    tremor_amp: float = 0.85          # Physiological micro-tremor amplitude (pixels)
    tremor_freq: float = 9.5          # Micro-tremor oscillation frequency (Hz)
    stroke_mu: float = -0.65          # Sigma-lognormal log-time delay parameter
    stroke_sigma: float = 0.35        # Sigma-lognormal log-time dispersion parameter
    stroke_ratio: float = 0.82        # Primary vs secondary corrective stroke amplitude ratio
    dwell_mu: float = 4.45            # Keystroke/click dwell log-mean (median ~85ms)
    dwell_sigma: float = 0.22         # Keystroke/click dwell log-dispersion
    flight_mu: float = 4.78           # Inter-action flight log-mean (median ~119ms)
    flight_sigma: float = 0.28        # Inter-action flight log-dispersion

    def to_vector(self) -> List[float]:
        return [
            self.fitts_a,
            self.fitts_b,
            self.sdn_k,
            self.tremor_amp,
            self.tremor_freq,
            self.stroke_mu,
            self.stroke_sigma,
            self.stroke_ratio,
            self.dwell_mu,
            self.dwell_sigma,
            self.flight_mu,
            self.flight_sigma,
        ]

    @classmethod
    def from_vector(cls, v: List[float]) -> "BehavioralGenome":
        return cls(
            fitts_a=v[0],
            fitts_b=v[1],
            sdn_k=v[2],
            tremor_amp=v[3],
            tremor_freq=v[4],
            stroke_mu=v[5],
            stroke_sigma=v[6],
            stroke_ratio=v[7],
            dwell_mu=v[8],
            dwell_sigma=v[9],
            flight_mu=v[10],
            flight_sigma=v[11],
        )


@dataclass
class PhenotypicDescriptor:
    """
    4-dimensional phenotypic coordinate in the MAP-Elites behavioral space.
    """
    mean_velocity: float              # Average tangential velocity (px/s)
    curvature_entropy: float          # Shannon entropy of path curvature
    submovement_ratio: float          # Ratio of corrective submovement amplitude
    fitts_id_deviation: float         # Normalized deviation from empirical Fitts model


@dataclass
class ActionTransaction:
    transaction_id: str
    target: TargetBounds
    timestamp: float = field(default_factory=time.time)
    status: ActionStatus = ActionStatus.PENDING
    rollback_handler: Optional[Callable[[], bool]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
