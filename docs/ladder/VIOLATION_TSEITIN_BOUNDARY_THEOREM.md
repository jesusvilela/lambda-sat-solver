# Tseitin's exact graph-boundary obstruction

**29 October 2026 | dev/kakeya-violation-frame.** P = elementary classical finite graph theorem with proof below; M = bounded tests and external CDCL results; H/S = any proposed bridge to Kakeya, local smoothing, n-manifolds, or a new asymptotic SAT advantage. This is NOT a new theorem in the mathematical literature.

## Typed GF(2) boundary (not the real signed Laplacian)

Let G=(V,E) be a finite undirected multigraph without self-loops. Treat each edge as a Boolean variable and each vertex as an XOR parity equation with charge b_v. The linear boundary is

    partial: GF(2)^E -> GF(2)^V,
    (partial x)_v = XOR_{e incident to v} x_e.

For each connected component C define q_C(b)=XOR_{v in C} b_v.

**Classical proposition (P):**

    im(partial) = {b : q_C(b)=0 for every connected component C}
    rank(partial) = |V| - number_of_components(G)
    dim coker(partial) = number_of_components(G).

**Proof (necessity).** XOR all vertex equations over C. Each internal edge occurs exactly twice, hence cancels mod 2. Thus q_C(b)=0.

**Proof (sufficiency).** Choose a rooted spanning forest, set non-tree edge bits to zero, and traverse each tree from leaves to root. At a non-root vertex v, set its parent edge bit equal to the residual charge at v and XOR that value into its parent's charge. All non-root equations hold by construction, and each root residual equals q_C(b), which is zero by hypothesis. This constructs x in O(|V|+|E|) from adjacency lists. Since these component conditions are independent and sufficient, rank(partial)=|V|-#components, while the cokernel has one GF(2) degree per component. Equivalently, component indicator vectors span the left kernel of partial.

The implementation in [violation_tseitin_boundary.py](../../backend/violation_tseitin_boundary.py) returns either verified edge bits (SAT) or an odd-charge connected-component witness of the XOR contradiction (UNSAT). Its tests check all charge vectors against an independent brute-force image on seeded small graphs, including multiedges, disconnected components and isolated vertices.

### CNF recovery contract

Use the existing λSAT complete XOR-group extractor. Admit the graph-boundary specialization only if every original clause belongs to a recovered XOR encoding and every declared variable appears in **exactly two distinct XOR equations**, determining that edge's two endpoint vertices. Reconstructed SAT assignments are independently replayed on the original CNF. Partial-XOR, non-graph-XOR and unmatched-clause inputs return NOT_TSEITIN. The module leaves the existing XOR extractor, certified solver decisions, ACAF, and main untouched.

This finite boundary map is DIFFERENT from the real signed clause-variable graph Laplacian developed in the earlier round. The latter has energy sum_(c,v) (z_c - sigma_cv z_v)^2 and a kernel indexed by balanced signed components; its variables are real-valued at clause and variable vertices. The characteristic-two boundary map acts between edge and vertex GF(2) chains. In particular, DO NOT transfer real-Laplacian rank, spectral positivity or Kakeya smoothing claims to partial*partial^T over GF(2): the characteristic-two calculation requires its own proof. The obstruction used here is the left cokernel of partial.

## External CDCL and GF(2) positive control (M)

[Disjoint-seed exploratory protocol, written after the first pilot](VIOLATION_CDCL_PARITY_ADDENDUM.md): generator seeds 100–105, declared variables 48/72/96, six generator families, 3 independent signed-relabeling Glucose4 runs per formula, conflict budget 5,000. There were **108 distinct labeled CNFs and 324 solver calls; 2.16% UNKNOWN/censored**.

The existing λSAT GF(2) frame independently resolved **36/36 generated fully parity-encoded Tseitin CNFs**: 18 SAT with a verified algebraic model and 18 UNSAT by inconsistency of global charges. It returned INCONCLUSIVE for all 72 random 3-CNF examples.

Leave-one-generator-family-out MAE for log2(1+budget-capped CDCL conflicts), lower is better:

| Formula-only predictors | MAE |
|---|---:|
| Classical (degree, unsigned cycles, density, polarity, XOR coverage) | 2.2298 |
| Classical + signed connection | 2.2501 |
| Classical + GF(2) rank / consistency | 1.3121 |
| Classical + GF(2) + support-rewired null | 1.3051 |
| Classical + GF(2) + signed connection | **1.2623** |

The main improvement is from the existing GF(2) algebraic frame, not an inferred Kakeya inequality. The signed connection offers a modest *post-hoc, exploratory* incremental improvement after conditioning on rank, but on the held-out largest n=96, signed and null errors were 1.16224 and 1.16152 respectively (null fractionally better). This does not establish a robust distinctive signal.

GitHub Actions median feature times: ~3.69 ms for baseline feature preparation; an additional ~4.42 ms for signed/null preparation; ~0.85 ms for the GF(2) gate audit; versus ~0.32 ms for a Glucose4 solve. These stages have overlapping work, so they are not additive production timing predictions, but their scale defeats a current **routing speedup** claim.

The raw per-instance solver results, oracle statuses and exact GF(2) gate controls are preserved as JSON workflow artifacts. The prism family shares one graph topology per size; its differently charged examples are not independent nonisomorphic graphs. The rewired cubic family uses independently switched graphs, and tests check seeded nonisomorphism. The experiment retains the earlier null-negative DPLL results and the first 36-formula CDCL pilot.

## Reproduction and next formal step

    python -m pytest -q backend/tests/test_violation_tseitin_boundary.py
    python -m pytest -q backend/tests/test_violation_cdcl_topology.py backend/tests/test_violation_cdcl_parity.py
    python docs/ladder/scripts/violation_cdcl_parity_probe.py --seeds 6 --seed-start 100 --sizes 48 72 96 --orbits 3 --budget 5000 --json

A meaningful Lean target is the image/cokernel equivalence for a finite graph's GF(2) boundary together with its constructive spanning-forest witness. That would be a formalized classical result. A geometric or analytic lift would need an additional typed transport theorem, not yet demonstrated.
