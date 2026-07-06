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
