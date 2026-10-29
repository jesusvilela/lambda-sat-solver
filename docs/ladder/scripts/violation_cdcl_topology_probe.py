"""PySAT Glucose4 topology experiment: reproducible held-out CDCL work.

This CLI is separate from lambda-sat's certified solve path. It emits raw
sample/seed, model replay, conflict counts, UNKNOWN censoring, selected
regression features, null-swaps and feature overhead.

Usage:
  python docs/ladder/scripts/violation_cdcl_topology_probe.py \
    --seeds 3 --sizes 48 72 --orbits 2 --budget 2000 --json
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from dataclasses import asdict
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from backend.violation_cdcl_topology import PREDICTORS, topology_benchmark


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seeds",type=int,default=4,help="2..16 independent formula seeds")
    p.add_argument("--sizes",type=int,nargs="+",default=[48,72,96],
                   help="declared variable counts, each divisible by 3")
    p.add_argument("--orbits",type=int,default=3,help="1..8 signed relabelings per CNF")
    p.add_argument("--budget",type=int,default=2000,help="per-call CDCL conflict budget")
    p.add_argument("--swaps",type=int,default=160,help="support-rewiring null attempts")
    p.add_argument("--json",action="store_true")
    args=p.parse_args()
    report=topology_benchmark(seeds=args.seeds,sizes=args.sizes,orbits=args.orbits,
                              budget=args.budget,swaps=args.swaps)
    try:
        pysat_version=version("python-sat")
    except PackageNotFoundError:
        pysat_version="unknown"
    payload={"design":"docs/ladder/VIOLATION_CDCL_TOPOLOGY_PREREG.md",
             "kind":"experimental Glucose4 CDCL statistics, NOT certified λSAT results",
             "instrument":{"python":sys.version.split()[0],
                           "platform":platform.platform(),
                           "python_sat":pysat_version,
                           "solver":"g4",
                           "github_sha":os.environ.get("GITHUB_SHA","unrecorded local")},
             "parameters":vars(args),
             "report":asdict(report)}
    if args.json:
        print(json.dumps(payload,indent=2,sort_keys=True))
        return
    print("Glucose4, fixed conflict budget and independent signed relabelings")
    print("CNFs:",report.total_formulas,"unique labeled:",report.unique_labeled_formulas,
          "unknown calls: %.1f%%"%(100*report.censored_call_fraction))
    print("Unsigned graph, degree and polarity features are included in 'classical'.")
    for k,v in report.aggregate_family_mae.items():
        print(f"  {k:30} log2 capped-conflicts LOFO MAE {v:.4f}")
    if report.size_holdout:
        print("Largest n holdout:", report.size_holdout.label,
              report.size_holdout.capped_conflict_mae)
    print("Nontrivial null coverage: %.1f%%"%(100*report.null_nontrivial_fraction))
    print("Feature cost baseline / +signed+control / CDCL median: "
          f"{report.median_baseline_ms:.3f} / {report.median_signed_increment_ms:.3f} / "
          f"{report.median_cdcl_ms:.3f} ms")
    print("Raw outcomes, missingness and family folds are available with --json.")
    print("No geometry win is required for valid evidence; claims remain bounded.")


if __name__=="__main__":
    main()
