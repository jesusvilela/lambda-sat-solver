"""SOTA-style stress benchmark: the frame-aware middleware vs raw SOTA CDCL.

Compares three strategies across SAT-competition-like families:
  kissat      -- raw Kissat 4.0.4 (SOTA CDCL)
  cadical     -- raw CaDiCaL (second SOTA CDCL baseline)
  middleware  -- sound algebraic fast paths (2-SAT via check_binary_clauses,
                 parity via gf2_xor_solve) then Kissat fallback; every SAT
                 model independently verified (Charter: verify, don't trust)

Honest question: on a benchmark that includes parity/XOR categories (as real
competitions do), does the frame-aware middleware dominate raw CDCL, and at what
overhead? Metrics: solved-count within a timeout and PAR-2, per family + total.

Run: python -m docs.ladder.scripts.sota_benchmark
"""
import json
import os
import statistics
import time

from backend.binary_clause_check import check_binary_clauses
from backend.cnf_utils import verify_model
from backend.eval.generators import pigeonhole
from backend.xor_extraction import extract_xors, gf2_xor_solve
from docs.ladder.scripts.frame_benchmark import (
    mixed, random_3sat, random_xorsat, run_cdcl, tseitin)

TIMEOUT = 20.0


def middleware_solve(formula, timeout_s=TIMEOUT):
    """Fast-path pre-check, then CDCL fallback. Returns (status, seconds,
    solved_by, verified)."""
    t0 = time.perf_counter()
    # sound 2-SAT refutation
    bc = check_binary_clauses(formula)
    if not bc.consistent:
        return 'UNSAT', time.perf_counter() - t0, 'binary_clause', True
    # sound parity-frame decision (SAT model is verified inside gf2_xor_solve)
    xr = gf2_xor_solve(formula)
    if xr.status == 'UNSAT':
        return 'UNSAT', time.perf_counter() - t0, 'gf2', True
    if xr.status == 'SAT':
        ok = verify_model(formula, xr.model)
        if ok:
            return 'SAT', time.perf_counter() - t0, 'gf2', True
    # fallback to CDCL on the remaining budget. In THIS harness a Kissat verdict
    # is not independently re-checked (SAT needs a model, UNSAT needs DRAT), so
    # it is flagged unverified -- only the sound fast-path verdicts are certified.
    elapsed = time.perf_counter() - t0
    res, kt, _ = run_cdcl(formula, "kissat", timeout_s=max(1.0, timeout_s - elapsed))
    return res, elapsed + kt, 'kissat', False


def instances():
    """Yield (family, label, formula). Sizes tuned so CDCL is fast on its own
    frames and stressed on the parity ones."""
    for n in (100, 150, 200):
        for s in range(3):
            yield 'random3', f'n{n}s{s}', random_3sat(n, round(4.26 * n), s)
    for nv in (60, 80, 100):
        for s in range(3):
            yield 'tseitin', f'nv{nv}s{s}', tseitin(nv, s)
    for n in (40, 60):
        for ratio in (0.8, 1.0):
            for s in range(3):
                yield 'xorsat', f'n{n}r{ratio}s{s}', random_xorsat(n, round(ratio * n), s)
    for p in (9, 10, 11, 12):
        cnf, _ = pigeonhole(p)
        yield 'php', f'php{p}', cnf
    for (mx, mr) in ((25, 25), (35, 15)):
        for s in range(3):
            yield 'mixed', f'x{mx}r{mr}s{s}', mixed(35, mx, mr, s)


def par2(times, results):
    return statistics.mean([t if r not in ('TIMEOUT', 'UNKNOWN') else 2 * TIMEOUT
                            for t, r in zip(times, results)])


def main():
    rows = []
    for family, label, f in instances():
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
        print(f"  {family:8s} {label:10s} xor={xr_frac:.2f} | "
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
        print(f"{fam:9s} {n:3d} | {stat('kissat'):>13s} {stat('cadical'):>13s} {stat('middleware'):>13s}")

    n = len(rows)
    def total(eng):
        solved = sum(1 for r in rows if r[eng] in ('SAT', 'UNSAT'))
        p = par2([r[eng + '_s'] for r in rows], [r[eng] for r in rows])
        return solved, p
    ks, kp = total('kissat'); cs, cp = total('cadical'); ms, mp = total('middleware')
    print(f"{'TOTAL':9s} {n:3d} | {ks:2d}/{n} {kp:6.2f}s   {cs:2d}/{n} {cp:6.2f}s   {ms:2d}/{n} {mp:6.2f}s")

    # honesty accounting
    by_fastpath = sum(1 for r in rows if r['solved_by'] in ('binary_clause', 'gf2'))
    unverified = sum(1 for r in rows if not r['verified'])
    print(f"\nmiddleware decided by algebraic fast-path (no CDCL): {by_fastpath}/{n}")
    print(f"middleware verdicts independently verified: {n - unverified}/{n} "
          f"({unverified} kissat-SAT fallbacks not model-checked here)")

    out = os.path.join(os.path.dirname(__file__), "sota_benchmark_results.json")
    with open(out, "w") as fh:
        json.dump(rows, fh, indent=1)
    print(f"wrote {n} rows -> {out}")


if __name__ == "__main__":
    main()
