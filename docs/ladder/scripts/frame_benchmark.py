"""Frame benchmark — does xor_fraction predict the algebraic-vs-CDCL frame advantage?

Tests the corollary of docs/ladder/LEARNINGS.md empirically: on parity-structured
(high xor_fraction) instances the GF(2) frame (Gaussian elimination) is polynomial
while CDCL (Kissat, CaDiCaL) is exponential; on random 3-SAT the reverse holds.

Families span the frame spectrum:
  tseitin   (xor_fraction 1.0, UNSAT)  -- resolution-hard, algebra-easy
  xorsat    (xor_fraction 1.0)         -- pure parity at varying density
  php       (xor_fraction 0.0, UNSAT)  -- both frames hard (counting)
  random3   (xor_fraction ~0.0)        -- CDCL's own frame
  mixed     (0 < xor_fraction < 1)     -- algebraic core may certify UNSAT alone

Outputs JSON + printed tables. Run: python -m docs.ladder.scripts.frame_benchmark
"""
import json
import os
import random
import statistics
import subprocess
import tempfile
import time
from itertools import product

from backend.cnf_utils import CNFFormula
from backend.eval.generators import pigeonhole
from backend.xor_extraction import extract_xors

TIMEOUT = 20.0


# ---------------- generators ----------------
def parity_clauses(vars_, rhs):
    out = []
    for bits in product([0, 1], repeat=len(vars_)):
        if sum(bits) % 2 != rhs:
            out.append([(v if b == 0 else -v) for v, b in zip(vars_, bits)])
    return out


def random_3regular(nv, seed):
    rng = random.Random(seed)
    for _ in range(500):
        stubs = [v for v in range(nv) for _ in range(3)]
        rng.shuffle(stubs)
        edges, ok = set(), True
        for i in range(0, len(stubs), 2):
            a, b = stubs[i], stubs[i + 1]
            if a == b or (min(a, b), max(a, b)) in edges:
                ok = False
                break
            edges.add((min(a, b), max(a, b)))
        if ok and len(edges) == 3 * nv // 2:
            return sorted(edges)
    raise RuntimeError("no 3-regular graph found")


def tseitin(nv, seed):
    edges = random_3regular(nv, seed)
    ev = {e: i + 1 for i, e in enumerate(edges)}
    charge = {v: 0 for v in range(nv)}
    charge[random.Random(seed * 7 + 1).randrange(nv)] = 1  # odd total -> UNSAT
    clauses = []
    for v in range(nv):
        inc = [ev[e] for e in edges if v in e]
        clauses += parity_clauses(inc, charge[v])
    return CNFFormula(num_vars=len(edges), clauses=clauses)


def random_xorsat(n, m, seed, k=3):
    rng = random.Random(seed)
    clauses = []
    for _ in range(m):
        clauses += parity_clauses(rng.sample(range(1, n + 1), k), rng.randint(0, 1))
    return CNFFormula(num_vars=n, clauses=clauses)


def random_3sat(n, m, seed):
    rng = random.Random(seed)
    return CNFFormula(num_vars=n, clauses=[
        [v if rng.random() < .5 else -v for v in rng.sample(range(1, n + 1), 3)]
        for _ in range(m)])


def mixed(n, m_xor, m_rand, seed):
    a = random_xorsat(n, m_xor, seed).clauses
    b = random_3sat(n, m_rand, seed * 3 + 2).clauses
    return CNFFormula(num_vars=n, clauses=a + b)


# ---------------- GF(2) Gaussian on recovered XORs ----------------
def gf2_decide(xors, n):
    """Row-reduce the XOR system over GF(2). 'UNSAT' if inconsistent (a valid
    refutation certificate even for mixed formulas, since XORs are implied);
    'SAT' means the XOR subsystem is consistent (decisive only if it covers
    the whole formula)."""
    rows = []
    for x in xors:
        r = 0
        for v in x.variables:
            r |= (1 << (v - 1))
        if x.rhs:
            r |= (1 << n)
        rows.append(r)
    pivots = {}
    for r in rows:
        cur = r
        while cur:
            lead = (cur & -cur).bit_length() - 1
            if lead == n:
                return 'UNSAT'
            if lead in pivots:
                cur ^= pivots[lead]
            else:
                pivots[lead] = cur
                break
    return 'SAT'


