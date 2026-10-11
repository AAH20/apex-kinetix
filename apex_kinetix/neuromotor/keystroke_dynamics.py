"""
Digraph-Conditioned Keystroke and Click Dynamics Model.
Implements bivariate log-normal dwell and flight distributions with motor chunking.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import math
import random
from typing import Dict, List, Tuple
from apex_kinetix.core.types import BehavioralGenome


class KeystrokeDynamicsModel:
    """
    Generates human-like keypress and click timing intervals.
    """

    # Common English digraphs that exhibit neuromuscular motor chunking speedups
    MOTOR_CHUNKS: Dict[str, float] = {
        "th": 0.72,
        "he": 0.75,
        "in": 0.74,
        "er": 0.76,
        "an": 0.77,
        "re": 0.78,
        "on": 0.75,
        "at": 0.79,
        "en": 0.77,
        "nd": 0.73,
        "ti": 0.78,
        "es": 0.76,
        "or": 0.77,
        "te": 0.78,
        "of": 0.74,
    }

    @staticmethod
    def sample_lognormal(log_mean: float, log_sigma: float) -> float:
        """
        Samples a duration in seconds from a log-normal distribution.
        Note: log_mean is in ln(milliseconds). Returns seconds.
        """
        # Sample value in milliseconds
        val_ms = math.exp(random.gauss(log_mean, log_sigma))
        # Clamp to biologically plausible bounds (20ms to 900ms)
        clamped_ms = max(20.0, min(900.0, val_ms))
        return clamped_ms / 1000.0

    @classmethod
    def sample_click_dwell(cls, genome: BehavioralGenome) -> float:
        """
        Samples the mouse button press duration (time between MouseDown and MouseUp).
        Median human dwell time is ~85ms.
        """
        return cls.sample_lognormal(genome.dwell_mu, genome.dwell_sigma)

    @classmethod
    def sample_keystroke_sequence(
        cls,
        text: str,
        genome: BehavioralGenome,
    ) -> List[Tuple[str, float, float]]:
        """
        Generates timing for a string: list of (character, dwell_time, flight_to_next_key).
        Durations are in seconds.
        """
        sequence: List[Tuple[str, float, float]] = []
        n = len(text)

        for i, char in enumerate(text):
            dwell = cls.sample_lognormal(genome.dwell_mu, genome.dwell_sigma)

            if i < n - 1:
                digraph = (char + text[i + 1]).lower()
                speedup = cls.MOTOR_CHUNKS.get(digraph, 1.0)
                # Base flight time
                base_flight_ms = math.exp(random.gauss(genome.flight_mu, genome.flight_sigma))
                flight_ms = base_flight_ms * speedup
                flight = max(0.015, min(0.600, flight_ms / 1000.0))
            else:
                flight = 0.0

            sequence.append((char, dwell, flight))

        return sequence
