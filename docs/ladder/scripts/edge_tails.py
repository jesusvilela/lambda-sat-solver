"""Edge-tail stress: hammer the tails of the omni distributions.

Four sweeps into the extremes, each checking SOUNDNESS (vs Kissat as oracle, or
brute force when tiny) and measuring where the frames decide vs escalate to CDCL:

  1. PHASE-TRANSITION tail -- random 3-SAT across the clause/variable ratio alpha
     from the easy-SAT tail through the 4.26 hardness ridge to the easy-UNSAT
     tail; where does the frame router escalate, and is it ever wrong?
  2. SYMMETRY tail -- pigeonhole up its high-isotropy tail (counting frame vs
     Kissat, which times out around php12).
  3. COVERAGE tail -- a pure XOR system diluted with random noise, walking the
     parity frame off its decision boundary (coverage 1.0 -> 0).
  4. COUPLING tail -- parity + entailing units jointly UNSAT at growing arity: the
     home of the coupled router, where no single frame decides.

Run:  python -m docs.ladder.scripts.edge_tails
"""

from __future__ import annotations

import random
import sys
import time
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frame_benchmark import random_3sat, random_xorsat, run_cdcl, tseitin  # noqa: E402

from backend.cnf_utils import CNFFormula, verify_model  # noqa: E402
from backend.eval.generators import pigeonhole  # noqa: E402
from backend.frame_solver import frame_solve_coupled  # noqa: E402


def _kissat(formula, timeout=10.0):
    try:
        status, _t, _c = run_cdcl(formula, "kissat", timeout_s=timeout)
        return status
    except Exception:
        return "UNKNOWN"


def _mw(formula):
    t = time.perf_counter()
    r = frame_solve_coupled(formula)
    return r, (time.perf_counter() - t) * 1000.0


def phase_transition_tail():
    print("1. PHASE-TRANSITION tail (random 3-SAT, n=140, alpha sweep):")
    print(f"   {'alpha':>6} {'mw':>12} {'frame':>9} {'ms':>7} {'kissat':>8} {'sound':>6}")
    unsound = 0
    for alpha in (1.0, 2.0, 3.0, 4.0, 4.26, 4.5, 5.0, 6.0, 8.0):
        fr_dec = tot = 0
        worst_ms = 0.0
        agree = "ok"
        for s in range(6):
            f = random_3sat(140, round(alpha * 140), s)
            r, ms = _mw(f)
            worst_ms = max(worst_ms, ms)
            tot += 1
            if r.status != "CDCL_NEEDED":
                fr_dec += 1
            k = _kissat(f)
            if r.status in ("SAT", "UNSAT") and k in ("SAT", "UNSAT") and r.status != k:
                unsound += 1
                agree = "UNSOUND"
        print(f"   {alpha:>6.2f} {'solved':>12} {fr_dec:>4}/{tot:<4} {worst_ms:>7.1f} "
              f"{'(oracle)':>8} {agree:>6}")
    print(f"   -> soundness vs Kissat across the transition: {unsound} disagreements")


def symmetry_tail():
    print("\n2. SYMMETRY tail (pigeonhole, counting frame vs Kissat):")
    print(f"   {'php':>5} {'vars':>5} {'mw':>8} {'mw_ms':>8} {'kissat':>10}")
    for p in range(8, 14):
        f = pigeonhole(p)[0]
        r, ms = _mw(f)
        t = time.perf_counter()
        k = _kissat(f, timeout=6.0)
        kms = (time.perf_counter() - t) * 1000.0
        klabel = f"{k} {kms:.0f}ms" if k != "UNKNOWN" else "TIMEOUT"
        print(f"   php{p:<2} {f.num_vars:>5} {r.status:>8} {ms:>7.2f}ms {klabel:>10}")


def coverage_tail():
    print("\n3. COVERAGE tail (pure XOR diluted with noise -> parity boundary):")
    print(f"   {'noise':>6} {'cover':>6} {'mw':>12} {'frame':>9} {'sound':>6}")
    rng = random.Random(0)
    n = 24
    base = random_xorsat(n, n, 3).clauses            # a full XOR system
    for noise in (0, 2, 5, 10, 20, 40):
        cl = list(base) + [[rng.choice([-1, 1]) * rng.randint(1, n)
                            for _ in range(3)] for _ in range(noise)]
        f = CNFFormula(num_vars=n, clauses=cl)
        r, _ = _mw(f)
        from backend.xor_extraction import extract_xors
        cover = extract_xors(f).xor_clause_fraction
        k = _kissat(f)
        sound = "ok"
        if r.status in ("SAT", "UNSAT") and k in ("SAT", "UNSAT") and r.status != k:
            sound = "UNSOUND"
        print(f"   {noise:>6} {cover:>6.2f} {r.status:>12} {r.resolved_by:>9} {sound:>6}")


def coupling_tail():
    print("\n4. COUPLING tail (parity + units jointly UNSAT; no single frame sees it):")
    print(f"   {'arity':>6} {'mw':>8} {'frame':>9} {'rounds':>7} {'sound':>6}")
    for k in (3, 4, 5, 6, 8, 10):
        # XOR(v1..vk)=1 (SAT alone) + units v_i=0 (SAT alone) -> jointly UNSAT
        clauses = [[(v if b == 0 else -v) for v, b in zip(range(1, k + 1), bits)]
                   for bits in product([0, 1], repeat=k) if sum(bits) % 2 != 1]
        clauses += [[-v] for v in range(1, k + 1)]
        f = CNFFormula(num_vars=k, clauses=clauses)
        r, _ = _mw(f)
        # brute truth (small k)
        truth = "UNSAT"
        for bits in product([False, True], repeat=k):
            if verify_model(f, {i + 1: bits[i] for i in range(k)}):
                truth = "SAT"
                break
        sound = "ok" if (r.status == "CDCL_NEEDED" or r.status == truth) else "UNSOUND"
        print(f"   {k:>6} {r.status:>8} {r.resolved_by:>9} {r.rounds:>7} {sound:>6}")


if __name__ == "__main__":
    phase_transition_tail()
    symmetry_tail()
    coverage_tail()
    coupling_tail()
