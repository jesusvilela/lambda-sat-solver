"""Numerical differential checks of the elementary Z2 graph Laplacian theorem."""
from random import Random
import numpy as np
import pytest
from backend.cnf_utils import CNFFormula
from backend.violation_connection import signed_connection
from backend.violation_laplacian import signed_laplacian, signed_energy
from backend.violation_cross_instance import _shuffle_vars


def test_laplacian_quadratic_energy_and_psd():
    rng=Random(14)
    for _ in range(100):
        n,m=rng.randrange(0,5),rng.randrange(0,5)
        clauses=[]
        for j in range(m):
            vv=rng.sample(range(1,n+1),rng.randrange(n+1))
            clauses.append([v*rng.choice((-1,1)) for v in vv])
        f=CNFFormula(n,clauses)
        L=signed_laplacian(f)
        z=np.array([rng.uniform(-2,2) for j in range(n+m)])
        assert np.allclose(L,L.T)
        assert np.isclose(z @ L @ z,signed_energy(f,z),atol=1e-10)
        ev=np.linalg.eigvalsh(L)
        assert all(x>=-1e-9 for x in ev)
        expected=signed_connection(f).balanced_components
        assert sum(abs(x)<1e-8 for x in ev)==expected


def test_balanced_vs_unbalanced_nullity():
    good=CNFFormula(2,[[1,2],[1,2]])
    bad=CNFFormula(2,[[1,2],[1,-2]])
    assert signed_connection(good).balanced_components==1
    assert signed_connection(bad).balanced_components==0
    assert sum(abs(x)<1e-9 for x in np.linalg.eigvalsh(signed_laplacian(good)))==1
    assert sum(abs(x)<1e-9 for x in np.linalg.eigvalsh(signed_laplacian(bad)))==0
    # A satisfiability contradiction need not create graph holonomy.
    unsat=CNFFormula(1,[[1],[-1]])
    assert signed_connection(unsat).balanced_components==1


def test_gauge_relabelings_preserve_eigenvalues():
    f=CNFFormula(4,[[1,2,-3],[1,-2,4],[-1,-3,4],[2,3,-4]])
    original=np.linalg.eigvalsh(signed_laplacian(f))
    for seed in range(20):
        relabeled=_shuffle_vars(f,Random(seed))
        current=np.linalg.eigvalsh(signed_laplacian(relabeled))
        assert np.allclose(original,current,atol=1e-10)


def test_safe_laplacian_bounds():
    with pytest.raises(ValueError):signed_laplacian(CNFFormula(80,[]))
    with pytest.raises(ValueError):signed_laplacian(CNFFormula(1,[[0]]))
    with pytest.raises(ValueError):signed_energy(CNFFormula(1,[[1]]),[1])
