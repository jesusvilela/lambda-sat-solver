"""Tests for lambda's CONTRIBUTION to the mesh (backend/lambda_bridge.py).

Not equivalence -- contribution: the projection is sound (the shared, trusted
ground), and on top of it lambda adds composition and a dynamic epsilon>0
remainder that the flat frames cannot express.
"""

from backend.lambda_bridge import (
    brute_truth,
    frame_decide,
    lambda_contribution,
    lambda_signature,
    project,
)
from backend.lambda_sat import App, BAnd, BNot, BOr, BVar, BXor, Lam


class TestSoundProjection:
    def test_frame_decision_is_sound_vs_ground_truth(self):
        # the trusted shared ground: whenever the frame router decides the
        # projection, it agrees with the term's ground-truth satisfiability.
        terms = [
            BXor(BVar("a"), BVar("b")),
            BAnd(BXor(BVar("x"), BVar("y")), BNot(BXor(BVar("x"), BVar("y")))),
            BOr(BVar("a"), BVar("b")),
            BAnd(BVar("p"), BOr(BVar("q"), BNot(BVar("p")))),
        ]
        for t in terms:
            r = frame_decide(t)
            if r.status != "CDCL_NEEDED":
                assert r.status == brute_truth(t)

    def test_lambda_joins_the_orbifold_mesh(self):
        # a lambda term acquires a full orbifold chart via projection
        sig = lambda_signature(BXor(BVar("a"), BVar("b")))
        assert sig.classical_bit in ("SAT", "UNSAT", "CDCL_NEEDED")
        assert sig.symmetry_log2_upper >= 0.0
        assert hasattr(sig, "symmetry_log2_exact")

    def test_projection_is_nonempty(self):
        cnf, ids = project(BAnd(BVar("a"), BVar("b")))
        assert cnf.num_vars >= 2 and len(cnf.clauses) >= 1


class TestContribution:
    def test_plain_term_adds_no_composition_or_dynamics(self):
        c = lambda_contribution(BAnd(BVar("a"), BVar("b")))
        assert c.equisatisfiable
        assert not c.adds_composition
        assert not c.adds_dynamics

    def test_redex_adds_composition_and_reveals_a_frame(self):
        # (lambda f. f xor g)(x xor y) -> parity only AFTER reduction: the
        # contribution is that composition generates the frame.
        t = App(Lam("f", BXor(BVar("f"), BVar("g"))),
                BXor(BVar("x"), BVar("y")))
        c = lambda_contribution(t)
        assert c.adds_composition
        assert c.frame_after_reduction == "parity"

    def test_mobius_fixpoint_adds_dynamics_frames_cannot_hold(self):
        # lambda s. not s never stabilizes: an active epsilon>0 remainder, a
        # satisfiability MODE no flat frame can express. This is lambda's
        # irreducible contribution.
        c = lambda_contribution(Lam("s", BNot(BVar("s"))))
        assert c.adds_dynamics

    def test_stabilizing_fixpoint_has_no_active_remainder(self):
        # lambda s. a (ignores the tail) stabilizes -> no dynamic contribution
        c = lambda_contribution(Lam("s", BVar("a")))
        assert not c.adds_dynamics
