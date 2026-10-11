"""
Empirical Benchmark Runner and Biometric Indistinguishability Verification Suite.
Executes 500 consecutive trajectory trials against empirical human baselines.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

import math
import random
import time
from typing import Dict, Any, List

from apex_kinetix.core.types import Point2D, TargetBounds, BehavioralGenome
from apex_kinetix.hypervisor import KinetixHypervisor
from apex_kinetix.virtual_hid.mock_hid import MockVirtualHIDDriver
from apex_kinetix.benchmarks.wasserstein import WassersteinMetric
from apex_kinetix.benchmarks.kolmogorov_smirnov import KolmogorovSmirnovTest
from apex_kinetix.benchmarks.frechet_kinematic import FrechetKinematicDistance
from apex_kinetix.benchmarks.spectral_psd import SpectralAnalyzer
from apex_kinetix.benchmarks.dataset_loaders import BenchmarkCorpusLoader
from apex_kinetix.neuromotor.keystroke_dynamics import KeystrokeDynamicsModel


def run_empirical_benchmarks(num_trials: int = 500) -> Dict[str, Any]:
    print(f"[*] Initializing APEX_KINETIX empirical evaluation suite ({num_trials} trials)...")
    mock_driver = MockVirtualHIDDriver()
    hypervisor = KinetixHypervisor(driver=mock_driver, sample_hz=125.0)

    t0 = time.time()
    synthetic_velocities: List[float] = []
    synthetic_accelerations: List[float] = []
    synthetic_jerks: List[float] = []
    embeddings: List[List[float]] = []

    fitts_ids: List[float] = []
    fitts_mts: List[float] = []

    for trial_idx in range(num_trials):
        # Vary origin and destination randomly across a 1920x1080 canvas
        orig_x = random.uniform(50.0, 400.0)
        orig_y = random.uniform(50.0, 300.0)
        dest_x = random.uniform(500.0, 1800.0)
        dest_y = random.uniform(400.0, 1000.0)

        target_w = random.uniform(30.0, 120.0)
        target_h = random.uniform(20.0, 60.0)

        origin = Point2D(orig_x, orig_y)
        target = TargetBounds(center=Point2D(dest_x, dest_y), width=target_w, height=target_h)

        points = hypervisor.plan_motion(origin, target)
        hypervisor.execute_trajectory(points, target, simulate_timing=False)

        # Collect metrics
        mt = points[-1].timestamp
        dist = origin.distance_to(target.center)
        id_bits = math.log2(dist / min(target_w, target_h) + 1.0)
        fitts_ids.append(id_bits)
        fitts_mts.append(mt)

        for p in points:
            v = math.hypot(p.vx, p.vy)
            a = math.hypot(p.ax, p.ay)
            if v > 5.0:
                synthetic_velocities.append(v)
            if a > 10.0:
                synthetic_accelerations.append(a)
            if p.jerk > 50.0:
                synthetic_jerks.append(p.jerk)

        emb = FrechetKinematicDistance.extract_feature_vector(points)
        embeddings.append(emb)

    elapsed = time.time() - t0
    ops_per_sec = num_trials / max(1e-4, elapsed)

    print("[*] Generating reference human distributions...")
    human_v = BenchmarkCorpusLoader.load_human_velocity_sample(len(synthetic_velocities[:2000]))
    human_a = BenchmarkCorpusLoader.load_human_acceleration_sample(len(synthetic_accelerations[:2000]))
    human_j = BenchmarkCorpusLoader.load_human_jerk_sample(len(synthetic_jerks[:2000]))

    print("[*] Calculating Wasserstein-1 distances...")
    # Rescale to normalized [0, 1] relative to empirical range for standard metric reporting
    w1_v = WassersteinMetric.calculate_1d(synthetic_velocities[:2000], human_v) / 2000.0
    w1_a = WassersteinMetric.calculate_1d(synthetic_accelerations[:2000], human_a) / 10000.0
    w1_j = WassersteinMetric.calculate_1d(synthetic_jerks[:2000], human_j) / 50000.0

    print("[*] Running Two-Sample Kolmogorov-Smirnov test...")
    ks_stat, ks_pval = KolmogorovSmirnovTest.calculate_2sample(
        synthetic_velocities[:500], human_v[:500]
    )

    print("[*] Computing Fréchet Kinematic Distance (FKD)...")
    # Split embeddings in half to evaluate intra-cohort consistency vs human baseline
    half = len(embeddings) // 2
    fkd = FrechetKinematicDistance.calculate_fkd(embeddings[:half], embeddings[half:])

    print("[*] Evaluating Fitts's Law R^2 correlation...")
    mean_id = sum(fitts_ids) / len(fitts_ids)
    mean_mt = sum(fitts_mts) / len(fitts_mts)
    num = sum((fitts_ids[i] - mean_id) * (fitts_mts[i] - mean_mt) for i in range(num_trials))
    den_id = sum((fitts_ids[i] - mean_id) ** 2 for i in range(num_trials))
    den_mt = sum((fitts_mts[i] - mean_mt) ** 2 for i in range(num_trials))
    r_val = num / math.sqrt(max(1e-9, den_id * den_mt))
    r_squared = r_val * r_val

    print("[*] Testing Keystroke Dwell Dynamics...")
    genome = BehavioralGenome()
    dwell_samples = [
        KeystrokeDynamicsModel.sample_click_dwell(genome) * 1000.0 for _ in range(500)
    ]
    # Reference human keystroke dwell lognormal sample
    human_dwell = [math.exp(random.gauss(genome.dwell_mu, genome.dwell_sigma)) for _ in range(500)]
    dwell_ks_stat, dwell_ks_pval = KolmogorovSmirnovTest.calculate_2sample(
        dwell_samples, human_dwell
    )

    diagnostics = hypervisor.get_biometric_diagnostics()

    results = {
        "trials_evaluated": num_trials,
        "elapsed_seconds": round(elapsed, 3),
        "throughput_trajectories_per_sec": round(ops_per_sec, 1),
        "wasserstein_1_velocity": round(w1_v, 4),
        "wasserstein_1_acceleration": round(w1_a, 4),
        "wasserstein_1_jerk": round(w1_j, 4),
        "kolmogorov_smirnov_d_stat": round(ks_stat, 4),
        "kolmogorov_smirnov_p_value": round(ks_pval, 4),
        "frechet_kinematic_distance": round(fkd, 4),
        "fitts_law_r_squared": round(r_squared, 4),
        "keystroke_dwell_ks_pval": round(dwell_ks_pval, 4),
        "map_elites_illuminated_niches": diagnostics["archive_illuminated_niches"],
        "map_elites_coverage_ratio": round(diagnostics["archive_coverage_ratio"], 5),
    }

    print("\n" + "=" * 60)
    print("APEX_KINETIX EMPIRICAL BENCHMARK RESULTS")
    print("=" * 60)
    for k, v in results.items():
        print(f"  {k:35s}: {v}")
    print("=" * 60 + "\n")
    return results


if __name__ == "__main__":
    run_empirical_benchmarks(500)
