"""Post-pilot parity-vs-signed-geometry control on disjoint CDCL seeds.

Run:
  python docs/ladder/scripts/violation_cdcl_parity_probe.py \
    --seeds 6 --seed-start 100 --sizes 48 72 96 --orbits 3 --budget 5000 --json
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from dataclasses import asdict
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from backend.violation_cdcl_parity import PREDICTORS,parity_holdout


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seeds",type=int,default=6)
    p.add_argument("--seed-start",type=int,default=100)
    p.add_argument("--sizes",type=int,nargs="+",default=[48,72,96])
    p.add_argument("--orbits",type=int,default=3)
    p.add_argument("--budget",type=int,default=5000)
    p.add_argument("--swaps",type=int,default=160)
    p.add_argument("--json",action="store_true")
    args=p.parse_args()
    result=parity_holdout(seeds=args.seeds,seed_start=args.seed_start,
              sizes=tuple(args.sizes),orbits=args.orbits,
              budget=args.budget,swaps=args.swaps)
    try:
        pysat_version=version("python-sat")
    except PackageNotFoundError:
        pysat_version="unavailable"
    output={"design":"docs/ladder/VIOLATION_CDCL_PARITY_ADDENDUM.md",
            "kind":"post-pilot exploratory GF(2) positive control vs Glucose4",
            "instrument":{"python":sys.version.split()[0],"pysat":pysat_version,
                          "platform":platform.platform(),"github_sha":os.environ.get("GITHUB_SHA","local")},
            "parameters":vars(args),
            "report":asdict(result)}
    if args.json:
        print(json.dumps(output,indent=2,sort_keys=True))
        return
    print("Disjoint-seed GF(2) frame vs signed-topology CDCL prediction")
    print(f"{result.formulas} formulae; seeds {result.seed_start}..{result.seed_start+result.seed_count-1}")
    print("Actual independent algebraic frame:",result.status_counts)
    print(f"Glucose4 censored fraction: {result.censored_call_fraction:.3f}")
    for name,error in result.aggregate_mae.items():
        print(f"  {name:36} LOFO MAE {error:.4f}")
    if result.largest_size_holdout:
        print("Largest n held out:",result.largest_size_holdout.mae_log2_capped_conflicts)
    print(f"Median independent GF2 feature time: {result.median_gf2_ms:.3f} ms; "
          f"Glucose4 call: {result.median_cdcl_ms:.3f} ms")
    print("Machine-readable per-formula gate states and conflicts: use --json.")
    print("No asymptotic SAT, Kakeya or prod-router claims.")


if __name__=="__main__":
    main()