# ---------------- direct CDCL runner ----------------
def run_cdcl(formula, binary, timeout_s=TIMEOUT):
    dimacs = f"p cnf {formula.num_vars} {len(formula.clauses)}\n" + \
             "".join(" ".join(map(str, c)) + " 0\n" for c in formula.clauses)
    with tempfile.NamedTemporaryFile('w', suffix='.cnf', delete=False) as fh:
        fh.write(dimacs)
        path = fh.name
    t0 = time.perf_counter()
    try:
        p = subprocess.run([binary, path], capture_output=True, text=True,
                           timeout=timeout_s)
        dt = time.perf_counter() - t0
        res = {10: 'SAT', 20: 'UNSAT'}.get(p.returncode, 'UNKNOWN')
        conflicts = None
        for line in p.stdout.splitlines():
            if 'conflicts:' in line:
                try:
                    conflicts = int(line.split('conflicts:')[1].split()[0])
                except (ValueError, IndexError):
                    pass
        return res, dt, conflicts
    except subprocess.TimeoutExpired:
        return 'TIMEOUT', float(timeout_s), None
    finally:
        os.unlink(path)


# ---------------- one instance ----------------
def evaluate(family, params, formula, with_cadical=False):
    t0 = time.perf_counter()
    xr = extract_xors(formula)
    detect_ms = (time.perf_counter() - t0) * 1000
    covered = xr.xor_clause_fraction >= 0.999
    g0 = time.perf_counter()
    g = gf2_decide(xr.xors, formula.num_vars) if xr.xors else 'N/A'
    gauss_ms = (time.perf_counter() - g0) * 1000
    # gauss is DECISIVE if it refutes (UNSAT) or if XORs cover the whole formula
    gauss_decisive = (g == 'UNSAT') or (covered and g in ('SAT', 'UNSAT'))
    kres, kt, kc = run_cdcl(formula, "kissat")
    row = dict(family=family, **params, num_vars=formula.num_vars,
               num_clauses=len(formula.clauses),
               xor_fraction=round(xr.xor_clause_fraction, 4),
               num_xors=len(xr.xors), detect_ms=round(detect_ms, 3),
               gauss=g, gauss_ms=round(gauss_ms, 3), gauss_decisive=gauss_decisive,
               kissat=kres, kissat_s=round(kt, 4), kissat_conflicts=kc)
    if with_cadical:
        cres, ct, cc = run_cdcl(formula, "cadical")
        row.update(cadical=cres, cadical_s=round(ct, 4))
    # soundness cross-check: if gauss refutes and kissat decided, they must agree
    if g == 'UNSAT' and kres in ('SAT', 'UNSAT'):
        row['agree'] = (kres == 'UNSAT')
    return row


