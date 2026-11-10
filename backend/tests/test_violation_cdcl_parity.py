"""GF(2) parity gate as a known sound positive comparator, not invented geometry."""
import pytest

from backend.cnf_utils import CNFFormula
from backend.violation_cdcl_parity import GF2,PREDICTORS,gf2_control,parity_holdout
from backend.violation_cdcl_topology import generate_formula
from backend.xor_extraction import gf2_xor_solve


@pytest.mark.parametrize("family",["tseitin-prism","tseitin-rewired"])
def test_global_charge_obstruction_is_recovered_in_each_graph(family):
    for size in (12,48,72):
        for seed in range(4):
            f=generate_formula(family,size,seed)
            check=gf2_control(f)
            assert check.extracted_constraints==2*size//3
            assert check.features[0]==1.0
            assert check.rank==2*size//3-1
            assert check.frame_status==("UNSAT" if seed%2 else "SAT")
            # Existing verified frame and new feature extractor agree.
            assert check.frame_status==gf2_xor_solve(f).status
            assert check.elapsed_ms>=0


def test_incomplete_nonxor_must_never_claim_full_frame():
    for family in ("uniform3","ring3","community3","hub3"):
        f=generate_formula(family,48,100)
        report=gf2_control(f)
        assert report.frame_status=="INCONCLUSIVE"
        assert report.extracted_constraints>=0
        assert 0<=report.features[0]<=1
        assert len(report.features)==len(GF2)


def test_real_glucose4_independent_positive_control_if_installed():
    pytest.importorskip("pysat.solvers")
    report=parity_holdout(seeds=2,seed_start=100,sizes=(12,15),
                         orbits=1,budget=200,swaps=8)
    assert report.formulas==24
    assert report.seed_start==100
    assert len(report.cases)==24
    assert set(report.aggregate_mae)==set(PREDICTORS)
    assert report.status_counts["SAT"]>=4
    assert report.status_counts["UNSAT"]>=4
    assert report.status_counts["SAT"]+report.status_counts["UNSAT"]==report.pure_xor_checked
    assert report.match_error_count==0
    assert len(report.family_holdouts)==6
    assert report.largest_size_holdout is not None
    for r in report.cases:
        assert r.frame_status in ("SAT","UNSAT","INCONCLUSIVE")
        assert all(s in ("SAT","UNSAT","UNKNOWN") for s in r.call_statuses)


def test_pure_xor_and_partial_nonxor_compare_not_equate():
    xor=CNFFormula(3,[[1,2,3],[1,-2,-3],[-1,2,-3],[-1,-2,3]])
    assert gf2_control(xor).frame_status=="SAT"
    # Extra clause makes the full formula potentially different:
    # an entailed XOR cannot decide this partial fragment alone.
    augmented=CNFFormula(4,xor.clauses+[[4]])
    assert gf2_control(augmented).frame_status=="INCONCLUSIVE"
