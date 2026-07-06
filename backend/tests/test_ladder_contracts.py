"""Evals for the ladder invariant contracts (backend/complexity/contracts.py).

Two layers:
  1. binding    - every contract in REGISTRY resolves to a real callable, and
                  CONTRACTS.md is in sync with the registry.
  2. claim evals - the *contracted claim* of each invariant is asserted on
                  small fixtures, so the research claims cannot silently rot.

These are regression evals for the claims in the RUNG docs, kept fast and
deterministic (no stochastic sweeps in the test path).
"""

import importlib
from pathlib import Path

import pytest

from backend.cnf_utils import CNFFormula
from backend.complexity import contracts
from backend.complexity.invariants import (
    energy_landscape_saddle,
    min_refutation_width,
    nullstellensatz_degree,
    signed_laplacian_frustration,
    spectral_gap,
)
from backend.eval.generators import pigeonhole


def _resolve(target: str):
    """Resolve a contract target to its callable. Bare names live in
    backend.complexity.invariants; dotted names are full module paths."""
    if "." in target:
        mod, attr = target.rsplit(".", 1)
        return getattr(importlib.import_module(mod), attr)
    inv = importlib.import_module("backend.complexity.invariants")
    return getattr(inv, target)


# --------------------------------------------------------------------------
# Layer 1 — binding + doc sync
# --------------------------------------------------------------------------

class TestContractBinding:
    def test_every_contract_binds_to_a_callable(self):
        assert contracts.REGISTRY
        for c in contracts.REGISTRY:
            fn = _resolve(c.target)
            assert callable(fn), f"{c.name} -> {c.target} is not callable"

    def test_verdicts_are_known(self):
        allowed = {contracts.CARRIER, contracts.NOT_CARRIER,
                   contracts.STRUCTURE, contracts.SUBSTRATE}
        for c in contracts.REGISTRY:
            assert c.verdict in allowed
            # carriers must cite a theorem; negatives must state a limit
            if c.verdict == contracts.CARRIER:
                assert c.proven, f"{c.name} is a CARRIER but cites no theorem"
            assert c.limit, f"{c.name} has no honest limit"

    def test_contracts_md_in_sync(self):
        path = Path(__file__).resolve().parents[2] / "docs/ladder/CONTRACTS.md"
        rendered = contracts.render_markdown().rstrip("\n")
        on_disk = path.read_text(encoding="utf-8").rstrip("\n")
        assert rendered == on_disk, (
            "docs/ladder/CONTRACTS.md is stale — regenerate with "
            "`python -m backend.complexity.contracts > docs/ladder/CONTRACTS.md`")


# --------------------------------------------------------------------------
# Layer 2 — the contracted claim of each invariant
# --------------------------------------------------------------------------

# fixtures the claims are asserted on
UNIT_CONTRA = CNFFormula(num_vars=1, clauses=[[1], [-1]])
CHAIN = CNFFormula(num_vars=3, clauses=[[1], [-1, 2], [-2, 3], [-3]])
SAT_DISJ = CNFFormula(num_vars=2, clauses=[[1, 2]])
PHP32, _ = pigeonhole(3)  # 3 pigeons, 2 holes, 6 vars


def _tseitin_k4():
    """Tseitin on K4 with one odd vertex -> UNSAT; 6 edge-variables."""
    from itertools import combinations, product
    edges = list(combinations(range(4), 2))
    edge_var = {e: i + 1 for i, e in enumerate(edges)}
    charge = {0: 1, 1: 0, 2: 0, 3: 0}  # total charge odd
    clauses = []
    for v in range(4):
        inc = [edge_var[e] for e in edges if v in e]
        for bits in product([0, 1], repeat=len(inc)):
            if sum(bits) % 2 != charge[v]:
                clauses.append([(lit if b else -lit)
                                for lit, b in zip(inc, bits)])
    return CNFFormula(num_vars=6, clauses=clauses)


class TestCarrierClaims:
    def test_width_and_ns_agree_on_easy(self):
        # both carriers agree on the trivial obstructions
        assert min_refutation_width(UNIT_CONTRA) == 1
        assert nullstellensatz_degree(UNIT_CONTRA) == 1
        assert min_refutation_width(CHAIN) == 2
        assert nullstellensatz_degree(CHAIN) == 2

    def test_ns_and_width_are_incomparable(self):
        # the contracted claim: NS degree and resolution width are ORTHOGONAL
        # obstructions -- neither dominates. (Corrects an earlier "NS >= width"
        # overclaim; Tseitin is the witness the other way.)
        w_php = min_refutation_width(PHP32, wmax=4)
        d_php = nullstellensatz_degree(PHP32, dmax=6)
        assert (w_php, d_php) == (2, 4)          # NS ABOVE width
        tse = _tseitin_k4()
        w_tse = min_refutation_width(tse, wmax=6, max_closure=300000)
        d_tse = nullstellensatz_degree(tse, dmax=6)
        assert (w_tse, d_tse) == (4, 3)          # NS BELOW width
        assert d_php > w_php and d_tse < w_tse    # incomparable, both directions

    def test_carriers_return_none_on_satisfiable(self):
        # no refutation obstruction exists for a SAT formula
        assert nullstellensatz_degree(SAT_DISJ) is None


class TestScopedNegatives:
    def test_spectral_gap_is_monotone_in_density_not_a_peak(self):
        # Rung-1 claim: the cheap graph gap tracks density, not the hardness
        # peak. Deterministic witness: on a fixed variable set, densifying the
        # co-occurrence graph does not lower lambda_2.
        sparse = CNFFormula(num_vars=6, clauses=[[1, 2], [3, 4], [5, 6]])
        dense = CNFFormula(num_vars=6, clauses=[
            [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 1], [1, 4], [2, 5]])
        assert spectral_gap(dense) >= spectral_gap(sparse)

    def test_signed_laplacian_scoped_to_balance(self):
        # contract: 0 iff balanced (frustration-free), > 0 on frustration;
        # it is a balance detector, not a 3-SAT hardness carrier.
        balanced = CNFFormula(num_vars=3, clauses=[[1, 2], [2, 3]])
        frustrated = CNFFormula(num_vars=3, clauses=[[1, 2], [2, 3], [1, -3]])
        assert signed_laplacian_frustration(balanced) < 1e-9
        assert signed_laplacian_frustration(frustrated) > 0.0


class TestStructureClaims:
    def test_saddle_barrier_fixtures(self):
        s = energy_landscape_saddle(CNFFormula(num_vars=2, clauses=[[1, 2]]))
        assert s.satisfiable and s.num_solution_basins == 1
        assert s.connect_barrier == 0
        x = energy_landscape_saddle(
            CNFFormula(num_vars=2, clauses=[[1, 2], [-1, -2]]))
        assert x.num_solution_basins == 2 and x.connect_barrier == 1


class TestSubstrateClaims:
    def test_associator_is_the_associativity_obstruction(self):
        import numpy as np
        from docs.ladder.scripts.fano_braid_associator import (
            associator, omul, e)
        # composition norm |ab| = |a||b|
        rng = np.random.default_rng(0)
        a, b = rng.standard_normal(8), rng.standard_normal(8)
        assert abs(np.linalg.norm(omul(a, b))
                   - np.linalg.norm(a) * np.linalg.norm(b)) < 1e-9
        # zero on a quaternionic triple, nonzero on an octonionic one
        assert np.linalg.norm(associator(e(1), e(2), e(3))) < 1e-9
        assert np.linalg.norm(associator(e(1), e(2), e(4))) == pytest.approx(2.0)
