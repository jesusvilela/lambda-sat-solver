"""Contracts for the ladder's intrinsic invariants.

Each invariant in `backend.complexity.invariants` is a research claim, not just
a function. This module pins every one to an explicit, machine-readable
contract in the operator's discipline:

    input  ->  invariant  ->  action  ->  benchmark

plus the two fields that keep the work honest: what is *theorem-backed*
(`proven`) and the boundary it must not be claimed past (`limit`). The
`verdict` classifies what the invariant is *for*:

  CARRIER      - a hardness lower-bound carrier with a theorem under it
  NOT_CARRIER  - measured NOT to track per-instance hardness (a scoped negative)
  STRUCTURE    - an exact structural readout (no hardness claim on its own)
  SUBSTRATE    - research substrate; explicitly not a solver route

`backend/tests/test_ladder_contracts.py` binds every contract to its callable
and asserts the contracted claim on small fixtures, so the claims cannot
silently rot. `docs/ladder/CONTRACTS.md` is rendered from `REGISTRY` and must
stay in sync (a test enforces it).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

CARRIER = "CARRIER"
NOT_CARRIER = "NOT_CARRIER"
STRUCTURE = "STRUCTURE"
SUBSTRATE = "SUBSTRATE"


@dataclass(frozen=True)
class InvariantContract:
    """One invariant's promise. `target` is the dotted attribute name in
    `backend.complexity.invariants` (or a script module) it binds to."""

    name: str
    target: str
    cost: str          # complexity of computing it
    input_domain: str  # what formulas it accepts
    invariant: str     # the solver-independent quantity it computes
    action: str        # the decision / claim it licenses
    benchmark: str     # the eval that validates it (see test_ladder_contracts)
    proven: str        # the theorem-backed part (empty if none)
    limit: str         # the boundary it must not be claimed past
    verdict: str       # CARRIER | NOT_CARRIER | STRUCTURE | SUBSTRATE


REGISTRY: List[InvariantContract] = [
    InvariantContract(
        name="mean_var_degree / var_degree_entropy / spectral_gap",
        target="spectral_gap",
        cost="poly-time (O(n^3) eig on the co-occurrence graph)",
        input_domain="any CNFFormula",
        invariant="cheap graph-structural statistics of the variable "
                  "co-occurrence graph; spectral_gap = lambda_2 of its "
                  "normalized Laplacian (a Cheeger/expansion surrogate)",
        action="licenses NOTHING about per-instance hardness; usable only as "
                "an expansion proxy inside a width argument",
        benchmark="RUNG1_REPORT: monotone-increasing in clause density across "
                  "the n=50 transition; does NOT peak at the hardness maximum "
                  "(rank-corr with DPLL cost ~ +0.19)",
        proven="",
        limit="a poly-time incidence-graph scalar is provably NOT the carrier "
              "of random-3-SAT hardness (this is the Rung-1 negative)",
        verdict=NOT_CARRIER,
    ),
    InvariantContract(
        name="solution_stats",
        target="solution_stats",
        cost="exact, O(2^n) (guarded by max_vars)",
        input_domain="CNFFormula with num_vars <= max_vars (default 24)",
        invariant="exact solution-space geometry: num_solutions, "
                  "backbone_fraction (frozen vars), num_clusters "
                  "(Hamming-1 components), satisfiable",
        action="licenses reading the freezing/shattering signature "
                "(backbone up, clusters collapse through the transition)",
        benchmark="unit fixtures (disjunction 3 sols / conj full backbone / "
                  "xor 2 clusters / unsat 0); RUNG1_REPORT transition table",
        proven="freezing/clustering is the established structural phenomenon of "
               "random-k-SAT near threshold (Achlioptas-Coja-Oghlan; "
               "Mezard-Zecchina)",
        limit="also largely monotone in density, not a single-number hardness "
              "peak; exact only where the hardness peak itself is shallow",
        verdict=STRUCTURE,
    ),
    InvariantContract(
        name="min_refutation_width",
        target="min_refutation_width",
        cost="exact, up to Theta(n^w) width-w closure (guarded)",
        input_domain="UNSAT CNFFormula (0 if empty clause; None if not found "
                     "within wmax/max_closure)",
        invariant="minimum resolution refutation width = the sheaf/k-consistency "
                  "obstruction level (local sections fail to glue at this width)",
        action="lower-bounds resolution refutation SIZE, hence DPLL/CDCL "
                "search cost on UNSAT instances",
        benchmark="unit fixtures (unit-contra 1 / chain 2 / PHP(3->2) 2 / "
                  "empty 0)",
        proven="Ben-Sasson-Wigderson (JACM'01): size >= "
               "exp(Omega((w-w0)^2/n)) — width provably lower-bounds size",
        limit="expensive by design (blows past PHP(4->3)); names the obstruction, "
              "does not cheapen it; no polynomial algorithm implied",
        verdict=CARRIER,
    ),
    InvariantContract(
        name="nullstellensatz_degree",
        target="nullstellensatz_degree",
        cost="exact, exponential (O(m*n^d) generators over 2^n monomials; "
             "guarded by dmax/max_vars)",
        input_domain="UNSAT CNFFormula, num_vars <= max_vars (0 if empty "
                     "clause; None if satisfiable)",
        invariant="Nullstellensatz/Polynomial-Calculus degree over GF(2) = "
                  "least d at which 1 enters the GF(2)-span of "
                  "{monomial * clause-violation-poly}; the rank-deficiency "
                  "(cokernel of M_d) obstruction — the zero-divisor lift",
        action="lower-bounds Polynomial-Calculus refutation size; the algebraic "
                "sibling of resolution width",
        benchmark="unit fixtures (unit-contra 1 / chain 2 / PHP(3->2) 4 / "
                  "SAT None / empty 0); NS >= width on every tested instance; "
                  "PHP separates them (NS 4 vs width 2)",
        proven="Clegg-Edmonds-Impagliazzo'96 / Impagliazzo-Pudlak-Sgall'99: "
               "PC degree lower-bounds PC size",
        limit="exponential; the clean G2/symmetry channel reduction that would "
              "cheapen it is char-2 obstructed over GF(2) (RUNG2_LIE_TELOS)",
        verdict=CARRIER,
    ),
    InvariantContract(
        name="signed_laplacian_frustration",
        target="signed_laplacian_frustration",
        cost="poly-time (eig on the signed variable graph)",
        input_domain="any CNFFormula",
        invariant="smallest eigenvalue of the connection (Z/2 gain) Laplacian "
                  "over mean degree = polarity-aware frustration (0 iff the "
                  "signed graph is balanced)",
        action="detects the balanced (frustration-free) 2-SAT/XOR fragment; "
                "licenses NOTHING about general-3-SAT hardness",
        benchmark="unit fixtures (balanced path 0 / frustrated triangle > 0); "
                  "RUNG2_REPORT: also monotone in density, rank-corr +0.19 — "
                  "same as the unsigned gap",
        proven="balance = 2-SAT satisfiability of the equivalence fragment",
        limit="polarity-awareness does NOT rescue a graph-spectral invariant "
              "as a hardness carrier; correctly scoped to XOR/2-SAT structure",
        verdict=NOT_CARRIER,
    ),
    InvariantContract(
        name="energy_landscape_saddle",
        target="energy_landscape_saddle",
        cost="exact, O(2^n) flood (guarded by max_vars)",
        input_domain="CNFFormula with num_vars <= max_vars (default 22)",
        invariant="violated-clause energy landscape: num_solution_basins and "
                  "connect_barrier (the saddle energy E* to connect all "
                  "solution basins), plus ground_energy",
        action="reads the barrier/disconnectivity structure of the "
                "solution space; tracks hardness better than cluster count",
        benchmark="unit fixtures (connected basin barrier 0 / xor 2 basins "
                  "barrier 1 / unsat ground 1); RUNG_SADDLE_NOTE (+0.40 vs "
                  "+0.20 at n=18)",
        proven="",
        limit="ruggedness is NOT the P/NP separator — XOR is rugged yet in P "
              "via Gaussian elimination; the separator is algebraic (Schaefer / "
              "the gate), not landscape barrier height",
        verdict=STRUCTURE,
    ),
    InvariantContract(
        name="fano_braid_associator (substrate)",
        target="docs.ladder.scripts.fano_braid_associator.associator",
        cost="O(1) per triple (octonion arithmetic)",
        input_domain="octonions in R^8 (Cayley-Dickson doubling of H)",
        invariant="the associator [a,b,c]=(ab)c-a(bc): the local obstruction to "
                  "a,b,c sharing a common associative (quaternionic) frame; the "
                  "Braid8 non-associativity core, dynamical face of g2=Der(O)",
        action="research substrate for the braid-theta engine; NOT a SAT route",
        benchmark="composition norm |ab|=|a||b|; associator 0 on quaternionic "
                  "triples, != 0 (magnitude 2) on octonionic triples",
        proven="Aut(O)=G2; braiding is universal for BQP "
               "(Freedman-Kitaev-Larsen-Wang)",
        limit="BQP is not believed to contain NP; braid-closure invariants "
              "(Jones) are #P-hard to evaluate exactly — power, not a shortcut",
        verdict=SUBSTRATE,
    ),
]


def render_markdown() -> str:
    """Render REGISTRY to the canonical CONTRACTS.md body."""
    order = [CARRIER, STRUCTURE, NOT_CARRIER, SUBSTRATE]
    titles = {
        CARRIER: "Hardness carriers (theorem-backed)",
        STRUCTURE: "Exact structural readouts",
        NOT_CARRIER: "Scoped negatives (measured NOT to carry hardness)",
        SUBSTRATE: "Research substrate (not a solver route)",
    }
    lines = [
        "# Ladder invariants — contracts",
        "",
        "Auto-rendered from `backend/complexity/contracts.py` (`REGISTRY`). "
        "Do not edit by hand — edit the registry and re-render; a test enforces "
        "that this file matches. Every contract is bound to its callable and "
        "its claim is asserted in `backend/tests/test_ladder_contracts.py`.",
        "",
        "Each row is a promise in the form **input -> invariant -> action -> "
        "benchmark**, with the theorem-backed part and the honest boundary "
        "called out separately.",
        "",
    ]
    for verdict in order:
        group = [c for c in REGISTRY if c.verdict == verdict]
        if not group:
            continue
        lines.append(f"## {titles[verdict]}")
        lines.append("")
        for c in group:
            lines.append(f"### {c.name}")
            lines.append("")
            lines.append(f"- **binds:** `{c.target}`")
            lines.append(f"- **cost:** {c.cost}")
            lines.append(f"- **input:** {c.input_domain}")
            lines.append(f"- **invariant:** {c.invariant}")
            lines.append(f"- **action:** {c.action}")
            lines.append(f"- **benchmark:** {c.benchmark}")
            if c.proven:
                lines.append(f"- **proven:** {c.proven}")
            lines.append(f"- **limit:** {c.limit}")
            lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    print(render_markdown())
