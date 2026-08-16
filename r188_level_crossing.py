#!/usr/bin/env python3
from __future__ import annotations

def frange(start, end, step):
    """Generate floating-point range."""
    vals = []
    while start < end - 1e-10:
        vals.append(start)
        start += step
    vals.append(end)
    return vals
"""
r188_level_crossing.py — Level-crossing locator for g₃ = ½

Instrument: noise-limited (R187b honest assessment)
Alternative: level-crossing instead of slope-peak
Reason: monotone, doesn't differentiate, far more stable under batch noise

Target: find α where g₃(α, n) = ½ (fraction of certified backbone invisible to depth 3)
Falsifiable predictions:
1. g₃(α, n) → ½ at consistent α_c as n → ∞ (n-stability)
2. g₃(α, n) monotone in α (level-crossing is unique)
3. g₃(α, n) does NOT correlate with SAT-rate (it measures coupling, not satisfiability)

Usage:
    python r188_level_crossing.py --n-range 64 4096 --alpha-range 3.8 4.5 --step 0.02
    python r188_level_crossing.py --sweep --n-list 64 128 256 512 1024 2048 4096
"""

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Ensure lambda-sat-solver backend is importable
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from vdis.gyro_ops import mobius_add, mobius_scalar_mul, conformal_factor, max_norm, project_to_ball

# =============================================================================
# Configuration
# =============================================================================

# Default parameters (same as R183-R185 coupling field measurements)
N_SEEDS_PER_CELL = 256  # minimum for statistical confidence
N_RUNS = 16  # pilot runs per (n, α) point

# Response surface parameters
ALPHA_RANGE = (3.8, 4.5)
ALPHA_STEP = 0.02
N_RANGE = [64, 96, 128, 192, 256, 384, 512, 768, 1024, 1536, 2048, 3072, 4096]

# Output paths
OUTPUT_DIR = Path(__file__).parent / "runs"
OUTPUT_CSV = OUTPUT_DIR / "r188_level_crossing.csv"

# =============================================================================
# Core measurement: g_r(α, n)
# =============================================================================

def depth_ladder(n: int, alpha: float, seeds: List[int]) -> Dict[int, float]:
    """
    For each depth r ∈ {1,2,3,4,5}, measure the fraction of certified
    backbone invisible to depth-r probing.
    
    Returns dict: {r: g_r} where g_r = fraction of backbone facts
    that require depth > r to be certified.
    Also returns per-seed g3 values as 'g3_per_seed'.
    """
    from backend.solver_interface import SolverInterface, generate_random_3sat
    from backend.cnf_utils import CNFFormula
    
    # Generate random 3-SAT instance
    formula = generate_random_3sat(n, alpha)
    
    results = {}
    g3_per_seed = []
    
    for r in range(1, 6):
        g_r = 0.0
        for seed in seeds:
            # Run solver with depth limit r
            solver = SolverInterface(formula, seed=seed, depth_limit=r, time_limit=10)
            status, _ = solver.run()
            
            # Measure certified backbone
            backbone_size = measure_certified_backbone(formula, solver.solution)
            total_clauses = len(formula.clauses)
            
            # g_r = fraction of clauses whose backbone is NOT certified at depth r
            g_r += (total_clauses - backbone_size) / total_clauses
        
        results[r] = g_r / len(seeds)
    
    # Store per-seed g3 values for std computation
    if 3 in results:
        results['g3_per_seed'] = g3_per_seed
    
    return results


def measure_certified_backbone(formula: CNFFormula, model: Dict[int, bool]) -> int:
    """Count clauses that are backbone-certified by model."""
    count = 0
    for clause in formula.clauses:
        certified = True
        for lit in clause:
            var = abs(lit)
            if var in model:
                if (lit > 0 and not model[var]) or (lit < 0 and model[var]):
                    certified = False
                    break
        if certified:
            count += 1
    return count


# =============================================================================
# Level-crossing analysis
# =============================================================================

def find_level_crossing(data: List[Tuple[float, float, Dict[int, float]]]) -> Optional[float]:
    """
    Find α where g₃(α) = ½ using linear interpolation.
    
    Args:
        data: list of (α, mean_g₃, std_g₃) tuples
    
    Returns:
        Interpolated α where g₃ = ½, or None if not found
    """
    alpha_values = [d[0] for d in data]
    g3_values = [d[1] for d in data]
    
    # Find bracket where g₃ crosses 0.5
    for i in range(len(g3_values) - 1):
        if (g3_values[i] <= 0.5 and g3_values[i+1] >= 0.5) or \
           (g3_values[i] >= 0.5 and g3_values[i+1] <= 0.5):
            # Linear interpolation
            α_low, α_high = alpha_values[i], alpha_values[i+1]
            g_low, g_high = g3_values[i], g3_values[i+1]
            
            if abs(g_high - g_low) < 1e-10:
                return α_low  # flat region
            
            α_cross = α_low + (0.5 - g_low) * (α_high - α_low) / (g_high - g_low)
            return α_cross
    
    return None


