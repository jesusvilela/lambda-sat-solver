"""
VDIS Track B1, Phase 1 - the S4 degeneracy test.

Claim under test: with A=R, D=1, c->0 (kappa->0-), beta=0,
lambda_tau=lambda_chi=0, monotone sigma, VDIS's literal ordering is
IDENTICAL to EVSIDS's, decision-for-decision, on identical solver
traces. This is the falsifiable form of "VSIDS is the scalar fossil of
the living gyrovector field" - if it fails, either the gyro machinery
has a bug, or the reduction claim in the spec is wrong. Both are
reportable findings; this file does not paper over a failure to force
a pass.
"""

from typing import List

import pytest

from backend.cnf_utils import CNFFormula
from backend.eval.suite import StandardSuites
from backend.refsolver.solver import CDCLSolver
from backend.refsolver.heuristics import EVSIDSHeuristic
from backend.vdis.vdis_heuristic import VDISHeuristic


class _RecordingWrapper:
    """Wraps a DecisionHeuristic, recording every literal returned by pick()."""

    def __init__(self, inner):
        self.inner = inner
        self.decisions: List[int] = []

    def on_conflict(self, learned, lbd, trail):
        self.inner.on_conflict(learned, lbd, trail)

    def on_assign(self, lit):
        self.inner.on_assign(lit)

    def on_unassign(self, lit):
        self.inner.on_unassign(lit)

    def pick(self, num_vars, value):
        lit = self.inner.pick(num_vars, value)
        self.decisions.append(lit)
        return lit

    def decay(self):
        self.inner.decay()


def _run_with_recording(cnf: CNFFormula, heuristic, max_conflicts=20000):
    wrapper = _RecordingWrapper(heuristic)
    solver = CDCLSolver(cnf, wrapper, max_conflicts=max_conflicts)
    result, model = solver.solve()
    return result, wrapper.decisions, solver.stats


def _degenerate_vdis(num_vars: int) -> VDISHeuristic:
    # eta/decay_gamma must match EVSIDSHeuristic's defaults (var_inc=1.0,
    # var_decay=0.95) exactly for the order-equivalence argument in
    # docs/vdis/PHASE_1_PATCH.md to apply.
    return VDISHeuristic(num_vars, dim=1, c=0.0, eta=1.0, decay_gamma=0.95)


class TestDegeneracyGate:
    """Runs on >=20 instances from the quick eval suite, per S4."""

    @pytest.fixture(scope="class")
    def instances(self):
        suite = StandardSuites.quick()
        assert len(suite) >= 20
        return suite.instances

    def test_decision_sequences_identical(self, instances):
        mismatches = []
        for inst in instances:
            cnf = inst.formula
            evsids_result, evsids_decisions, evsids_stats = _run_with_recording(
                cnf, EVSIDSHeuristic(cnf.num_vars, seed=0)
            )
            vdis_result, vdis_decisions, vdis_stats = _run_with_recording(
                cnf, _degenerate_vdis(cnf.num_vars)
            )
            if evsids_decisions != vdis_decisions:
                first_diff = next(
                    (i for i, (a, b) in enumerate(zip(evsids_decisions, vdis_decisions)) if a != b),
                    min(len(evsids_decisions), len(vdis_decisions)),
                )
                mismatches.append(
                    {
                        "instance": inst.name,
                        "evsids_result": evsids_result,
                        "vdis_result": vdis_result,
                        "evsids_num_decisions": len(evsids_decisions),
                        "vdis_num_decisions": len(vdis_decisions),
                        "first_diff_index": first_diff,
                        "evsids_at_diff": evsids_decisions[first_diff] if first_diff < len(evsids_decisions) else None,
                        "vdis_at_diff": vdis_decisions[first_diff] if first_diff < len(vdis_decisions) else None,
                    }
                )

        if mismatches:
            pytest.fail(
                f"Degeneracy gate FAILED on {len(mismatches)}/{len(instances)} instances "
                f"(S4 stop condition S2 applies). First few mismatches:\n"
                + "\n".join(str(m) for m in mismatches[:5])
            )