def main():
    rows = []
    print("=== tseitin (xor 1.0, UNSAT): CDCL exponential vs Gaussian polynomial ===")
    for nv in [30, 40, 50, 60, 70, 80, 90, 100]:
        seeds = range(3) if nv >= 80 else range(5)
        for s in seeds:
            r = evaluate("tseitin", dict(nv=nv, seed=s), tseitin(nv, s),
                         with_cadical=True)
            rows.append(r)
            print(f"  nv={nv:3d} s={s} xor={r['xor_fraction']:.2f} "
                  f"gauss={r['gauss']:5s}{r['gauss_ms']:6.2f}ms | "
                  f"kissat={r['kissat']:7s}{r['kissat_s']:7.2f}s "
                  f"cadical={r.get('cadical'):7s}{r.get('cadical_s'):7.2f}s")

    print("=== xorsat (xor 1.0) across density ===")
    for n in [30, 50, 80]:
        for ratio in [0.7, 0.9, 1.1]:
            for s in range(4):
                f = random_xorsat(n, round(ratio * n), s)
                r = evaluate("xorsat", dict(n=n, ratio=ratio, seed=s), f)
                rows.append(r)
        print(f"  n={n}: " + " ".join(
            f"a{ratio}:{statistics.mean([x['kissat_s'] for x in rows if x['family']=='xorsat' and x.get('n')==n and x.get('ratio')==ratio]):.2f}s"
            for ratio in [0.7, 0.9, 1.1]))

    print("=== php (xor 0.0, UNSAT): both frames hard ===")
    for pigeons in [6, 7, 8, 9, 10, 11]:
        cnf, _ = pigeonhole(pigeons)
        r = evaluate("php", dict(pigeons=pigeons), cnf)
        rows.append(r)
        print(f"  PHP({pigeons}->{pigeons-1}) xor={r['xor_fraction']:.2f} "
              f"gauss={r['gauss']:4s} kissat={r['kissat']:7s}{r['kissat_s']:7.2f}s")

    print("=== random3 (xor ~0): CDCL's own frame ===")
    for n in [50, 100, 150]:
        for s in range(4):
            f = random_3sat(n, round(4.26 * n), s)
            rows.append(evaluate("random3", dict(n=n, seed=s), f))
        sub = [x for x in rows if x['family'] == 'random3' and x['n'] == n]
        print(f"  n={n} alpha=4.26: kissat mean {statistics.mean([x['kissat_s'] for x in sub]):.3f}s "
              f"xor_frac {statistics.mean([x['xor_fraction'] for x in sub]):.3f}")

    print("=== mixed (0<xor<1): does the algebraic core certify UNSAT alone? ===")
    for (mx, mr) in [(20, 40), (30, 30), (40, 20)]:
        for s in range(3):
            r = evaluate("mixed", dict(m_xor=mx, m_rand=mr, seed=s),
                         mixed(30, mx, mr, s))
            rows.append(r)
            print(f"  m_xor={mx} m_rand={mr} s={s} xor={r['xor_fraction']:.2f} "
                  f"gauss={r['gauss']:5s} decisive={r['gauss_decisive']} "
                  f"kissat={r['kissat']:7s}{r['kissat_s']:6.2f}s")

    # ---------- analyses ----------
    def par2(times, results):
        return statistics.mean([t if r != 'TIMEOUT' else 2 * TIMEOUT
                                for t, r in zip(times, results)])

    print("\n=== PORTFOLIO ANALYSIS (all UNSAT-decidable instances) ===")
    dec = [r for r in rows if r['kissat'] in ('SAT', 'UNSAT', 'TIMEOUT')]
    k_times = [r['kissat_s'] for r in dec]
    k_res = [r['kissat'] for r in dec]
    # xor-router: use gauss time when decisive, else kissat
    route_t, route_r = [], []
    vbs_t, vbs_r = [], []
    for r in dec:
        if r['gauss_decisive']:
            route_t.append(r['gauss_ms'] / 1000 + r['detect_ms'] / 1000)
            route_r.append(r['gauss'])
            vbs_t.append(min(r['kissat_s'] if r['kissat'] != 'TIMEOUT' else 2 * TIMEOUT,
                             r['gauss_ms'] / 1000))
            vbs_r.append(r['gauss'])
        else:
            route_t.append(r['detect_ms'] / 1000 + r['kissat_s'])
            route_r.append(r['kissat'])
            vbs_t.append(r['kissat_s'])
            vbs_r.append(r['kissat'])
    print(f"  instances: {len(dec)}   timeouts (kissat): {sum(1 for x in k_res if x=='TIMEOUT')}")
    print(f"  PAR-2  kissat-always : {par2(k_times, k_res):8.3f}s")
    print(f"  PAR-2  xor-router    : {par2(route_t, route_r):8.3f}s   "
          f"(detector adds {statistics.mean([r['detect_ms'] for r in dec]):.2f}ms/instance)")
    print(f"  PAR-2  virtual-best  : {par2(vbs_t, vbs_r):8.3f}s")
    # soundness
    checked = [r for r in rows if 'agree' in r]
    print(f"  soundness cross-check: {sum(r['agree'] for r in checked)}/{len(checked)} "
          f"Gaussian-UNSAT verdicts agree with Kissat")

    out = os.path.join(os.path.dirname(__file__), "frame_benchmark_results.json")
    with open(out, "w") as fh:
        json.dump(rows, fh, indent=1)
    print(f"\nwrote {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
