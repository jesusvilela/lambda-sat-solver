"""The beat-CMS benchmark: the description-driven metasolver vs Kissat, CaDiCaL and
CryptoMiniSat (all live), on a SAT-competition-style mix.

The metasolver (backend/metasolver) reverts the dynamical description into a
dispatch: frame/geometry-sufficient instances decided by a certified frame in ~0 ms,
the rest by DRAT-certified CDCL. The honest question: on a mix that includes the
counting and parity fragments (as real competitions do), does it dominate every
individual solver -- including CryptoMiniSat, the one that also carries a Gaussian
engine and owns parity?

Measured terrain (BEAT_CMS_NOTE.md): CMS is exponential on counting (php10/php12 time
out) and strong on the tunnel (competitive with Kissat/CaDiCaL). So the metasolver's
win is structural: instant where CMS blows up, comparable where CMS is strong.

Run:  python -m docs.ladder.scripts.metasolver_benchmark
"""

import json
import os
import statistics
import time

from backend.cms_wrapper import cms_solve
from backend.eval.generators import pigeonhole
from backend.metasolver import metasolve
from docs.ladder.scripts.frame_benchmark import (
    mixed, random_3sat, random_xorsat, run_cdcl, tseitin)

TIMEOUT = 20.0


def instances():
    for n in (100, 150, 200):
        for s in range(3):
            yield "random3", f"n{n}s{s}", random_3sat(n, round(4.26 * n), s)
    for nv in (60, 80, 100):
        for s in range(3):
            yield "tseitin", f"nv{nv}s{s}", tseitin(nv, s)
    for n in (40, 60):
        for ratio in (0.8, 1.0):
            for s in range(3):
                yield "xorsat", f"n{n}r{ratio}s{s}", random_xorsat(n, round(ratio * n), s)
    for p in (9, 10, 11, 12):
        yield "php", f"php{p}", pigeonhole(p)[0]
    for (mx, mr) in ((25, 25), (35, 15)):
        for s in range(3):
            yield "mixed", f"x{mx}r{mr}s{s}", mixed(35, mx, mr, s)


def par2(times, oks):
    return statistics.mean([t if ok else 2 * TIMEOUT for t, ok in zip(times, oks)])


def _cms(formula):
    r = cms_solve(formula, TIMEOUT)
    return r.status, r.seconds


def main():
    rows = []
    for family, label, f in instances():
        kr, kt, _ = run_cdcl(f, "kissat")
        cr, ct, _ = run_cdcl(f, "cadical")
        cmr, cmt = _cms(f)
        m = metasolve(f, TIMEOUT)
        rows.append(dict(family=family, label=label,
                         kissat=kr, kissat_s=round(kt, 4),
                         cadical=cr, cadical_s=round(ct, 4),
                         cms=cmr, cms_s=round(cmt, 4),
                         meta=m.status, meta_s=round(m.seconds, 4),
                         via=m.strategy, certified=m.certified))
        print(f"  {family:8s} {label:10s} | kissat={kr:7s}{kt:6.2f}s "
              f"cadical={cr:7s}{ct:6.2f}s cms={cmr:7s}{cmt:6.2f}s "
              f"META={m.status:7s}{m.seconds:6.2f}s via={m.strategy}")

    fams = ["random3", "tseitin", "xorsat", "php", "mixed"]
    ok = {"SAT", "UNSAT"}
    print("\n=== SOLVED-COUNT and PAR-2 by family (timeout %.0fs) ===" % TIMEOUT)
    print(f"{'family':9} {'#':>2} | {'kissat':>12} {'cadical':>12} "
          f"{'cms':>12} {'metasolver':>12}")

    def cell(sub, eng):
        solved = sum(1 for r in sub if r[eng] in ok)
        p = par2([r[eng + "_s"] for r in sub], [r[eng] in ok for r in sub])
        return f"{solved}/{len(sub)} {p:6.2f}s"

    for fam in fams:
        sub = [r for r in rows if r["family"] == fam]
        print(f"{fam:9} {len(sub):>2d} | {cell(sub,'kissat'):>12} "
              f"{cell(sub,'cadical'):>12} {cell(sub,'cms'):>12} "
              f"{cell(sub,'meta'):>12}")

    n = len(rows)
    def tot(eng):
        solved = sum(1 for r in rows if r[eng] in ok)
        p = par2([r[eng + "_s"] for r in rows], [r[eng] in ok for r in rows])
        return solved, p
    ks, kp = tot("kissat"); cs, cp = tot("cadical")
    cms_s, cmp = tot("cms"); ms, mp = tot("meta")
    print(f"{'TOTAL':9} {n:>2d} | {ks:>2d}/{n} {kp:5.2f}s  {cs:>2d}/{n} {cp:5.2f}s  "
          f"{cms_s:>2d}/{n} {cmp:5.2f}s  {ms:>2d}/{n} {mp:5.2f}s")

    by_frame = sum(1 for r in rows if r["via"] not in ("kissat", "cadical"))
    certified = sum(1 for r in rows if r["meta"] in ok and r["certified"])
    solved = sum(1 for r in rows if r["meta"] in ok)
    print(f"\nmetasolver decided by a certified frame (no CDCL): {by_frame}/{n}")
    print(f"metasolver verdicts certified: {certified}/{solved} solved")
    print(f"PAR-2 advantage over CMS: {cmp / mp:.1f}x   over Kissat: {kp / mp:.1f}x")

    out = os.path.join(os.path.dirname(__file__), "metasolver_benchmark_results.json")
    with open(out, "w") as fh:
        json.dump(rows, fh, indent=1)
    print(f"wrote {n} rows -> {out}")


if __name__ == "__main__":
    main()
