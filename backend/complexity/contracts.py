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
        invariant="Nullstellensatz degree over GF(2) (static: least d with "
                  "Sum g_i v_i = 1, deg <= d) = least d at which 1 enters the "
                  "GF(2)-span of {monomial * clause-violation-poly}; the "
                  "rank-deficiency (cokernel of M_d) obstruction — the "
                  "zero-divisor lift",
        action="measures the degree complexity of the (static) Nullstellensatz "
                "proof system; the executable form of the zero-divisor = "
                "rank-deficiency insight. Note PC degree <= NS degree, so this "
                "UPPER-bounds PC degree — it does NOT lower-bound PC/resolution "
                "size on its own",
        benchmark="unit fixtures (unit-contra 1 / chain 2 / PHP(3->2) 4 / "
                  "SAT None / empty 0). NS and width are INCOMPARABLE: NS > "
                  "width on PHP (4 vs 2), NS < width on Tseitin K4 (3 vs 4) — "
                  "orthogonal obstructions in different proof systems",
        proven="NS degree is the complexity measure of the Nullstellensatz "
               "system (Beame-Impagliazzo-Krajicek-Pitassi-Pudlak); high NS "
               "degree = hard for Nullstellensatz. It does NOT certify a PC or "
               "resolution size bound (PC degree <= NS degree; Tseitin < width)",
        limit="a carrier for its OWN (weak, static) system only — incomparable "
              "to resolution width, not a CDCL/PC hardness bound; exponential; "
              "the G2/symmetry channel reduction is char-2 obstructed (LIE_TELOS)",
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
        name="cross_algebra_depth",
        target="cross_algebra_depth",
        cost="exact, exponential (runs both width and NS-degree)",
        input_domain="UNSAT CNFFormula within both invariants' guards",
        invariant="obstruction depth in each proof algebra we can measure "
                  "(resolution width, GF(2) Nullstellensatz degree) and the "
                  "minimum over them -- the 'shallow-Emperor' depth",
        action="makes the portfolio principle intrinsic: since the two depths "
                "are incomparable, best = min(...) beats either algebra alone "
                "on a mixed workload -- why portfolio solvers win",
        benchmark="PHP best = width 2 (< NS 4); Tseitin K4 best = NS 3 "
                  "(< width 4); on the pair the portfolio (2,3) strictly beats "
                  "width-only (2,4) and NS-only (4,3)",
        proven="the incomparability itself (NS vs width) is verified; portfolio "
               "= min is elementary",
        limit="a DEMONSTRATOR, not a fast router -- both depths are exponential "
              "to compute; the practical shadow is the solver's real "
              "portfolio/restart/heuristic switching",
        verdict=STRUCTURE,
    ),
    InvariantContract(
        name="xor_extraction.extract_xors (frame detector)",
        target="backend.xor_extraction.extract_xors",
        cost="poly-time O(clauses * arity) (capped by max_arity)",
        input_domain="any CNFFormula",
        invariant="recovered XOR/parity constraints and xor_clause_fraction = "
                  "share of clauses that form complete parity groups",
        action="cheap detector of the GF(2) shallow frame: high fraction => the "
                "algebraic (Gaussian-elimination) frame is shallow here; the "
                "practical poly-time shadow of cross_algebra_depth, sibling of "
                "binary_clause_check (the 2-SAT frame detector)",
        benchmark="Tseitin K4 fraction 1.0 (GF(2) shallow), PHP(3->2) 0.0 "
                  "(resolution shallow); single 3-XOR recovered with correct rhs",
        proven="XOR CNF encoding is exact (2^(k-1) clauses of fixed negative-"
               "literal parity); recovery is sound for complete groups",
        limit="detects only COMPLETE short parity groups (<= max_arity); a "
              "frame discriminator, not a solver, and not wired into routing "
              "until benchmarked (matching policy.py's evidence discipline)",
        verdict=STRUCTURE,
    ),
    InvariantContract(
        name="xor_extraction.gf2_xor_refutation (sound fast-path)",
        target="backend.xor_extraction.gf2_xor_refutation",
        cost="poly-time (XOR recovery + GF(2) Gaussian elimination)",
        input_domain="any CNFFormula",
        invariant="refuted = the recovered XOR subsystem is inconsistent over "
                  "GF(2) (=> formula UNSAT, a sound certificate); decides_fully "
                  "= the XORs cover the whole formula",
        action="engine-independent UNSAT fast-path in the algebraic frame, "
                "sibling of binary_clause_check (the 2-SAT-frame fast-path); "
                "run before CDCL to short-circuit parity-inconsistent instances",
        benchmark="FRAME_BENCHMARK_REPORT: on Tseitin-expander returns UNSAT in "
                  "<<1ms where Kissat AND CaDiCaL time out (>20s at nv=100); "
                  "PAR-2 2.858s -> 0.036s as a router; soundness 53/53 vs Kissat",
        proven="recovered XORs are logically entailed (exact CNF encodings), so "
               "an inconsistent XOR subsystem soundly refutes the whole formula; "
               "Tseitin resolution width is Omega(n) (BSW) hence CDCL-exponential",
        limit="only refutes via the parity fragment -- inconclusive on formulas "
              "whose contradiction is not in the XOR core (falls through to CDCL)",
        verdict=CARRIER,
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
