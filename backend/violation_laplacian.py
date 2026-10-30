"""Exact finite Z2 signed graph connection Laplacian for clause-variable frames.

This is NOT the continuous Euclidean wave-equation operator and is not
an extension of OpenAI's Kakeya theorem. It is a separate finite matrix
whose nullity is controlled by signed graph cycle balance. Not a SAT solver.
"""
from __future__ import annotations

from typing import Sequence
import numpy as np

from .cnf_utils import CNFFormula
from .violation_connection import _rows


def signed_laplacian(formula: CNFFormula, *, max_vertices: int=64) -> np.ndarray:
    """L = D - A_s for the signed clause-variable bipartite graph.

    For real z, z.T L z = sum_edges (z_clause-sign*z_variable)^2 >=0.
    The kernel has one dimension for each balanced connected component,
    including isolated nodes; unbalanced components contribute zero.
    This is a finite graph identity, not a solver certificate.
    """
    rows=_rows(formula)
    m,n=len(rows),formula.num_vars
    if not isinstance(max_vertices,int) or max_vertices<0 or n+m>max_vertices:
        raise ValueError('laplacian vertex budget exceeded')
    L=np.zeros((n+m,n+m),dtype=np.float64)
    for ci,row in enumerate(rows):
        for v,sign in row.items():
            j=m+v
            L[ci,ci]+=1
            L[j,j]+=1
            L[ci,j]-=sign
            L[j,ci]-=sign
    return L


def signed_energy(formula: CNFFormula, vector: Sequence[float]) -> float:
    """Return the exact edge-energy expression for a real node vector."""
    rows=_rows(formula)
    m,n=len(rows),formula.num_vars
    if len(vector)!=m+n:
        raise ValueError('expected one real coordinate per clause/variable node')
    return sum((vector[ci]-sign*vector[m+v])**2
               for ci,row in enumerate(rows) for v,sign in row.items())
