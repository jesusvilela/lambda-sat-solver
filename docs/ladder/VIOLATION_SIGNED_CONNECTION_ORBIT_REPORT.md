# The signed incidence connection and the relabeling orbit: an ETH/Kakeya bridge audit

**29 October 2026 | development branch: dev/kakeya-violation-frame | source: [lambda-sat-solver](../../README.md).**

Evidence typing: **P** = elementary finite signed-graph identities, with an explicit proof below and numerical verification, **M** = small synthetic measurements, **R** = failed predictive lift *within the tested scope*, **S/H** = prospective analogy/bridge to wave smoothing, Kakeya, n-manifold geometry, SAT complexity or solver runtime. None of these is a formal Lean proof or an asymptotic SAT result.

## Why relabel the observer, not only the formula?

The previous cross-instance target was log2(1+DPLL recursive calls) for a fixed lexicographic variable order and False-first phase. Its cost changes under Boolean-variable permutation and complement, although satisfiability and the abstract formula are unchanged.

Witness: one generated random-3SAT instance (generator seed 0) takes 7 recursive calls in its original presentation; on 40 seeded logically equivalent signed relabelings, it takes 7 to 21 calls. The original target was thus partly a property of the *coordinate/branching convention*. This does not invalidate its earlier negative result; it narrows its meaning.

The new target samples 8 reproducible signed variable relabelings and takes the median of log2(1+DPLL nodes). **A finite sampled orbit median is not an exactly gauge-invariant functional.** It reduces dependence on the arbitrary representation; no claim of continuous Hamiltonian, holonomy flow, or quantum computation is implied.

## A genuinely typed finite connection

Normalize repeated literals and ignore tautological clauses. Define a bipartite factor graph with clause vertices C, variable vertices V and signed edge sigma(c,v) in {+1,-1} recording literal polarity. For any closed factor-graph walk gamma, set

    H(gamma) = product_{e in gamma} sigma(e) in {+1,-1}.

A negative cycle H=-1 is an obstruction to finding vertex spins g(node) in {+1,-1} satisfying sigma(c,v)=g(c)g(v) on every edge. Conversely, if all cycle products equal +1, a spanning-forest propagation constructs those spins. This equivalence follows directly from path multiplication; it is not a SAT contradiction theorem.

For a clause pair c<d, let p_cd be the number of variables v shared by c and d with sigma(c,v)sigma(d,v)=+1, and q_cd the number shared with product -1. Then

    number_of_4cycles = sum_{c<d} choose(p_cd+q_cd, 2),
    number_of_negative_4cycles = sum_{c<d} p_cd*q_cd.

This exact combinatorial identity underlies the cheap signed-square diagnostic (O(L + sum_v degree(v)^2)), independently differential-tested against literal enumeration. Negative cycles may have length >=6 even when no 4-cycles exist.

The actual finite connection Laplacian is L_sigma = D - A_sigma, where A_sigma is the symmetric signed adjacency matrix of that bipartite graph. For any real node vector z,

    z^T L_sigma z = sum_{(c,v) edge} (z_c - sigma(c,v) z_v)^2 >= 0.

Hence L_sigma is positive semidefinite. On a connected component, the energy is zero exactly when all edge relations z_c=sigma(c,v)z_v hold. If the component is balanced this leaves one free real scalar (kernel dimension 1); if it has a negative cycle all coordinates must vanish (kernel dimension 0). **Therefore nullity(L_sigma) equals the number of balanced connected components**, isolated vertices included.

Gauge switching sigma'_{uv}=g_u sigma_{uv}g_v yields L_sigma'=G L_sigma G, preserving the eigenvalue multiset. Variable complementation and permutations give particular such transformations plus vertex permutations. Note that switching *clause* signs is a valid graph gauge transformation but is not generally a semantics-preserving Boolean formula transformation.

Tests include 100 seeded small matrices comparing the edge-sum energy with z^T L z, PSD/eigenvalue nullity, 120 randomly generated CNFs checking four-cycle counts against independent enumeration, and signed-relabeling invariance.

**Boundary:** a balanced factor graph may encode an UNSAT CNF (x AND not-x), and an unbalanced graph may encode a SAT CNF ((x OR y) AND (x OR not-y)). Nullity and negative holonomy cannot be used for certified SAT/UNSAT decisions.

## Matched controls borrowed from the Canary direction, not its unverifiable claims

Control 1: the nine classical structural predictors already include clause width, density, literal polarity imbalance, variable degree dispersion and XOR pattern recognition. The variance feature is inspired by the private Canary flavor analyzer; the claimed Z2xZ2/A4 symmetry tags are not imported.

