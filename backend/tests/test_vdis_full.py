"""
VDIS Track B1, Phase 2 - full-configuration behavior tests: C and H
variants run without numerical failure and give correct SAT/UNSAT
answers; the living field actually activates (the Phase 1 absorbing
fixed point does not recur one level up); rotor state moves and Psi
stays a unit rotor. Wall-clock budget (S3.7) is measured by
docs/vdis/scripts/phase2_budget.py, not asserted here - a timing
assertion in CI is a flaky test waiting to happen.
"""

import numpy as np
import pytest

from backend.cnf_utils import CNFFormula
from backend.eval.generators import pigeonhole, random_ksat
from backend.refsolver.solver import CDCLSolver, SolveResult
from backend.vdis.vdis_heuristic import VDISHeuristic, compute_chi


def _full_config(num_vars, algebra, chi=None, **kw):
    """Spec defaults: D=16/A=C or D=8/A=H (dim=32 either way), kappa=-1,
    beta and lambdas at their S3.6 default 0.1."""
    return VDISHeuristic(
        num_vars,
        dim=32,
        c=1.0,
        algebra=algebra,
        beta=0.1,
        lambda_tau=0.1,
        lambda_chi=0.1 if chi is not None else 0.0,
        chi=chi,
        seed=0,
        **kw,
    )


def _check_model(formula: CNFFormula, model):
    for clause in formula.clauses:
        if not any(
            (lit > 0) == model[abs(lit)]
            for lit in clause
            if model[abs(lit)] is not None
        ):
            return False
    return True


class TestConstructorValidation:
    def test_dim_must_be_multiple_of_algebra_dim(self):
        with pytest.raises(ValueError):
            VDISHeuristic(5, dim=6, algebra="H")  # 6 % 4 != 0

    def test_rotor_channel_needs_bivectors(self):
        with pytest.raises(ValueError):
            VDISHeuristic(5, dim=1, algebra="R", beta=0.1)

    def test_hard_budget(self):
        with pytest.raises(ValueError):
            VDISHeuristic(5, dim=128, algebra="C")

    def test_phase2_params_now_accepted(self):
        # Phase 1 raised NotImplementedError here; Phase 2 must not.
        h = _full_config(5, "H")
        assert h.D == 8 and h.m == 4

    def test_unknown_algebra_rejected(self):
        with pytest.raises(ValueError):
            VDISHeuristic(5, dim=8, algebra="O")  # octonions are PARKED


class TestFullConfigSolves:
    @pytest.mark.parametrize("algebra", ["C", "H"])
    def test_sat_instance_solved_and_model_checked(self, algebra):
        formula, _ = random_ksat(20, 60, k=3, seed=7)  # underconstrained: SAT
        chi = compute_chi(formula.clauses, formula.num_vars)
        solver = CDCLSolver(
            formula, _full_config(formula.num_vars, algebra, chi=chi)
        )
        result, model = solver.solve()
        assert result == SolveResult.SAT
        assert _check_model(formula, model)

    @pytest.mark.parametrize("algebra", ["C", "H"])
    def test_unsat_instance(self, algebra):
        formula, expected = pigeonhole(4)  # PHP(4,3): UNSAT
        assert expected == "UNSAT"
        solver = CDCLSolver(formula, _full_config(formula.num_vars, algebra))
        result, _ = solver.solve()
        assert result == SolveResult.UNSAT


class TestLivingFieldActivates:
    """The Phase 1 failure mode, one level up: with zero init, the
    state-dependent living axes (and the rotor wedge built from them)
    stay exactly zero forever. eps-init must break that - i.e. the
    living axes must MOVE from their initial values once conflicts
    happen, not merely sit at the eps seeds."""

    def test_living_axes_move_from_init(self):
        formula, _ = pigeonhole(4)
        h = _full_config(formula.num_vars, "H")
        init_living = h._t[:, 1:].copy()
        solver = CDCLSolver(formula, h)
        solver.solve()
        assert solver.stats.conflicts > 0
        moved = np.abs(h._t[:, 1:] - init_living).max()
        assert moved > 0.0, "living axes never moved: absorbing fixed point is back"

    def test_zero_eps_reproduces_the_fixed_point(self):
        # Negative control: with living_eps=0 the living axes must stay
        # exactly zero - demonstrating the eps-init is what breaks the
        # fixed point, not some other Phase 2 change. (beta=0 because the
        # rotor channel needs a direction to exist at all.)
        formula, _ = pigeonhole(4)
        h = VDISHeuristic(
            formula.num_vars, dim=32, c=1.0, algebra="H", living_eps=0.0, seed=0
        )
        solver = CDCLSolver(formula, h)
        solver.solve()
        assert solver.stats.conflicts > 0
        assert np.all(h._t[:, 1:] == 0.0)

    def test_fossil_axis_init_is_exactly_zero(self):
        h = _full_config(10, "C")
        assert np.all(h._t[:, 0] == 0.0)


class TestRotorChannel:
    def test_omega_moves_and_psi_stays_unit(self):
        formula, _ = pigeonhole(4)
        h = _full_config(formula.num_vars, "H")
        solver = CDCLSolver(formula, h)
        solver.solve()
        assert solver.stats.conflicts > 1
        assert np.abs(h._omega).max() > 0.0
        assert np.linalg.norm(h.psi) == pytest.approx(1.0, abs=1e-9)

    def test_tau_bounded(self):
        formula, _ = pigeonhole(4)
        h = _full_config(formula.num_vars, "H")
        solver = CDCLSolver(formula, h)
        solver.solve()
        h._rotors = None  # force recompute path
        h._rotors_dirty = True
        scores_with = h._lit_scores()
        assert np.all(np.isfinite(scores_with))
        # tau itself: recompute directly and check range
        from backend.vdis.algebra import rotor_exp, rotor_sandwich

        rotors = rotor_exp(h._omega / 2.0, "H")
        tau = np.sum(rotor_sandwich(rotors, h.psi, "H") * h.psi, axis=-1)
        assert np.all(tau <= 1.0 + 1e-9) and np.all(tau >= -1.0 - 1e-9)


class TestChi:
    def test_compute_chi_values(self):
        clauses = [[1, -2], [1, 2, 3], [-3]]
        chi = compute_chi(clauses, 3)
        nv = 3
        assert chi[1 + nv] == pytest.approx(2.0 * 2 / (2 + 3))  # lit 1: lens 2,3
        assert chi[-2 + nv] == pytest.approx(2.0 / 2)           # lit -2: len 2
        assert chi[-3 + nv] == pytest.approx(2.0 / 1)           # lit -3: len 1
        assert chi[2 + nv] == pytest.approx(2.0 / 3)            # lit 2: len 3
        assert chi[-1 + nv] == 0.0                              # absent literal

    def test_chi_length_validated(self):
        with pytest.raises(ValueError):
            VDISHeuristic(5, dim=2, algebra="C", lambda_chi=0.1, chi=np.zeros(3))