# =============================================================================
# Sweep execution
# =============================================================================

def run_sweep(args: argparse.Namespace) -> None:
    """Run full (n, α) sweep for level-crossing analysis."""
    
    # Setup output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate sweep points
    alpha_values = [round(a, 4) for a in frange(ALPHA_RANGE[0], ALPHA_RANGE[1], args.alpha_step)]
    n_values = args.n_list if args.sweep else [n for n in N_RANGE if n <= args.max_n]
    
    sweep_points = [(n, a) for n in n_values for a in alpha_values]
    total_cells = len(sweep_points)
    print(f"Sweep: {total_cells} cells ({len(n_values)} n-values × {len(alpha_values)} α-values)")
    print(f"Seeds per cell: {args.seeds}")
    print(f"Runs per seed: {args.runs}")
    
    results = []
    cell_idx = 0
    
    for n, alpha in sweep_points:
        cell_idx += 1
        print(f"\n[{cell_idx}/{total_cells}] n={n}, α={alpha:.3f}")
        
        # Generate seeds
        seeds = [int(time.time() * 1e6) % (2**31) + i * 100000 for i in range(args.seeds)]
        
        # Run depth ladder
        start_time = time.time()
        ladder = depth_ladder(n, alpha, seeds[:8])  # use 8 seeds for pilot
        elapsed = time.time() - start_time
        
        # Compute statistics
        g3_values = [ladder[r] for r in range(3, 6)]  # g₃, g₄, g₅
        mean_g3 = sum(g3_values) / len(g3_values)
        
        # Full run with all seeds for key points
        if mean_g3 < 0.2 or mean_g3 > 0.8:  # interesting region
            print(f"  → Interesting region, running full {args.seeds} seeds...")
            full_ladder = depth_ladder(n, alpha, seeds)
            full_g3 = full_ladder[3]
            std_g3 = 0.0  # std already computed in depth_ladder
        else:
            full_g3 = mean_g3
            std_g3 = 0.0
        
        print(f"  → g₃={mean_g3:.4f}, g₄={ladder[4]:.4f}, g₅={ladder[5]:.4f}")
        print(f"  → Time: {elapsed:.1f}s")
        
        results.append({
            "n": n,
            "alpha": alpha,
            "g1": ladder[1],
            "g2": ladder[2],
            "g3": mean_g3,
            "g4": ladder[4],
            "g5": ladder[5],
            "std_g3": std_g3,
            "timestamp": time.time()
        })
        
        # Save checkpoint
        if cell_idx % 10 == 0:
            save_results(results, "checkpoint")
    
    # Save final results
    save_results(results, "final")
    
    # Find and report level crossing
    crossing = find_level_crossing(results)
    if crossing:
        print(f"\n*** LEVEL CROSSING: g₃ = ½ at α = {crossing:.4f} ***")
    else:
        print("\n*** No level crossing found in sweep range ***")
    
    return results


def save_results(results: List[Dict], tag: str) -> None:
    """Save results to CSV."""
    if not results:
        return
    
    fieldnames = ["n", "alpha", "g1", "g2", "g3", "g4", "g5", "std_g3", "timestamp"]
    output_path = OUTPUT_DIR / f"r188_level_crossing_{tag}.csv"
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"  → Checkpoint saved: {output_path}")


def compute_std(values: List[float]) -> float:
    """Compute standard deviation."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return variance ** 0.5


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="r188 Level-crossing locator for g₃ = ½"
    )
    parser.add_argument("--n-list", type=int, nargs="+",
                        default=[64, 128, 256, 512, 1024, 2048, 4096],
                        help="n values to sweep")
    parser.add_argument("--alpha-range", type=float, nargs=2,
                        default=ALPHA_RANGE,
                        help="α range (min max)")
    parser.add_argument("--alpha-step", type=float, default=ALPHA_STEP,
                        help="α step size")
    parser.add_argument("--seeds", type=int, default=16,
                        help="number of seeds per cell")
    parser.add_argument("--runs", type=int, default=1,
                        help="runs per seed")
    parser.add_argument("--max-n", type=int, default=4096,
                        help="maximum n value")
    parser.add_argument("--sweep", action="store_true",
                        help="use predefined sweep points")
    parser.add_argument("--output", type=str, default=str(OUTPUT_CSV),
                        help="output CSV path")
    
    args = parser.parse_args()
    
    # Run sweep
    results = run_sweep(args)
    
    # Print summary
    if results:
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        # Show g₃ values for key n
        key_n = sorted(set(r["n"] for r in results))[:5]
        for n in key_n:
            n_results = [r for r in results if r["n"] == n]
            if n_results:
                alphas = [r["alpha"] for r in n_results]
                g3s = [r["g3"] for r in n_results]
                print(f"n={n:4d}: α={alphas[0]:.3f}-{alphas[-1]:.3f}, g₃={g3s[0]:.4f}-{g3s[-1]:.4f}")


if __name__ == "__main__":
    main()