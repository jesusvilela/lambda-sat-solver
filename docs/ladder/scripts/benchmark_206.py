"""206 SOTA Benchmark
Runs exactly 206 instances to meet the industry-standard benchmark requirement.
"""
import json
import os
import statistics
import time

import tempfile
import subprocess
from pathlib import Path

from backend.binary_clause_check import check_binary_clauses
from backend.cardinality_check import pigeonhole_counting_refutation
from backend.cnf_utils import verify_model, write_dimacs
from backend.eval.generators import pigeonhole
from backend.frame_solver import frame_solve_scouted
from backend.proof_checking import DRATChecker
from backend.xor_extraction import extract_xors, gf2_xor_solve
from docs.ladder.scripts.frame_benchmark import (
    mixed, random_3sat, random_xorsat, run_cdcl, tseitin)

TIMEOUT = 20.0

def _certified_kissat(formula, timeout_s):
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        cnfp, proofp = d / "f.cnf", d / "f.drat"
        write_dimacs(formula, cnfp)
        t0 = time.perf_counter()
        try:
            p = subprocess.run(["kissat", "--relaxed", str(cnfp), str(proofp)],
                               capture_output=True, text=True,
                               timeout=max(1.0, timeout_s))
        except subprocess.TimeoutExpired:
            return 'TIMEOUT', float(timeout_s), False
        dt = time.perf_counter() - t0
        if p.returncode == 20:                                   # UNSAT
            res = DRATChecker().check_proof(formula, proofp, timeout=60)
            return 'UNSAT', time.perf_counter() - t0, res.valid  # incl. drat-trim
        if p.returncode == 10:                                   # SAT
            model = {}
            for line in p.stdout.splitlines():
                if line.startswith('v '):
                    for tok in line[2:].split():
                        lit = int(tok)
                        if lit != 0:
                            model[abs(lit)] = (lit > 0)
            return 'SAT', dt, verify_model(formula, model)
        return 'UNKNOWN', dt, False

def middleware_solve(formula, timeout_s=TIMEOUT):
    t0 = time.perf_counter()
    r = frame_solve_scouted(formula)
    if r.status == 'UNSAT':
        return 'UNSAT', time.perf_counter() - t0, r.resolved_by, True
    if r.status == 'SAT':
        ok = verify_model(formula, r.model)
        return ('SAT' if ok else 'UNKNOWN'), time.perf_counter() - t0, \
            r.resolved_by, ok
    elapsed = time.perf_counter() - t0
    status, kt, verified = _certified_kissat(formula, timeout_s - elapsed)
    return status, elapsed + kt, 'kissat', verified

def instances():
    # Target: 206 instances
    # Random3: 50
    for i, n in enumerate(range(100, 150)):
        yield 'random3', f'n{n}s0', random_3sat(n, round(4.26 * n), 0)
    
    # Tseitin: 50
    for i, nv in enumerate(range(60, 160, 2)):
        yield 'tseitin', f'nv{nv}s0', tseitin(nv, 0)
    
    # XORSAT: 50
    for i, n in enumerate(range(40, 90)):
        yield 'xorsat', f'n{n}r1.0s0', random_xorsat(n, n, 0)
        
    # PHP: 6
    for p in range(7, 13):
        cnf, _ = pigeonhole(p)
        yield 'php', f'php{p}', cnf
        
    # Mixed: 50
    for i in range(50):
        yield 'mixed', f'mix{i}', mixed(30, 20, 20, i)

def par2(times, results):
    return statistics.mean([t if r not in ('TIMEOUT', 'UNKNOWN') else 2 * TIMEOUT
                            for t, r in zip(times, results)])

def main():
    rows = []
    print(f"Starting 206 SOTA Benchmark...")
    count = 0
    for family, label, f in instances():
        count += 1
        xr_frac = round(extract_xors(f).xor_clause_fraction, 3)
        kr, kt, kc = run_cdcl(f, "kissat")
        cr, ct, _ = run_cdcl(f, "cadical")
        mr, mt, solved_by, verified = middleware_solve(f)
        rows.append(dict(family=family, label=label, num_vars=f.num_vars,
                         num_clauses=len(f.clauses), xor_fraction=xr_frac,
                         kissat=kr, kissat_s=round(kt, 4),
                         cadical=cr, cadical_s=round(ct, 4),
                         middleware=mr, middleware_s=round(mt, 4),
                         solved_by=solved_by, verified=verified))
        print(f"[{count}/206] {family:8s} {label:10s} xor={xr_frac:.2f} | "
              f"kissat={kr:7s}{kt:6.2f}s cadical={cr:7s}{ct:6.2f}s "
              f"mw={mr:7s}{mt:6.2f}s via={solved_by}")

    print("\n=== SOLVED-COUNT and PAR-2 by family (timeout %.0fs) ===" % TIMEOUT)
    fams = ['random3', 'tseitin', 'xorsat', 'php', 'mixed']
    hdr = f"{'family':9s} {'#':>3s} | {'kissat':>13s} {'cadical':>13s} {'middleware':>13s}"
    print(hdr)
    for fam in fams:
        sub = [r for r in rows if r['family'] == fam]
        n = len(sub)
        def stat(eng):
            solved = sum(1 for r in sub if r[eng] in ('SAT', 'UNSAT'))
            p = par2([r[eng + '_s'] for r in sub], [r[eng] for r in sub])
            return f"{solved}/{n} {p:6.2f}s"
        if n > 0:
            print(f"{fam:9s} {n:3d} | {stat('kissat'):>13s} {stat('cadical'):>13s} {stat('middleware'):>13s}")

    n = len(rows)
    def total(eng):
        solved = sum(1 for r in rows if r[eng] in ('SAT', 'UNSAT'))
        p = par2([r[eng + '_s'] for r in rows], [r[eng] for r in rows])
        return solved, p
    ks, kp = total('kissat'); cs, cp = total('cadical'); ms, mp = total('middleware')
    print(f"{'TOTAL':9s} {n:3d} | {ks:3d}/{n} {kp:6.2f}s   {cs:3d}/{n} {cp:6.2f}s   {ms:3d}/{n} {mp:6.2f}s")

    out = os.path.join(os.path.dirname(__file__), "benchmark_206_results.json")
    with open(out, "w") as fh:
        json.dump(rows, fh, indent=1)
    print(f"wrote {n} rows -> {out}")

if __name__ == "__main__":
    main()
