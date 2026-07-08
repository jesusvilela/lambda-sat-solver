"""Tests for the crystallized frame router (backend/frame_solver.py).

The router is the session's distilled result: one call that decides a formula in
the shallowest sound frame that collapses it, or reports CDCL_NEEDED. These tests
pin the contract -- each frame resolves the family it owns, every verdict is
certified, and a structureless instance honestly falls through.
"""

from itertools import combinations, product

from backend.cnf_utils import CNFFormula, verify_model
from backend.eval.generators import pigeonhole
from backend.frame_solver import (
    coupled_entailments,
    coupling_breath,
    frame_solve,
    frame_solve_coupled,
    frame_solve_guided,
    frame_solve_scouted,
)


def _tseitin_k4():
    """Tseitin on K4 with one odd vertex -> UNSAT; pure parity (GF(2) frame)."""
    edges = list(combinations(range(4), 2))
    ev = {e: i + 1 for i, e in enumerate(edges)}
    charge = {0: 1, 1: 0, 2: 0, 3: 0}  # total charge odd
    clauses = []
    for v in range(4):
        inc = [ev[e] for e in edges if v in e]
        for bits in product([0, 1], repeat=len(inc)):
            if sum(bits) % 2 != charge[v]:
                clauses.append([(l if b else -l) for l, b in zip(inc, bits)])
    return CNFFormula(num_vars=6, clauses=clauses)


class TestFrameRouting:
    def test_tseitin_resolves_in_parity_frame(self):
        r = frame_solve(_tseitin_k4())
        assert r.status == 'UNSAT'
        assert r.resolved_by == 'parity'
        assert r.certified is True
        assert r.model is None

    def test_pigeonhole_resolves_in_counting_frame(self):
        # PHP is counting-shallow / GF(2)-blind: it must land in 'counting',
        # not 'parity' (the parity frame has no XOR structure to bite on).
        php, _ = pigeonhole(4)
        r = frame_solve(php)
        assert r.status == 'UNSAT'
        assert r.resolved_by == 'counting'
        assert r.certified is True

    def test_binary_contradiction_resolves_in_2sat_frame(self):
        # (x1) and (-x1) as binary/unit clauses: the implication frame refutes
        f = CNFFormula(num_vars=2, clauses=[[1, 2], [-1, 2], [1, -2], [-1, -2]])
        r = frame_solve(f)
        assert r.status == 'UNSAT'
        assert r.resolved_by == '2sat'
        assert r.certified is True

    def test_satisfiable_parity_returns_verified_model(self):
        # x1 ^ x2 ^ x3 = 1 (full parity, SAT): decided in 'parity' with a model
        # that is INDEPENDENTLY re-checked against the original CNF.
        f = CNFFormula(num_vars=3,
                       clauses=[[1, 2, 3], [1, -2, -3], [-1, 2, -3], [-1, -2, 3]])
        r = frame_solve(f)
        assert r.status == 'SAT'
        assert r.resolved_by == 'parity'
        assert r.certified is True
        assert r.model is not None
        assert verify_model(f, r.model)          # the certificate is real

    def test_structureless_formula_falls_through_to_cdcl(self):
        # a small satisfiable 3-SAT with no parity/counting/2-SAT collapse:
        # the router must NOT invent a verdict -- it reports CDCL_NEEDED,
        # uncertified, and leaves the decision to the engine.
        f = CNFFormula(num_vars=4,
                       clauses=[[1, 2, 3], [-1, 2, 4], [1, -3, 4], [2, 3, -4]])
        r = frame_solve(f)
        assert r.status == 'CDCL_NEEDED'
        assert r.resolved_by == 'none'
        assert r.certified is False
        assert r.model is None


class TestFrameSoundness:
    def test_every_certified_unsat_is_genuinely_unsatisfiable(self):
        # differential soundness: no certified UNSAT verdict may have a model.
        # Brute-force the small instances the frames claim to refute.
        instances = [
            _tseitin_k4(),
            pigeonhole(3)[0],
            pigeonhole(4)[0],
        ]
        for f in instances:
            r = frame_solve(f)
            assert r.status == 'UNSAT' and r.certified
            # exhaustively confirm unsatisfiability
            assert not _has_model(f)

    def test_every_certified_sat_model_verifies(self):
        # any SAT the router returns must satisfy the original formula
        f = CNFFormula(num_vars=2, clauses=[[1, -2], [-1, 2]])  # x1^x2=0, SAT
        r = frame_solve(f)
        assert r.status == 'SAT' and r.certified
        assert verify_model(f, r.model)


