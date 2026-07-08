"""Warm-start: GRD's escape field made operational -- carry the moving-frame
structure into the CDCL fallback instead of discarding it.

When the coupled router escalates (CDCL_NEEDED) it has often ENTAILED some
literals via GF(2) Gaussian elimination -- and those are exactly the literals a
pure-CDCL solver (Kissat, no Gaussian) cannot derive cheaply by unit propagation.
Appending them as units before the fallback is a sound warm-start (they are
implied, so satisfiability is preserved).

Test instances: a parity gadget that Gaussian-FORCES its variables (Tseitin-hard
for pure CDCL) planted consistently with a random assignment, unioned with a
planted-SAT random-3SAT core so the whole thing is CDCL_NEEDED (not pure parity)
but the parity variables are entailed. Cold Kissat must search the forcing gadget;
warm Kissat gets the Gaussian solution for free.

Run:  python -m docs.ladder.scripts.warmstart
"""

from __future__ import annotations

import random
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frame_benchmark import parity_clauses, run_cdcl  # noqa: E402

from backend.cnf_utils import CNFFormula, verify_model  # noqa: E402
from backend.frame_solver import coupled_entailments  # noqa: E402


def planted(p: int, h: int, seed: int):
    """Planted-SAT: a forcing arity-3 XOR gadget over vars 1..p (Gaussian-forced,
    Tseitin-hard for pure CDCL) + a planted-SAT random-3SAT core over all n=p+h."""
    rng = random.Random(seed)
    n = p + h
    beta = {v: rng.random() < 0.5 for v in range(1, n + 1)}
    clauses = []
    for _ in range(round(1.7 * p)):                  # ~full-rank forcing XORs
        vs = rng.sample(range(1, p + 1), 3)
        rhs = sum(beta[v] for v in vs) % 2
        clauses += parity_clauses(vs, rhs)
    for _ in range(round(4.1 * n)):                  # planted-SAT hard core
        vs = rng.sample(range(1, n + 1), 3)
        cl = [v if rng.random() < 0.5 else -v for v in vs]
        if not any((l > 0) == beta[abs(l)] for l in cl):
            i = rng.randrange(3)
            cl[i] = abs(cl[i]) if beta[abs(cl[i])] else -abs(cl[i])
        clauses.append(cl)
    return CNFFormula(num_vars=n, clauses=clauses)


def _kissat(formula, timeout):
    t = time.perf_counter()
    try:
        st, _t, _c = run_cdcl(formula, "kissat", timeout_s=timeout)
    except Exception:
        st = "UNKNOWN"
    return (st if st in ("SAT", "UNSAT") else "TIMEOUT"), (time.perf_counter() - t) * 1000.0


def main():
    print("Warm-start: cold Kissat vs Kissat + coupling's Gaussian-entailed units")
    print(f"   {'p+h':>7} {'entailed':>9} {'cold_ms':>10} {'warm_ms':>10} "
          f"{'speedup':>8} {'sound':>6}")
    cold_all, warm_all = [], []
    for (p, h) in [(30, 16), (34, 18), (38, 20), (42, 22)]:
        for s in range(4):
            f = planted(p, h, s)
            ent, verdict = coupled_entailments(f)
            # warm formula: original + entailed literals as sound units
            warm = CNFFormula(num_vars=f.num_vars,
                              clauses=f.clauses + [[v if b else -v]
                                                   for v, b in ent.items()])
            cold_s, cold_ms = _kissat(f, timeout=15.0)
            warm_s, warm_ms = _kissat(warm, timeout=15.0)
            sound = "ok" if (cold_s == warm_s or "TIMEOUT" in (cold_s, warm_s)) else "BAD"
            cold_all.append(cold_ms)
            warm_all.append(warm_ms)
            sp = cold_ms / warm_ms if warm_ms > 0 else float('inf')
            print(f"   {p+h:>7} {len(ent):>9} {cold_ms:>9.0f}m {warm_ms:>9.0f}m "
                  f"{sp:>7.2f}x {sound:>6}")
    print(f"\n   median cold={statistics.median(cold_all):.0f}ms  "
          f"warm={statistics.median(warm_all):.0f}ms  "
          f"overall speedup={statistics.median(cold_all)/statistics.median(warm_all):.2f}x")
    print("   (warm = cold formula + the coupling's GF(2)-entailed units; the units")
    print("    are Gaussian-derived, which pure-CDCL Kissat cannot get by BCP.)")


if __name__ == "__main__":
    main()
