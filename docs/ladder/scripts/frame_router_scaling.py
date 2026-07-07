"""Scaling benchmark for the crystallized frame router (backend/frame_solver).

The prototype-and-benchmark loop that produced the router: measure where the time
actually goes as the frame grows, in pure Python, no externals. The finding baked
into docs/ladder/METAL_ROADMAP.md:

  * The sound GF(2) *refutation* is near-linear -- ~36 ms end-to-end at 4500
    variables (2-SAT scan + XOR parsing + triangularization to 0 = 1).
  * The full GF(2) *solve* (reduced row-echelon + model reconstruction) is
    superlinear (~1.1 s at 4500 vars) because it back-reduces every basis row.
  * So the router refutes BEFORE it reconstructs: the common UNSAT case stays
    linear, and the RREF cost is paid only when a SAT model is actually needed.

Conclusion: at research scale the Gaussian core is near-free; M4RI / a metal
rewrite is premature. What survives is the ordering, not a speedup of the kernel.

Run:  python -m docs.ladder.scripts.frame_router_scaling
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frame_benchmark import tseitin  # noqa: E402

from backend.binary_clause_check import check_binary_clauses  # noqa: E402
from backend.frame_solver import frame_solve  # noqa: E402
from backend.xor_extraction import (  # noqa: E402
    extract_xors,
    gf2_xor_refutation,
    gf2_xor_solve,
)


def _ms(fn) -> float:
    t = time.perf_counter()
    fn()
    return (time.perf_counter() - t) * 1000.0


def main(sizes=(500, 1000, 2000, 3000)) -> None:
    print("Frame-router scaling on Tseitin (UNSAT, pure parity), pure Python:\n")
    print(f"{'nv':>6} {'vars':>6} {'clauses':>8} "
          f"{'2sat':>7} {'parse':>7} {'refute':>7} {'solve':>8} "
          f"{'router':>7} {'by':>7}")
    for nv in sizes:
        f = tseitin(nv, seed=1)
        t2 = _ms(lambda: check_binary_clauses(f))
        tp = _ms(lambda: extract_xors(f))
        tr = _ms(lambda: gf2_xor_refutation(f))
        ts = _ms(lambda: gf2_xor_solve(f))
        t0 = time.perf_counter()
        r = frame_solve(f)
        troute = (time.perf_counter() - t0) * 1000.0
        print(f"{nv:>6} {f.num_vars:>6} {len(f.clauses):>8} "
              f"{t2:>7.1f} {tp:>7.1f} {tr:>7.1f} {ts:>8.1f} "
              f"{troute:>7.1f} {r.resolved_by:>7}")
    print("\nrouter ~= 2sat + parse + refute (near-linear); the superlinear "
          "'solve' column is the RREF the router avoids on the UNSAT path.")


if __name__ == "__main__":
    main()