class TestGuidedRouter:
    """The moving-frame router (frame_solve_guided): same certified verdicts as
    frame_solve, reached by one shared parse + structure-directed order."""

    def _battery(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                               / "docs/ladder/scripts"))
        from frame_benchmark import random_3sat, random_xorsat, tseitin
        cases = [_tseitin_k4()]
        for s in (4, 6, 8):
            cases.append(tseitin(s, seed=1))
        for s in (3, 4, 5):
            cases.append(pigeonhole(s)[0])
        for s in range(25):
            cases.append(random_xorsat(16, 16, s))
            cases.append(random_3sat(20, 85, s))
        return cases

    def test_guided_matches_frame_solve(self):
        # differential: identical status + resolved_by on every band; any SAT
        # model the guided router returns must verify.
        for f in self._battery():
            a = frame_solve(f)
            b = frame_solve_guided(f)
            assert (a.status, a.resolved_by) == (b.status, b.resolved_by)
            if b.status == "SAT":
                assert b.certified and verify_model(f, b.model)

    def test_guided_skips_parity_on_unstructured(self):
        # a structureless 3-SAT is CDCL_NEEDED via the guided router too
        f = CNFFormula(num_vars=4,
                       clauses=[[1, 2, 3], [-1, 2, 4], [1, -3, 4], [2, 3, -4]])
        r = frame_solve_guided(f)
        assert r.status == "CDCL_NEEDED" and r.certified is False

    def test_guided_parity_refute_first_no_regression(self):
        # Tseitin still decided in the parity frame (refute-first preserved)
        r = frame_solve_guided(_tseitin_k4())
        assert r.status == "UNSAT" and r.resolved_by == "parity"


class TestCoupledTriple:
    """The coupled three-frame router: exchanges entailed literals across the
    frames (Nelson-Oppen) to decide instances no single frame decides alone."""

    # parity x1^x2^x3=1 (SAT alone) + units forcing all three to 0 (SAT alone):
    # jointly UNSAT only once the units are substituted into the parity system.
    _COUPLED_UNSAT = CNFFormula(num_vars=3, clauses=[
        [1, 2, 3], [1, -2, -3], [-1, 2, -3], [-1, -2, 3],   # x1^x2^x3 = 1
        [-1], [-2], [-3]])                                   # x1=x2=x3=0

    def test_frame_solve_punts_but_coupling_refutes(self):
        assert frame_solve(self._COUPLED_UNSAT).status == "CDCL_NEEDED"
        r = frame_solve_coupled(self._COUPLED_UNSAT)
        assert r.status == "UNSAT" and r.resolved_by == "coupled"
        assert r.certified and _has_model(self._COUPLED_UNSAT) is False

    def test_coupling_finds_sat_with_verified_model(self):
        # parity x1^x2^x3=1 + units x1=1, x2=0  -> parity pins x3=0 -> SAT
        f = CNFFormula(num_vars=3, clauses=[
            [1, 2, 3], [1, -2, -3], [-1, 2, -3], [-1, -2, 3], [1], [-2]])
        assert frame_solve(f).status == "CDCL_NEEDED"
        r = frame_solve_coupled(f)
        assert r.status == "SAT" and r.resolved_by == "coupled"
        assert verify_model(f, r.model)

    def test_single_frame_verdicts_pass_through_unchanged(self):
        # when a single frame decides, coupled == frame_solve, no extra rounds
        for f in (_tseitin_k4(), pigeonhole(5)[0]):
            base = frame_solve(f)
            r = frame_solve_coupled(f)
            assert (r.status, r.resolved_by) == (base.status, base.resolved_by)
            assert r.rounds == 0

    def test_soundness_vs_brute_force_on_random_mixed(self):
        # every non-CDCL coupled verdict must match brute force; SAT verifies
        import random
        from itertools import product
        rng = random.Random(7)
        decided = 0
        for _ in range(150):
            nv = rng.randint(3, 6)
            vs = rng.sample(range(1, nv + 1), 3)
            rhs = rng.randint(0, 1)
            cl = [[(v if b == 0 else -v) for v, b in zip(vs, bits)]
                  for bits in product([0, 1], repeat=3) if sum(bits) % 2 != rhs]
            for _ in range(rng.randint(1, 4)):
                cl.append([rng.choice([-1, 1]) * rng.randint(1, nv)])
            f = CNFFormula(num_vars=nv, clauses=cl)
            r = frame_solve_coupled(f)
            if r.status != "CDCL_NEEDED":
                decided += 1
                assert (r.status == "SAT") == _has_model(f)
                if r.status == "SAT":
                    assert verify_model(f, r.model)
        assert decided > 100          # the coupling decides the large majority


