"""Reproducible bounded ETH x Kakeya violation-geometry pilot.

Run: python docs/ladder/scripts/violation_geometry_probe.py [--json]
"""
from __future__ import annotations
import argparse
import json
import random
import sys
from dataclasses import asdict
from itertools import combinations, product
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from backend.cnf_utils import CNFFormula
from backend.violation_geometry import run_bridge_experiment


def xor_cnf(variables, rhs):
    return [[-v if bit else v for v,bit in zip(variables,bits)]
            for bits in product((0,1), repeat=len(variables))
            if sum(bits)%2 != rhs]


def corpus():
    edges=list(combinations(range(4),2))
    ids={edge:j+1 for j,edge in enumerate(edges)}
    k4=[]
    for vertex in range(4):
        inc=tuple(ids[e] for e in edges if vertex in e)
        k4+=xor_cnf(inc,1 if vertex==0 else 0)
    pigeons,holes=4,3
    var=lambda p,h:p*holes+h+1
    php=[[var(p,h) for h in range(holes)] for p in range(pigeons)]
    for p,q in combinations(range(pigeons),2):
        for h in range(holes):
            php.append([-var(p,h),-var(q,h)])
    def rand3(planted):
        rng=random.Random(92)
        clauses=[]
        for _ in range(34):
            vs=rng.sample(range(1,9),3)
            ss=[rng.choice((-1,1)) for _ in vs]
            if planted and all(s==-1 for s in ss):
                ss[0]=1
            clauses.append([s*v for s,v in zip(ss,vs)])
        return CNFFormula(8,clauses)
    return {
        "tseitin-K4-odd": CNFFormula(6,k4),
        "pigeonhole-4to3": CNFFormula(12,php),
        "xor-two-triples": CNFFormula(6,xor_cnf((1,2,3),1)+xor_cnf((4,5,6),0)),
        "random-3SAT": rand3(False),
        "planted-3SAT": rand3(True),
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json",action="store_true")
    parser.add_argument("--split-seed",type=int,default=41)
    parser.add_argument("--candidate-seed",type=int,default=19)
    parser.add_argument("--rows",type=int,default=8)
    parser.add_argument("--weight",type=int,default=3)
    parser.add_argument("--budget",type=int,default=512)
    args=parser.parse_args()
    out={}
    for name,formula in corpus().items():
        out[name]=asdict(run_bridge_experiment(
            formula,max_vars=12,split_seed=args.split_seed,
            candidate_seed=args.candidate_seed,max_rows=args.rows,
            max_weight=args.weight,candidate_budget=args.budget))
    if args.json:
        print(json.dumps({"warning":"finite exploratory pilot, not a Kakeya or SAT complexity theorem",
                          "args":vars(args),"corpus":out},indent=2))
        return
    print("Finite ETH x Kakeya pilot (non-certifying, small-n only)")
    for name,r in out.items():
        nulls=[c["heldout_spurious"] for c in r["controls"]]
        print(f"{name:20} n={r['variables']:2} m={r['clauses']:2} "
              f"#SAT={r['models']:4} rows={len(r['chosen_rows']):2} "
              f"held-out={r['heldout_spurious']:3} "
              f"singleton={r['singleton_heldout_spurious']:3} "
              f"matched-null-mean={sum(nulls)/len(nulls):5.2f} "
              f"GramEig={r['overlap']['top_gram_eigenvalue']:.3f}")
    print("No solver verdicts; parity checks are relaxations unless independently certified.")


if __name__=="__main__":
    main()
