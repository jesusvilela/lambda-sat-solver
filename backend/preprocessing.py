r"""
SAT Formula Preprocessing — SOTA 2026
Pure-Python preprocessing passes that simplify a CNF formula before
passing it to the main solver (Kissat).  Applied as a pipeline, these
techniques mirror what state-of-the-art preprocessors do:

  1. Unit Propagation (UP)
     Assigns forced variables and simplifies the formula.  O(n·m) per pass.

  2. Pure Literal Elimination (PLE)
     Variables that appear in only one polarity can be freely assigned to
     satisfy all their clauses.  O(n·m) per pass.

  3. Subsumption Elimination (SE)
     If clause A is a subset of clause B, then B is subsumed by A and can
     be removed (A being shorter implies B is already covered).  O(m²) but
     typically fast on sparse formulas.

  4. Self-Subsuming Resolution (SSR) — also called clause strengthening
     If A ∪ {l} and B ∪ {¬l} are clauses and A ⊆ B, then B can be
     replaced by B \ {¬l}.  This is one step of vivification.

  5. Bounded Variable Elimination (BVE) — simplified
     If eliminating variable x does not increase the total clause count,
     replace all clauses containing x with the resolvents.

These passes are applied iteratively until a fixpoint.

Usage:
    from backend.preprocessing import preprocess
    simplified, assignment = preprocess(formula)
    # simplified is a smaller CNFFormula; assignment maps forced variables
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from .cnf_utils import CNFFormula


# ---------------------------------------------------------------------------
# Internal representation: use frozenset clauses for fast subset tests
# ---------------------------------------------------------------------------

Assignment = Dict[int, bool]  # var → True/False


class UNSATException(Exception):
    """Raised when preprocessing discovers the formula is trivially UNSAT."""


def preprocess(
    formula: CNFFormula,
    max_iterations: int = 10,
    enable_bve: bool = True,
    bve_max_increase: int = 0,
) -> Tuple[CNFFormula, Assignment]:
    """
    Apply iterative preprocessing passes to simplify a CNF formula.

    Passes applied each iteration (until fixpoint or max_iterations reached):
      1. Unit propagation
      2. Pure literal elimination
      3. Subsumption elimination
      4. Self-subsuming resolution
      5. Bounded variable elimination (if enable_bve=True)

    If the formula becomes trivially UNSAT (empty clause discovered) this
    function still returns — the returned formula will contain an empty
    clause [], which any correct SAT solver will immediately classify as UNSAT.

    Args:
        formula: CNF formula to preprocess.
        max_iterations: Maximum fixpoint iterations (default 10).
        enable_bve: Enable bounded variable elimination (default True).
        bve_max_increase: BVE is applied only if the resolvent set does not
            add more than this many clauses net (default 0 = no increase).

    Returns:
        (simplified_formula, forced_assignment)
        simplified_formula: A CNFFormula with fewer variables / clauses.
        forced_assignment: Dict mapping variables that were fixed during
            preprocessing to their forced truth values.
    """
    # Work with lists of sets for mutability
    clauses: List[Optional[Set[int]]] = [set(c) for c in formula.clauses]
    assignment: Assignment = {}

    try:
        for _ in range(max_iterations):
            prev_count = sum(1 for c in clauses if c is not None)

            clauses, new_assigns = _unit_propagation(clauses)
            assignment.update(new_assigns)

            clauses = _pure_literal_elimination(clauses, assignment)

            clauses = _subsumption_elimination(clauses)

            clauses = _self_subsuming_resolution(clauses)

            if enable_bve:
                clauses, bve_assigns = _bounded_variable_elimination(
                    clauses, max_increase=bve_max_increase
                )
                assignment.update(bve_assigns)

            # Convergence check
            curr_count = sum(1 for c in clauses if c is not None)
            if curr_count == prev_count:
                break

    except UNSATException:
        # Return the formula with an empty clause to signal UNSAT
        return CNFFormula(
            num_vars=formula.num_vars,
            clauses=[[]],
            comments=formula.comments + ["UNSAT detected during preprocessing"],
        ), assignment

    # Rebuild CNFFormula from surviving clauses
    final_clauses = [sorted(c) for c in clauses if c is not None]

    # Recompute num_vars from surviving literals
    all_vars: Set[int] = set()
    for c in final_clauses:
        all_vars.update(abs(lit) for lit in c)

    num_vars = max(all_vars) if all_vars else 0

    return CNFFormula(
        num_vars=num_vars,
        clauses=final_clauses,
        comments=formula.comments + [
            f"preprocessed: {len(formula.clauses)}->{len(final_clauses)} clauses"
        ],
    ), assignment


# ---------------------------------------------------------------------------
# Pass 1: Unit Propagation
# ---------------------------------------------------------------------------

def _unit_propagation(
    clauses: List[Optional[Set[int]]],
) -> Tuple[List[Optional[Set[int]]], Assignment]:
    """
    Propagate unit clauses to fixpoint.

    Returns updated clause list and new variable assignments.
    Raises UNSATException if a contradiction is found (clause becomes empty).
    """
    assignment: Assignment = {}

    changed = True
    while changed:
        changed = False

        # Detect empty clause — trivially UNSAT
        for c in clauses:
            if c is not None and len(c) == 0:
                raise UNSATException("Empty clause detected")

        # Find unit clauses
        units = []
        for c in clauses:
            if c is not None and len(c) == 1:
                (lit,) = c
                units.append(lit)

        if not units:
            break

        for lit in units:
            var = abs(lit)
            val = lit > 0

            # Check for contradiction
            if var in assignment:
                if assignment[var] != val:
                    raise UNSATException(f"Contradiction on variable {var}")
                continue

            assignment[var] = val
            changed = True

            # Propagate: remove satisfied clauses, shorten others
            new_clauses: List[Optional[Set[int]]] = []
            for c in clauses:
                if c is None:
                    new_clauses.append(None)
                    continue
                if lit in c:
                    # Clause satisfied — drop it
                    new_clauses.append(None)
                elif -lit in c:
                    # Shorten clause
                    shortened = c - {-lit}
                    if len(shortened) == 0:
                        raise UNSATException("Empty clause after unit propagation")
                    new_clauses.append(shortened)
                else:
                    new_clauses.append(c)
            clauses = new_clauses

    return clauses, assignment


# ---------------------------------------------------------------------------
# Pass 2: Pure Literal Elimination
# ---------------------------------------------------------------------------

def _pure_literal_elimination(
    clauses: List[Optional[Set[int]]],
    existing_assignment: Assignment,
) -> List[Optional[Set[int]]]:
    """
    Assign pure literals (those that appear in only one polarity).

    Pure literals can be set to True to satisfy all their clauses, so we
    simply remove all clauses that contain a pure literal.
    """
    pos_vars: Set[int] = set()
    neg_vars: Set[int] = set()
    for c in clauses:
        if c is None:
            continue
        for lit in c:
            if lit > 0:
                pos_vars.add(lit)
            else:
                neg_vars.add(-lit)

    pure_pos = pos_vars - neg_vars  # appear only positive
    pure_neg = neg_vars - pos_vars  # appear only negative

    # Exclude already-assigned variables
    assigned = set(existing_assignment.keys())
    pure_pos -= assigned
    pure_neg -= assigned

    if not pure_pos and not pure_neg:
        return clauses

    new_clauses: List[Optional[Set[int]]] = []
    for c in clauses:
        if c is None:
            new_clauses.append(None)
            continue
        # Check if any literal in c is pure
        satisfied = any(lit in pure_pos or -lit in pure_neg for lit in c)
        if satisfied:
            new_clauses.append(None)
        else:
            new_clauses.append(c)

    return new_clauses


# ---------------------------------------------------------------------------
# Pass 3: Subsumption Elimination
# ---------------------------------------------------------------------------

def _subsumption_elimination(
    clauses: List[Optional[Set[int]]],
) -> List[Optional[Set[int]]]:
    """
    Remove clauses that are subsumed by a shorter clause.

    Clause A subsumes clause B if A ⊆ B (every literal of A is in B).
    Since A is more specific (shorter), B is redundant.

    We use a signature-based filter to avoid O(m²) full comparisons on large
    instances: only compare clauses that share at least one literal with the
    candidate short clause.
    """
    # Work only on non-None clauses with their original indices
    live = [(i, c) for i, c in enumerate(clauses) if c is not None]
    if len(live) < 2:
        return clauses

    # Sort by clause length ascending so we try subsuming with short clauses first
    live.sort(key=lambda x: len(x[1]))

    # Build literal → clause-index inverted index for fast candidate lookup
    lit_to_indices: Dict[int, Set[int]] = defaultdict(set)
    index_set = {i for i, _ in live}
    for i, c in live:
        for lit in c:
            lit_to_indices[lit].add(i)

    subsumed: Set[int] = set()

    for i, ci in live:
        if i in subsumed:
            continue
        # Candidates are clauses that share at least one literal with ci
        # and are longer (can be subsumed by ci)
        candidates: Set[int] = set()
        for lit in ci:
            candidates |= lit_to_indices.get(lit, set())
        candidates.discard(i)
        candidates -= subsumed

        for j in candidates:
            cj = clauses[j]
            if cj is None or j in subsumed:
                continue
            if len(cj) < len(ci):
                continue  # can't be subsumed by ci (strictly shorter — already handled)
            if ci.issubset(cj):
                subsumed.add(j)

    result: List[Optional[Set[int]]] = list(clauses)
    for i in subsumed:
        result[i] = None

    return result


# ---------------------------------------------------------------------------
# Pass 4: Self-Subsuming Resolution (clause strengthening / vivification step)
# ---------------------------------------------------------------------------

def _self_subsuming_resolution(
    clauses: List[Optional[Set[int]]],
) -> List[Optional[Set[int]]]:
    """
    Strengthen clauses using self-subsuming resolution.

    If clause A = C ∪ {l} and clause B = C ∪ {¬l} ∪ extra, then
    resolving on l gives C ∪ extra, which subsumes B.  Replace B with
    C ∪ extra.

    Equivalently: if A ∪ {¬l} ⊆ B for some literal l in A, then remove ¬l
    from B (strengthen B).
    """
    live = [(i, c) for i, c in enumerate(clauses) if c is not None]
    if len(live) < 2:
        return clauses

    live.sort(key=lambda x: len(x[1]))

    # Inverted index: literal → set of clause indices containing it
    lit_to_indices: Dict[int, Set[int]] = defaultdict(set)
    for i, c in live:
        for lit in c:
            lit_to_indices[lit].add(i)

    result: List[Optional[Set[int]]] = [
        set(c) if c is not None else None for c in clauses
    ]

    for i, ci in live:
        if result[i] is None:
            continue
        for lit in list(ci):
            # A = ci \ {lit}; look for clauses that contain -lit and A
            neg_lit = -lit
            candidates = lit_to_indices.get(neg_lit, set()).copy()
            candidates.discard(i)
            for j in candidates:
                cj = result[j]
                if cj is None or i == j:
                    continue
                # Check if (ci - {lit}) ⊆ cj
                a = ci - {lit}
                if a.issubset(cj) and neg_lit in cj:
                    # Strengthen cj: remove -lit
                    new_cj = cj - {neg_lit}
                    if len(new_cj) == 0:
                        raise UNSATException("Empty clause from self-subsuming resolution")
                    result[j] = new_cj
                    # Update inverted index
                    lit_to_indices[neg_lit].discard(j)

    return result


# ---------------------------------------------------------------------------
# Pass 5: Bounded Variable Elimination (BVE)
# ---------------------------------------------------------------------------

def _bounded_variable_elimination(
    clauses: List[Optional[Set[int]]],
    max_increase: int = 0,
) -> Tuple[List[Optional[Set[int]]], Assignment]:
    """
    Eliminate variables by resolution when doing so does not increase clause count.

    For variable x:
      pos_clauses = clauses containing x
      neg_clauses = clauses containing ¬x
      resolvents  = {C ∪ D | (x ∈ C) and (¬x ∈ D)} minus tautologies

    If |resolvents| ≤ |pos_clauses| + |neg_clauses| + max_increase,
    replace pos_clauses ∪ neg_clauses with resolvents.

    Returns updated clause list and any forced assignments (e.g. if one
    polarity had no clauses, the variable is pure and can be assigned).
    """
    assignment: Assignment = {}
    live = [(i, c) for i, c in enumerate(clauses) if c is not None]

    # Collect variable occurrences
    var_pos: Dict[int, List[int]] = defaultdict(list)  # var → [clause indices with +var]
    var_neg: Dict[int, List[int]] = defaultdict(list)  # var → [clause indices with -var]
    for i, c in live:
        for lit in c:
            v = abs(lit)
            if lit > 0:
                var_pos[v].append(i)
            else:
                var_neg[v].append(i)

    all_vars = set(var_pos.keys()) | set(var_neg.keys())
    result: List[Optional[Set[int]]] = list(clauses)

    for v in sorted(all_vars):
        pos_idxs = [i for i in var_pos.get(v, []) if result[i] is not None]
        neg_idxs = [i for i in var_neg.get(v, []) if result[i] is not None]

        if not pos_idxs:
            # Variable appears only negatively → assign False
            assignment[v] = False
            for i in neg_idxs:
                result[i] = None
            continue
        if not neg_idxs:
            # Variable appears only positively → assign True
            assignment[v] = True
            for i in pos_idxs:
                result[i] = None
            continue

        # Compute resolvents
        resolvents: List[Set[int]] = []
        tautology = False
        for pi in pos_idxs:
            cp = result[pi]
            if cp is None:
                continue
            for ni in neg_idxs:
                cn = result[ni]
                if cn is None:
                    continue
                resolvent = (cp | cn) - {v, -v}
                # Check for tautology: if both l and ¬l appear, skip
                is_tautology = any(-lit in resolvent for lit in resolvent if lit > 0)
                if not is_tautology:
                    resolvents.append(resolvent)

        original_count = len(pos_idxs) + len(neg_idxs)
        if len(resolvents) <= original_count + max_increase:
            # Elimination worthwhile
            for i in pos_idxs + neg_idxs:
                result[i] = None
            result.extend(resolvents)   # type: ignore[arg-type]

    return result, assignment
