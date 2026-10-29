"""Independent finite checks of graph-boundary image = even component charges."""
from itertools import product
from random import Random
import pytest

from backend.cnf_utils import CNFFormula,verify_model
from backend.violation_cdcl_topology import generate_formula
from backend.violation_tseitin_boundary import (
    solve_boundary,edge_boundary,recover_tseitin_graph,
    decide_tseitin_boundary)
from backend.xor_extraction import gf2_xor_solve


def test_path_and_explicit_odd_charge_witness():
    edges=((0,1),(1,2))
    yes=solve_boundary(3,edges,(1,0,1))
    assert yes.consistent and yes.rank==2
    assert yes.edge_bits==(1,1)
    assert edge_boundary(3,edges,yes.edge_bits)==(1,0,1)
    no=solve_boundary(3,edges,(1,0,0))
    assert not no.consistent
    assert no.odd_component_indices==(0,)
    assert no.components==((0,1,2),)
    assert no.charges_per_component==(1,)
    assert no.edge_bits is None


def test_disconnected_and_isolated_obstruction():
    edges=((0,1),(2,3))
    yes=solve_boundary(5,edges,(1,1,0,0,0))
    assert yes.consistent and yes.rank==2
    assert len(yes.components)==3
    no=solve_boundary(5,edges,(1,1,0,0,1))
    assert not no.consistent
    assert no.odd_component_indices==(2,)
    assert no.components[2]==(4,)
    assert no.charges_per_component==(0,0,1)


def test_parallel_edges_and_empty_graph_are_handled():
    edges=((0,1),(0,1))
    for charges in ((0,0),(1,1)):
        result=solve_boundary(2,edges,charges)
        assert result.consistent
        assert edge_boundary(2,edges,result.edge_bits)==charges
    assert not solve_boundary(2,edges,(1,0)).consistent
    assert solve_boundary(0,(),()).rank==0


def test_random_graphs_match_bruteforce_gf2_image_and_rank():
    rng=Random(20261029)
    for _ in range(120):
        vertices=rng.randrange(1,7)
        possible=[(a,b) for a in range(vertices) for b in range(a+1,vertices)]
        edges=tuple(rng.sample(possible,rng.randrange(min(8,len(possible))+1)))
        if edges and rng.randrange(3)==0:
            edges=edges+(rng.choice(edges),)  # allow multigraph boundary
        reachable={edge_boundary(vertices,edges,x) for x in product((0,1),repeat=len(edges))}
        for charges in product((0,1),repeat=vertices):
            cert=solve_boundary(vertices,edges,charges)
            assert cert.consistent==(charges in reachable)
            assert cert.rank==vertices-len(cert.components)
            assert 2**cert.rank==len(reachable)
            if cert.consistent:
                assert edge_boundary(vertices,edges,cert.edge_bits)==charges
            else:
                assert all(cert.charges_per_component[k]==1 for k in cert.odd_component_indices)


def test_fully_recovered_tseitin_has_exact_graph_obstruction():
    for family in ("tseitin-prism","tseitin-rewired"):
        for n in (12,48,72,96):
            for seed in range(4):
                f=generate_formula(family,n,seed)
                graph=recover_tseitin_graph(f)
                assert graph is not None
                assert graph.vertices==2*n//3
                assert len(graph.edges)==n
                decision=decide_tseitin_boundary(f)
                linear=gf2_xor_solve(f)
                assert decision.status==linear.status
                assert decision.status==("SAT" if seed%2==0 else "UNSAT")
                assert decision.rank==graph.vertices-1
                if decision.status=="SAT":
                    assert decision.model is not None
                    assert verify_model(f,decision.model)
                else:
                    assert decision.odd_component is not None
                    assert sum(graph.charges[v] for v in decision.odd_component)%2==1


def test_non_graph_and_partial_xor_must_be_rejected():
    random3=generate_formula("uniform3",48,99)
    assert recover_tseitin_graph(random3) is None
    assert decide_tseitin_boundary(random3).status=="NOT_TSEITIN"
    # One XOR variable belongs to exactly one parity equation: not a boundary.
    xor=CNFFormula(3,[[1,2,3],[1,-2,-3],[-1,2,-3],[-1,-2,3]])
    assert recover_tseitin_graph(xor) is None
    assert decide_tseitin_boundary(xor).status=="NOT_TSEITIN"
    with_extra=CNFFormula(3,xor.clauses+[[1]])
    assert recover_tseitin_graph(with_extra) is None


def test_invalid_boundary_inputs():
    with pytest.raises(ValueError):solve_boundary(2,((0,2),),(0,0))
    with pytest.raises(ValueError):solve_boundary(2,((0,0),),(0,0))
    with pytest.raises(ValueError):solve_boundary(2,(),(0,))
    with pytest.raises(ValueError):solve_boundary(2,(),(2,0))
    with pytest.raises(ValueError):edge_boundary(2,((0,1),),(2,))
