"""Leave-one-family-out ETH x Kakeya *diagnostic* experiment.

Run:
  python docs/ladder/scripts/violation_cross_instance_probe.py --seed-count 24 --replicates 10
  python docs/ladder/scripts/violation_cross_instance_probe.py --json
No SAT/UNSAT certificate or general complexity claim is produced.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path
from statistics import mean, median

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from backend.violation_cross_instance import cross_instance_benchmark, PREDICTORS


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed-count", type=int, default=12,
                   help="2..32 distinct formula seeds for each of six generator families")
    p.add_argument("--replicates", type=int, default=1,
                   help="independent assignment-sampling offsets, 1..30")
    p.add_argument("--sample-budget", type=int, default=48)
    p.add_argument("--rows", type=int, default=6)
    p.add_argument("--candidate-budget", type=int, default=96)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    if not 1 <= args.replicates <= 30:
        p.error("replicates must be within 1..30")
    runs = [
        cross_instance_benchmark(seed_count=args.seed_count, sample_budget=args.sample_budget,
                                 rows=args.rows, candidate_budget=args.candidate_budget,
                                 seed_offset=i)
        for i in range(args.replicates)
    ]
    aggregate = {
        name: {
            "mean_mae_log2_nodes": mean(run.overall_mae_log2[name] for run in runs),
            "min_mae_log2_nodes": min(run.overall_mae_log2[name] for run in runs),
            "max_mae_log2_nodes": max(run.overall_mae_log2[name] for run in runs),
            "replicates_better_than_structural": sum(
                run.overall_mae_log2[name] < run.overall_mae_log2["structure"]
                for run in runs),
        }
        for name in PREDICTORS
    }
    feature_cost_ms = median(run.median_feature_ms for run in runs)
    structure_cost_ms = median(run.median_structural_ms for run in runs)
    dpll_cost_ms = median(run.median_dpll_ms for run in runs)
    payload = {
        "evidence": "M: finite held-out-family predictions of fixed DPLL nodes, not CDCL or Kakeya",
        "canary_provenance": "family stratification and raw degree dispersion; no A4/Z2 group assertions",
        "parameters": vars(args),
        "instances_per_replicate": runs[0].instances,
        "families": [fold.heldout_family for fold in runs[0].folds],
        "aggregate": aggregate,
        "median_feature_cost_ms": feature_cost_ms,
        "median_structural_cost_ms": structure_cost_ms,
        "median_reference_dpll_ms": dpll_cost_ms,
        "runs": [asdict(run) for run in runs],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
        return
    print(f"Instance-held-out probe: {runs[0].instances} toy CNFs per replicate; "
          f"{args.replicates} feature-sampling offsets")
    print(f"{'predictor':37} {'mean MAE':>10} {'vs structure':>13}")
    base = aggregate["structure"]["mean_mae_log2_nodes"]
    for name, row in aggregate.items():
        value = row["mean_mae_log2_nodes"]
        print(f"{name:37} {value:10.4f} {value-base:+13.4f}")
    print(f"Median feature cost {feature_cost_ms:.4f} ms; "
          f"structure {structure_cost_ms:.4f} ms; "
          f"reference DPLL {dpll_cost_ms:.4f} ms")
    print("Null controls, all folds, and seed-level results: use --json.")
    print("These are finite diagnostic statistics; no solver claims follow.")


if __name__ == "__main__":
    main()
