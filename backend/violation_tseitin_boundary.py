"""Constructive GF(2) graph-boundary theorem for fully recovered Tseitin CNFs.

Let partial: F_2^E -> F_2^V map an edge bit to its two endpoints.
Then im(partial) is exactly the set of charge vectors with even XOR sum
on every connected component. This classical incidence fact is constructive,
and different from the real signed clause-variable graph Laplacian.

Only *fully covered* recovered XOR encodings with each variable in exactly
two XOR equations are admitted. This experimental module neither changes
the λSAT trusted base nor claims a new complexity theorem.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .cnf_utils import CNFFormula, verify_model
from .xor_extraction import extract_xors


@dataclass(frozen=True)
class BoundaryWitness:
    vertices: int
    edges: int
    components: tuple[tuple[int,...],...]
    rank: int
    charges_per_component: tuple[int,...]
    consistent: bool
    odd_component_indices: tuple[int,...]
    edge_bits: tuple[int,...] | None


def edge_boundary(vertices: int, edges: Sequence[tuple[int,int]],
                  values: Sequence[int]) -> tuple[int,...]:
    """Compute GF(2) incidence boundary; each edge toggles BOTH endpoints."""
    if not isinstance(vertices,int) or isinstance(vertices,bool) or vertices<0:
        raise ValueError("invalid vertex count")
    if len(edges)!=len(values):
        raise ValueError("edge/value count mismatch")
    result=[0]*vertices
    for (a,b),value in zip(edges,values):
        if (not isinstance(a,int) or not isinstance(b,int) or
                isinstance(a,bool) or isinstance(b,bool) or
                a==b or not (0<=a<vertices and 0<=b<vertices)):
            raise ValueError("invalid incidence endpoints")
        if value not in (0,1):
            raise ValueError("edge bits must lie in GF(2)")
        result[a]^=value
        result[b]^=value
    return tuple(result)


def solve_boundary(vertices: int, edges: Sequence[tuple[int,int]],
                   charges: Sequence[int]) -> BoundaryWitness:
    """O(V+E) constructive component-parity test with a forest witness.

    Parallel edges are allowed, indexed separately, as in a multigraph.
    Odd charge on a connected component is a left-kernel obstruction.
    Otherwise choose non-tree edge bits zero and solve leaf-to-root along a
    spanning forest. The proof uses no Gaussian inversion or solver oracle.
    """
    if not isinstance(vertices,int) or isinstance(vertices,bool) or vertices<0:
        raise ValueError("invalid vertex count")
    if len(charges)!=vertices or any(c not in (0,1) for c in charges):
        raise ValueError("charges must be one GF(2) bit per vertex")
    adj=[[] for _ in range(vertices)]
    for i,(a,b) in enumerate(edges):
        if (not isinstance(a,int) or not isinstance(b,int) or
                isinstance(a,bool) or isinstance(b,bool) or
                not (0<=a<vertices and 0<=b<vertices) or a==b):
            raise ValueError("invalid graph edge")
        adj[a].append((b,i))
        adj[b].append((a,i))
    parent=[-1]*vertices
    parent_edge=[-1]*vertices
    seen=[False]*vertices
    components=[]
    traversal=[]
    parities=[]
    for root in range(vertices):
        if seen[root]:
            continue
        seen[root]=True
        stack=[root]
        component=[]
        parity=0
        while stack:
            v=stack.pop()
            component.append(v)
            traversal.append(v)
            parity^=charges[v]
            for w,ei in adj[v]:
                if not seen[w]:
                    seen[w]=True
                    parent[w]=v
                    parent_edge[w]=ei
                    stack.append(w)
        components.append(tuple(sorted(component)))
        parities.append(parity)
    odd=tuple(i for i,p in enumerate(parities) if p)
    bits=None
    if not odd:
        residual=list(charges)
        assignment=[0]*len(edges)
        for v in reversed(traversal):
            if parent[v]<0:
                if residual[v]:
                    raise AssertionError("even component parity failed at root")
                continue
            value=residual[v]
            assignment[parent_edge[v]]=value
            residual[parent[v]]^=value
        bits=tuple(assignment)
        if edge_boundary(vertices,edges,bits)!=tuple(charges):
            raise AssertionError("forest solution failed independent boundary replay")
    return BoundaryWitness(vertices,len(edges),tuple(components),
            vertices-len(components),tuple(parities),not odd,odd,bits)


@dataclass(frozen=True)
class RecoveredTseitin:
    vertices: int
    edges: tuple[tuple[int,int],...]
    charges: tuple[int,...]
    variables: int


def recover_tseitin_graph(formula: CNFFormula) -> RecoveredTseitin | None:
    """Recover a GF(2) boundary system from *complete* short-XOR CNF.

    Admit only XOR fragments in which each variable belongs to exactly two
    recovered constraints, so the XOR matrix is an unoriented graph boundary.
    If coverage is partial or a variable has other incidence, refuse rather
    than pretending general parity constraints are a graph.
    """
    extracted=extract_xors(formula)
    if not extracted.xors or extracted.num_xor_clauses!=len(formula.clauses):
        return None
    membership=[[] for _ in range(formula.num_vars)]
    for ci,xor in enumerate(extracted.xors):
        for var in xor.variables:
            if not 1<=var<=formula.num_vars:
                raise AssertionError("malformed recovered XOR variable")
            membership[var-1].append(ci)
    if any(len(groups)!=2 or groups[0]==groups[1] for groups in membership):
        return None
    edges=tuple((groups[0],groups[1]) for groups in membership)
    charges=tuple(x.rhs for x in extracted.xors)
    return RecoveredTseitin(len(extracted.xors),edges,charges,formula.num_vars)


@dataclass(frozen=True)
class TseitinDecision:
    status: str                        # SAT | UNSAT | NOT_TSEITIN
    rank: int | None
    component_charges: tuple[int,...] | None
    odd_component: tuple[int,...] | None
    model: dict[int,bool] | None


def decide_tseitin_boundary(formula: CNFFormula) -> TseitinDecision:
    """Constructively decide the recognized pure graph-boundary XOR subclass.

    UNSAT: the listed odd-charge XOR equation component sums to 0=1.
    SAT: edge assignment from spanning tree is replayed on ORIGINAL CNF.
    Other CNFs: NOT_TSEITIN. No production routing or certificate change.
    """
    graph=recover_tseitin_graph(formula)
    if graph is None:
        return TseitinDecision("NOT_TSEITIN",None,None,None,None)
    cert=solve_boundary(graph.vertices,graph.edges,graph.charges)
    if cert.odd_component_indices:
        k=cert.odd_component_indices[0]
        return TseitinDecision("UNSAT",cert.rank,cert.charges_per_component,
                               cert.components[k],None)
    model={v+1:bool(bit) for v,bit in enumerate(cert.edge_bits or ())}
    if not verify_model(formula,model):
        raise AssertionError("Tseitin spanning-forest witness failed CNF replay")
    return TseitinDecision("SAT",cert.rank,cert.charges_per_component,None,model)
