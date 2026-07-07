"""Tests for the synthetic observer's hardening organs (backend/observer.py).

Three properties, all against a brute-force truth oracle:
  C  the ambiguous critic measures polysemy (PHP is 2-frame, Tseitin 1-frame).
  E  the erroneous observers are genuinely unsound (witnessed) AND our sound
     adjudicator kills them: it never emits a verdict that agrees with a mutant
     where the mutant is wrong ("A must be harder to fool than what it observes").
  Γ  sound frames never disagree (gluing_defect == 0), a live soundness guard.
"""

import random
from itertools import combinations, product

from backend.cnf_utils import CNFFormula, verify_model
from backend.eval.generators import pigeonhole
from backend.observer import (
    ERRONEOUS_OBSERVERS,
    adjudicate,
    frame_ambiguity,
    gluing_defect,
)


def _brute(f: CNFFormula) -> str:
    for b in product([False, True], repeat=f.num_vars):
        if verify_model(f, {i + 1: b[i] for i in range(f.num_vars)}):
            return "SAT"
    return "UNSAT"


def _tseitin_k4():
    edges = list(combinations(range(4), 2))
    ev = {e: i + 1 for i, e in enumerate(edges)}
    charge = {0: 1, 1: 0, 2: 0, 3: 0}
    clauses = []
    for v in range(4):
        inc = [ev[e] for e in edges if v in e]
        for bits in product([0, 1], repeat=len(inc)):
            if sum(bits) % 2 != charge[v]:
                clauses.append([(l if b else -l) for l, b in zip(inc, bits)])
    return CNFFormula(num_vars=6, clauses=clauses)


def _random_small(rng):
    nv = rng.randint(3, 6)
    m = rng.randint(2, 14)
    cl = []
    for _ in range(m):
        k = rng.randint(1, 3)
        cl.append([rng.choice([-1, 1]) * v for v in rng.sample(range(1, nv + 1), k)])
    return CNFFormula(num_vars=nv, clauses=cl)


class TestAmbiguousCritic:
    def test_pigeonhole_is_polysemous(self):
        # PHP(3->2) is decided by BOTH implication (2 holes -> all binary) and
        # counting: degree >= 2, coherent (they agree it is UNSAT).
        amb = frame_ambiguity(pigeonhole(3)[0])
        assert amb.degree >= 2 and amb.coherent
        assert "counting" in amb.frames

    def test_tseitin_is_single_frame(self):
        amb = frame_ambiguity(_tseitin_k4())
        assert amb.frames == ["parity"] and amb.degree == 1

    def test_structureless_is_frame_void(self):
        # a satisfiable, structureless 3-SAT: no single frame sees it (degree 0)
        f = CNFFormula(num_vars=4,
                       clauses=[[1, 2, 3], [-1, 2, 4], [1, -3, 4], [2, 3, -4]])
        assert frame_ambiguity(f).degree == 0


class TestErroneousObserverVaccine:
    def test_each_mutant_is_genuinely_unsound(self):
        # every erroneous observer must be WRONG on some instance (else it is not
        # a real mutant to inoculate against).
        rng = random.Random(1)
        witnessed = {name: False for name in ERRONEOUS_OBSERVERS}
        pool = [_random_small(rng) for _ in range(400)]
        pool += [_tseitin_k4(), pigeonhole(3)[0], pigeonhole(4)[0]]
        # satisfiable pure-XOR systems: dense parity that is NOT UNSAT -- these
        # expose the overconfident_parity mutant (it cries UNSAT on any dense XOR)
        pool.append(CNFFormula(num_vars=3, clauses=[
            [1, 2, 3], [1, -2, -3], [-1, 2, -3], [-1, -2, 3]]))   # x1^x2^x3=1, SAT
        pool.append(CNFFormula(num_vars=2, clauses=[[1, -2], [-1, 2]]))  # x1^x2=0, SAT
        for f in pool:
            truth = _brute(f)
            for name, e in ERRONEOUS_OBSERVERS.items():
                guess = e(f)
                if guess is not None and guess != truth:
                    witnessed[name] = True
        assert all(witnessed.values()), f"not unsound: {witnessed}"

    def test_sound_adjudicator_kills_every_mutant(self):
        # the defining invariant: wherever a mutant is wrong, our adjudicator
        # must NOT emit that wrong verdict -- either it abstains (escalate) or it
        # gives the truth. It is never fooled where the mutant is.
        rng = random.Random(2)
        for _ in range(500):
            f = _random_small(rng)
            truth = _brute(f)
            v = adjudicate(f)
            if v.status != "CDCL_NEEDED":
                assert v.status == truth            # soundness: never wrong
                if v.status == "SAT":
                    assert verify_model(f, v.model)
            for e in ERRONEOUS_OBSERVERS.values():
                guess = e(f)
                if guess is not None and guess != truth:
                    # the mutant is wrong here; we must not agree with it
                    assert v.status in ("CDCL_NEEDED", truth)
                    assert v.status != guess


class TestGluingAndAdjudication:
    def test_sound_frames_never_disagree(self):
        # Γ: gluing_defect is 0 by soundness -- assert it across a battery.
        rng = random.Random(3)
        for _ in range(500):
            assert gluing_defect(_random_small(rng)) == 0

    def test_adjudication_tiers(self):
        # accept (single frame), repair (coupling), escalate (CDCL)
        assert adjudicate(_tseitin_k4()).action == "accept"
        coupled_unsat = CNFFormula(num_vars=3, clauses=[
            [1, 2, 3], [1, -2, -3], [-1, 2, -3], [-1, -2, 3], [-1], [-2], [-3]])
        assert adjudicate(coupled_unsat).action == "repair"
        structureless = CNFFormula(num_vars=4,
                                   clauses=[[1, 2, 3], [-1, 2, 4], [1, -3, 4]])
        assert adjudicate(structureless).action == "escalate"
