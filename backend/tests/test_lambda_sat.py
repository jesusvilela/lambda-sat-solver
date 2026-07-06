"""Tests for the Lambda ⊗ SAT fusion (lambda_sat)."""

from backend.lambda_sat import (
    App, BAnd, BConst, BNot, BOr, BVar, Lam,
    beta_normalize, eval_bool, lambda_sat, tseitin_encode)
from backend.cnf_utils import verify_model


class TestBetaAndEval:
    def test_beta_identity(self):
        # (λx. x) True  ->  True
        assert beta_normalize(App(Lam('x', BVar('x')), BConst(True))) == BConst(True)

    def test_beta_application_into_body(self):
        # (λx. x ∧ y) True  ->  True ∧ y
        n = beta_normalize(App(Lam('x', BAnd(BVar('x'), BVar('y'))), BConst(True)))
        assert eval_bool(n, {'y': True}) and not eval_bool(n, {'y': False})

    def test_shadowing_not_captured(self):
        # (λx. (λx. x)) a  ->  λx. x   (inner x not substituted)
        assert beta_normalize(App(Lam('x', Lam('x', BVar('x'))), BConst(True))) \
            == Lam('x', BVar('x'))


class TestLambdaSat:
    def test_sat_with_certified_witness(self):
        # (λx. ¬x) y  ->  ¬y : SAT with y=False, witness re-verified
        r = lambda_sat(App(Lam('x', BNot(BVar('x'))), BVar('y')))
        assert r.status == 'SAT'
        assert r.witness == {'y': False}
        assert eval_bool(beta_normalize(BNot(BVar('y'))), r.witness)

    def test_unsat_contradiction(self):
        # x ∧ ¬x : no assignment makes it true -> UNSAT
        r = lambda_sat(BAnd(BVar('x'), BNot(BVar('x'))))
        assert r.status == 'UNSAT' and r.witness is None

    def test_remainder_links_clauses_to_source(self):
        r = lambda_sat(BOr(BVar('a'), BVar('b')))
        assert r.status == 'SAT'
        # every clause carries a provenance tag (the ghost fiber)
        assert len(r.remainder) == len(r.cnf.clauses)
        assert 'assert-true' in r.remainder.values()
        assert any(v == 'or' for v in r.remainder.values())

    def test_projection_is_faithful(self):
        # the Boolean shadow is SAT iff the source is SAT (equisatisfiable)
        for term in [BAnd(BVar('x'), BNot(BVar('x'))),          # UNSAT
                     BOr(BVar('a'), BNot(BVar('a'))),           # SAT (tautology)
                     App(Lam('x', BAnd(BVar('x'), BVar('y'))), BConst(True))]:
            r = lambda_sat(term)
            assert r.projection_faithful is True

    def test_tseitin_output_satisfiable_matches_eval(self):
        # the CNF projection, when SAT, yields an assignment consistent with eval
        n = beta_normalize(BAnd(BVar('p'), BOr(BVar('q'), BNot(BVar('p')))))
        cnf, remainder, free_ids = tseitin_encode(n)
        # p True, q True satisfies p ∧ (q ∨ ¬p)
        assert eval_bool(n, {'p': True, 'q': True})


class TestMetaResolution:
    def test_parity_sat_resolved_by_gf2_frame(self):
        from backend.lambda_sat import BXor, BVar
        r = lambda_sat(BXor(BVar('a'), BVar('b')))   # a⊕b=1
        assert r.status == 'SAT' and r.resolved_by == 'parity'
        assert eval_bool(BXor(BVar('a'), BVar('b')), r.witness)

    def test_parity_unsat_resolved_by_gf2_frame(self):
        from backend.lambda_sat import BXor, BVar, BAnd, BNot
        # (x⊕y) ∧ ¬(x⊕y): inconsistent parity system
        t = BAnd(BXor(BVar('x'), BVar('y')), BNot(BXor(BVar('x'), BVar('y'))))
        r = lambda_sat(t)
        assert r.status == 'UNSAT' and r.resolved_by == 'parity' and r.witness is None

    def test_odd_cycle_xor_unsat(self):
        from backend.lambda_sat import BXor, BVar, BAnd
        # x⊕y=1, y⊕z=1, x⊕z=1 -> sum gives 0=1 -> UNSAT (Gaussian)
        t = BAnd(BAnd(BXor(BVar('x'), BVar('y')), BXor(BVar('y'), BVar('z'))),
                 BXor(BVar('x'), BVar('z')))
        r = lambda_sat(t)
        assert r.status == 'UNSAT' and r.resolved_by == 'parity'

    def test_reduction_reveals_parity_frame(self):
        # (λf. f⊕g)(x⊕y) β-reduces to (x⊕y)⊕g -> parity only after reduction
        from backend.lambda_sat import BXor, BVar, Lam, App
        r = lambda_sat(App(Lam('f', BXor(BVar('f'), BVar('g'))),
                           BXor(BVar('x'), BVar('y'))))
        assert r.status == 'SAT' and r.resolved_by == 'parity'
        assert sorted(r.free_vars) == ['g', 'x', 'y']

    def test_generic_term_falls_to_direct(self):
        r = lambda_sat(BOr(BVar('a'), BVar('b')))
        assert r.status == 'SAT' and r.resolved_by == 'direct'

    def test_parity_frame_verdicts_are_sound(self):
        # every parity-frame verdict must match brute-force source evaluation
        import random
        from itertools import product as iproduct
        from backend.lambda_sat import BXor, BVar, BNot, BAnd
        rng = random.Random(0)
        names = ['a', 'b', 'c', 'd']

        def rand_xor(depth):
            if depth == 0 or rng.random() < 0.3:
                v = BVar(rng.choice(names))
                return BNot(v) if rng.random() < 0.5 else v
            return BXor(rand_xor(depth - 1), rand_xor(depth - 1))

        for _ in range(200):
            k = rng.randint(1, 3)
            term = rand_xor(2)
            for _ in range(k - 1):
                term = BAnd(term, rand_xor(2))
            r = lambda_sat(term)
            assert r.resolved_by == 'parity'
            fv = r.free_vars
            brute = any(eval_bool(beta_normalize(term), dict(zip(fv, bits)))
                        for bits in iproduct([False, True], repeat=len(fv)))
            assert (r.status == 'SAT') == brute
            if r.status == 'SAT':
                assert eval_bool(beta_normalize(term), r.witness)