Control 2: seeded **checkerboard sign switches** on two clauses sharing two variables, changing [[+,-],[-,+]] into [[-,+],[+,-]]. These preserve every clause's positive literal count, every variable's positive occurrence count, the entire unsigned clause-variable incidence, clause widths and degrees. They are a matched *feature null*, not a semantics-preserving SAT transformation. A null with **zero successful switches is not a useful randomization control**. In the toy corpus, only about 72%-74% of formulas admit at least one switch with the chosen budget; the pigeonhole family has zero. The report explicitly tracks this failure.

All six generator families are held out in turn; model fitting and standardization occur only on the other five. We compare a constant, the classical structural baseline, structure+signed connection, structure+margin-matched null, and signed connection alone. Fixed ridge penalty alpha=10. No solver result influences feature extraction.

## Exploratory local measurements (M)

Across 10 **orientation/null-seed offsets** of the *same generated formula set*, 8 signed-relabeling DPLL runs per formula, and 32 target checkerboard switches. Entries are LOFO mean absolute prediction error on log2(1+DPLL recursive calls); **lower is better**.

| Formulas (6 families) | Raw target: structural / signed / null | Orbit-median target: structural / signed / null | Signed wins vs structural (10 offsets) |
|---|---|---|---|
| 72 | 0.67735 / 0.71387 / 0.70533 | **0.57845** / 0.64165 / 0.63634 | 0/10 |
| 144 | 0.64016 / 0.65144 / 0.64089 | **0.53892** / 0.60951 / 0.60693 | 0/10 |
| 192 | 0.61441 / 0.67751 / 0.67863 | **0.55051** / 0.64702 / 0.64601 | 0/10 |

At 192 formulas the raw reference median varies by about 0.94 log2 units across relabelings for a typical instance (median range across the 10 offsets). Across all 3 corpus sizes, the signed connection underperforms the classical structure-only predictor on the orbit target, and the margin-matched sign null performs similarly to the measured signed connection. Some individual held-out families show minor gains, but the losses on other families dominate; family templates are small and repeated.

Illustrative local Python 3.13 timing for 192 formulas: median classical feature extraction about **0.068 ms**, signed+classical feature extraction about **0.268 ms**, and 8-run orbit reference computation about **1.04 ms**. These are not comparable production solver timings. The null randomization cost is *not* included in the signed feature's stated cost, because it is a diagnostic control rather than a proposed routing feature.

The 72-formula results are reproduced in dedicated branch CI with raw machine-readable JSON retained as an artifact; larger 144/192 runs are available from the same code and commands. Ten offsets on the same base formula set do **not** constitute ten independent held-out datasets. The small PHP corpus cycles through three base sizes, and the Tseitin corpus cycles through three graph topologies. We cannot infer population confidence intervals from the repeated offsets alone.

**R, bounded:** retire the claim that this specific signed-incidence/4-cycle connection predicts held-out toy DPLL effort better than conventional structural features. This supersedes the attempt to rescue the earlier centered parity-pass spectrum with another scalar. Keep the finite spectral and gauge identities as P.

## Commands

    python -m pytest -q backend/tests/test_violation_connection.py backend/tests/test_violation_laplacian.py backend/tests/test_violation_orbit.py
    python docs/ladder/scripts/violation_orbit_probe.py --seeds 12 --offsets 3 --json
    python docs/ladder/scripts/violation_orbit_probe.py --seeds 24 --offsets 10 --json
    python docs/ladder/scripts/violation_orbit_probe.py --seeds 32 --offsets 10 --json

All runs are deterministic modulo elapsed-time measurements and standard numerical tolerances.

## What remains open (H)

The next useful test is not another feature expansion on these six families. Build genuinely unseen graph topology generators (multiple cubic expanders, distinct community graphs, nonisomorphic PHP generalizations), preserve a large-n view, and use external certified CDCL runtime with all feature costs charged. Pre-register which feature predicts what, against degree/width/sign-matched nulls that actually mix. If the goal is a Kakeya or local smoothing lift, specify a valid finite-to-continuous oscillatory extension operator and an estimate; the finite Z2 connection Laplacian alone does not supply it.

References: [ETH paper](https://github.com/openai/math/blob/main/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026/paper.pdf), [local smoothing/Kakeya paper](https://github.com/openai/math/blob/main/preprints/Local-smoothing-for-the-Euclidean-wave-equation-October-25-2026/paper.pdf), [prior negative report](VIOLATION_CROSS_INSTANCE_REPORT.md).