class TestBreathingBordon:
    """The coupling as a dynamical system: it breathes (fixes literals round by
    round) and resonates (settles to a fixpoint)."""

    def test_single_frame_resolves_at_rest(self):
        b = coupling_breath(_tseitin_k4())
        assert b.rounds == 0 and b.breath == [] and b.settled
        assert b.verdict == "UNSAT"

    def test_coupling_breathes_then_settles(self):
        # parity + units: inhale the entailed literals, then settle to UNSAT
        w = CNFFormula(num_vars=3, clauses=[
            [1, 2, 3], [1, -2, -3], [-1, 2, -3], [-1, -2, 3], [-1], [-2], [-3]])
        b = coupling_breath(w)
        assert b.rounds >= 1 and b.amplitude >= 1 and b.settled
        assert b.verdict == "UNSAT"

    def test_entailed_literals_are_sound_warm_start(self):
        # every literal the coupling entails must be IMPLIED: appending them as
        # units preserves satisfiability (a sound warm-start for CDCL). Checked
        # by brute force on small random instances.
        import random
        from itertools import product
        rng = random.Random(5)
        for _ in range(200):
            nv = rng.randint(3, 6)
            cl = [[rng.choice([-1, 1]) * v
                   for v in rng.sample(range(1, nv + 1), rng.randint(1, 3))]
                  for _ in range(rng.randint(2, 12))]
            f = CNFFormula(num_vars=nv, clauses=cl)
            ent, _ = coupled_entailments(f)

            def sat(g):
                return any(verify_model(g, {i + 1: b[i] for i in range(g.num_vars)})
                           for b in product([False, True], repeat=g.num_vars))
            warm = CNFFormula(num_vars=nv,
                              clauses=cl + [[v if b else -v] for v, b in ent.items()])
            assert sat(f) == sat(warm)            # entailed units preserve SAT/UNSAT

    def test_breath_is_monotone_and_bounded(self):
        # a finite CNF's coupling is monotone (fixed only grows) and always
        # settles -- resonance to rest; no eternal drone here (that is the
        # self-referential lambda layer's epsilon>0).
        w = CNFFormula(num_vars=3, clauses=[
            [1, 2, 3], [1, -2, -3], [-1, 2, -3], [-1, -2, 3], [-1], [-2], [-3]])
        b = coupling_breath(w)
        assert all(b.breath[i] <= b.breath[i + 1] for i in range(len(b.breath) - 1))
        assert b.settled


class TestDecidabilityFold:
    """The escape field is a catastrophe fold, not a smooth Eikonal field: a
    small amount of noise snaps a decided instance across the decidability cliff
    to CDCL_NEEDED (U: finite -> infinite), with a near-empty far side."""

    def test_escape_field_snaps_at_the_fold(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                               / "docs/ladder/scripts"))
        from frame_benchmark import random_xorsat
        from backend.orbifold import hyperbolic_depth
        n = 26
        core = random_xorsat(n, n, 2).clauses
        decided = CNFFormula(num_vars=n, clauses=list(core))
        bt0 = coupling_breath(decided)
        assert bt0.verdict in ("SAT", "UNSAT")          # on the island: decided
        assert hyperbolic_depth(decided) < 1.0          # near the center

        import random
        rng = random.Random(1010)
        noisy = CNFFormula(num_vars=n, clauses=list(core) +
                           [[rng.choice([-1, 1]) * rng.randint(1, n)
                             for _ in range(3)] for _ in range(20)])
        bt1 = coupling_breath(noisy)
        assert bt1.verdict == "CDCL_NEEDED"             # snapped across the fold
        assert hyperbolic_depth(noisy) > 5.0            # jumped toward the boundary
        ent, _ = coupled_entailments(noisy)
        assert len(ent) < n // 3                        # near-empty far side


class TestScoutedGate:
    """frame_solve_scouted must be a strict, sound optimization of the coupled
    router: identical certified verdicts, never losing a frame decision, and
    short-circuiting only genuine tunnel instances."""

    def _corpus(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                              / "docs/ladder/scripts"))
        from frame_benchmark import mixed, random_3sat, random_xorsat, tseitin
        fams = []
        for n in (60, 100, 150):
            for s in range(4):
                fams.append(random_3sat(n, round(4.26 * n), s))
        for nv in (20, 40):
            for s in range(3):
                fams.append(tseitin(nv, s))
        for n in (30, 40):
            for s in range(3):
                fams.append(random_xorsat(n, n, s))
        for p in (5, 6, 7):
            fams.append(pigeonhole(p)[0])
        for s in range(4):
            fams.append(mixed(30, 20, 20, s))
        return fams

    def test_no_verdict_regression_vs_coupled(self):
        for f in self._corpus():
            c = frame_solve_coupled(f)
            sc = frame_solve_scouted(f)
            # decided verdicts must agree exactly
            if sc.status in ("SAT", "UNSAT"):
                assert sc.status == c.status
            # the gate must never drop a frame decision to CDCL
            if c.status in ("SAT", "UNSAT"):
                assert sc.status != "CDCL_NEEDED", f"lost a {c.status} frame win"

    def test_gate_punts_random3_to_cdcl(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                              / "docs/ladder/scripts"))
        from frame_benchmark import random_3sat
        f = random_3sat(120, round(4.26 * 120), 0)
        assert frame_solve_scouted(f).status == "CDCL_NEEDED"

    def test_gate_keeps_structured_wins(self):
        # tseitin (parity) and pigeonhole (counting) must still be decided
        assert frame_solve_scouted(_tseitin_k4()).status == "UNSAT"
        assert frame_solve_scouted(pigeonhole(6)[0]).status == "UNSAT"


def _has_model(f: CNFFormula) -> bool:
    """Brute-force satisfiability check for small formulas (test oracle)."""
    n = f.num_vars
    for bits in product([False, True], repeat=n):
        assign = {i + 1: bits[i] for i in range(n)}
        if verify_model(f, assign):
            return True
    return False
