"""Out-searching CryptoMiniSat on the random-3SAT tunnel with the fractal portfolio.

The honest claim I earlier declined to make -- that we beat CMS on unstructured
random-3SAT -- tested. The mechanism is real (Gomes-Selman): CDCL runtime on critically
constrained random-3SAT is HEAVY-TAILED across random seeds, so a parallel seed-
diversified portfolio (a mixed strategy) collapses the tail to its lower envelope. The
meta-metasolver races Kissat across `breadth` seeds + one CaDiCaL -- and NOT CMS -- so a
win is a genuine out-search of CMS, not "run CMS and take the best".

Reported per instance and in total: single Kissat (seed 0), single CMS, and the fractal
portfolio (wall-clock + the honest CPU-cost = arms x wall-clock). PAR-2 over the sweep.

Run:  python -m docs.ladder.scripts.metametasolver_benchmark
"""

import statistics
import time

from backend.cms_wrapper import cms_solve
from backend.metametasolver import metametasolve
from docs.ladder.scripts.frame_benchmark import random_3sat, run_cdcl

TIMEOUT = 30.0
BREADTH = 8


def tunnel_instances():
    # harder random-3SAT band (alpha=4.26), where the heavy tail is visible
    for n in (220, 240, 260, 280):
        for s in range(4):
            yield f"n{n}s{s}", random_3sat(n, round(4.26 * n), s)


def par2(times, oks):
    return statistics.mean([t if ok else 2 * TIMEOUT for t, ok in zip(times, oks)])


def main():
    ok = {"SAT", "UNSAT"}
    rows = []
    print(f"Random-3SAT tunnel: single Kissat vs single CMS vs fractal portfolio "
          f"(breadth={BREADTH}, no CMS in pool)\n")
    print(f"{'inst':10}{'kissat':>10}{'cms':>10}{'MMS wall':>10}{'MMS cpu':>9}"
          f"{'via':>10}  winner")
    for label, f in tunnel_instances():
        kr, kt, _ = run_cdcl(f, "kissat", timeout_s=TIMEOUT)   # same budget as CMS/MMS
        cm = cms_solve(f, TIMEOUT)
        mm = metametasolve(f, breadth=BREADTH, timeout_s=TIMEOUT)
        beat = "MMS<CMS" if (mm.status in ok and mm.seconds < cm.seconds) else "--"
        rows.append((label, kt, kr, cm.seconds, cm.status, mm.seconds, mm.status,
                     mm.winner, mm.cpu_seconds))
        print(f"{label:10}{kt:>10.2f}{cm.seconds:>10.2f}{mm.seconds:>10.2f}"
              f"{mm.cpu_seconds:>9.1f}{mm.winner:>10}  {beat}")

    kt = [r[1] for r in rows]; ko = [r[2] in ok for r in rows]
    ct = [r[3] for r in rows]; co = [r[4] in ok for r in rows]
    mt = [r[5] for r in rows]; mo = [r[6] in ok for r in rows]
    n = len(rows)
    print(f"\nsolved:   kissat {sum(ko)}/{n}   cms {sum(co)}/{n}   MMS {sum(mo)}/{n}")
    print(f"PAR-2:    kissat {par2(kt, ko):.2f}s   cms {par2(ct, co):.2f}s   "
          f"MMS(wall) {par2(mt, mo):.2f}s")
    wins = sum(1 for r in rows if r[6] in ok and r[5] < r[3])
    speedup = par2(ct, co) / max(par2(mt, mo), 1e-9)
    print(f"MMS beats CMS wall-clock on {wins}/{n} instances; "
          f"PAR-2 advantage over CMS: {speedup:.1f}x")
    print(f"\nHonest cost: the portfolio spends ~{BREADTH + 1} cores "
          f"(total CPU PAR-2 ~{par2([r[8] for r in rows], mo):.1f}s) to win wall-clock.")
    print("The win is a mixed strategy collapsing a heavy-tailed pure strategy "
          "(Gomes-Selman), not CMS in disguise -- CMS is not in the pool.")


if __name__ == "__main__":
    main()
