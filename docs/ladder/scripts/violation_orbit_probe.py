"""Reproducible Z2 signed-connection pilot with orbit-averaged DPLL targets.

Run: python docs/ladder/scripts/violation_orbit_probe.py --seeds 12 --offsets 3
The experiment is diagnostic, not a SAT solver or continuous Kakeya theorem.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from statistics import mean, median

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from backend.violation_orbit import PREDICTORS, orbit_holdout_benchmark


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds',type=int,default=12,help='formula seeds per family, 2..32')
    parser.add_argument('--orbits',type=int,default=8,help='signed relabelings, 2..24')
    parser.add_argument('--null-swaps',type=int,default=32,help='margin-preserving attempted swaps')
    parser.add_argument('--offsets',type=int,default=3,help='independent relabeling and null seeds, 1..16')
    parser.add_argument('--json',action='store_true')
    args=parser.parse_args()
    if not 1 <= args.offsets <= 16:
        parser.error('offsets must be in 1..16')
    reports=[orbit_holdout_benchmark(seed_count=args.seeds,repeats=args.orbits,
             null_swaps=args.null_swaps,offset=i) for i in range(args.offsets)]
    summaries={}
    for target in ('overall_raw_mae','overall_orbit_mae'):
        base=[getattr(r,target)['structure'] for r in reports]
        summaries[target]={
            key:{'mean_mae':mean(getattr(r,target)[key] for r in reports),
                 'wins_vs_structural':sum(getattr(r,target)[key] < getattr(r,target)['structure']
                                           for r in reports),
                 'mean_delta_vs_structural':mean(getattr(r,target)[key]-base[i]
                                       for i,r in enumerate(reports))}
            for key in PREDICTORS}
    payload={'claim':'M: finite exploratory DPLL node prediction, not SAT speed or Kakeya bound',
             'parameters':vars(args),'total_formulas':reports[0].formulas,
             'mean_median_orbit_range':mean(r.median_orbit_range for r in reports),
             'mean_fraction_nulls_with_switches':mean(r.fraction_nulls_with_switches for r in reports),
             'median_structural_ms':median(r.median_structure_ms for r in reports),
             'median_feature_ms':median(r.median_feature_ms for r in reports),
             'median_orbit_reference_ms':median(r.median_reference_ms for r in reports),
             'averages':summaries,
             'replicates':[asdict(r) for r in reports]}
    if args.json:
        print(json.dumps(payload,indent=2))
        return
    print('Z2 factor-graph connection; held-out generator families, relabeling-median DPLL nodes')
    print('formulas per offset:',payload['total_formulas'],'; offsets:',args.offsets)
    for target,rows in summaries.items():
        print(target)
        for name,v in rows.items():
            print('  %-35s MAE %.4f ; delta %+0.4f ; wins %d/%d' % (
                name,v['mean_mae'],v['mean_delta_vs_structural'],
                v['wins_vs_structural'],args.offsets))
    print('median log-node orbit range: %.3f ; fraction with mobile sign null: %.3f' % (
          payload['mean_median_orbit_range'],payload['mean_fraction_nulls_with_switches']))
    print('median feature: %.3f ms; baseline: %.3f ms; orbit reference: %.3f ms' % (
          payload['median_feature_ms'],payload['median_structural_ms'],
          payload['median_orbit_reference_ms']))
    print('Note: finite orbit samples are not exactly coordinate invariant; --json has all folds.')


if __name__=='__main__':
    main()
