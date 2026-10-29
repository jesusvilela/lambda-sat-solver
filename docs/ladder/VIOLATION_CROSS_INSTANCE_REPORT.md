# ETH x Kakeya: cross-instance falsification and centered signed cycles

**2026-10-29. Development branch: dev/kakeya-violation-frame. Status M/R for the predictive hypothesis, P for elementary finite identities, S for Kakeya vocabulary.** The production SAT path remains untouched.

## Why this round exists

The original [finite pilot](ETH_KAKEYA_VIOLATION_GEOMETRY.md) trained sparse parity checks on a fraction of *assignments from the same formula*, then evaluated other assignments of that formula. That cannot establish generalization to unseen formulas; moreover, its Gram spectrum required complete enumeration.

This round adds **bounded assignment sampling as a feature extractor**; an independent unit-propagating **DPLL search-node counter as a reference target**; and **leave-one-entire-generator-family-out** (LOFO) prediction. The model is deterministic fixed-penalty ridge regression with all standardization fit only on training families. No proof, UNSAT verdict, CDCL solver, or Lean theorem is invoked by the predictor.

## Canary provenance, with corrections

Source: private [jesusvilela/-SAT_Research_Canary](https://github.com/jesusvilela/-SAT_Research_Canary), especially [flavor_analyzer.hpp](https://github.com/jesusvilela/-SAT_Research_Canary/blob/main/backend/cpp/flavor_analyzer.hpp) and [evolve_heuristics.py](https://github.com/jesusvilela/-SAT_Research_Canary/blob/main/studies/evolve_heuristics.py).

We borrow the **actual low-cost measurements** (degree dispersion) and the idea of **family-stratified sampling and ablation**. We do **not** import the C++ thresholds calling low-variance 3CNF "Z2_x_Z2" or high-variance CNF "A4": those thresholds are classifiers, not group identification proofs. We do **not** import sample selection based on known solve times; that would leak the target. The Canary studies' simulated/mocked benchmarking results and cloned synthetic instances are not evidence here.

## Bounded representation

For F, evaluate its violation vector v_F(x) only on 48 distinct uniformly selected Boolean assignments (24 for choosing sparse checks, 24 held out for computing features). Sampling is strictly less than 2^n, n<=12; enumerated truth tables are not used to construct *cross-instance predictors*.

The original incidence matrix uses row check-pass indicators restricted to nonsatisfying sampled assignments. The new **centered covariance** removes the large random-check overlap background. Write b_i(x) = 1 when check i passes and v_F(x) != 0, p_i=E[b_i] over sampled nonmodels, and remove rows with p_i in {0,1}. Set

    Z_i(x) = (b_i(x)-p_i)/sqrt(p_i*(1-p_i))
    C_ij = E[Z_i(x)*Z_j(x)].

C is a positive-semidefinite correlation Gram matrix. We record its largest eigenvalue divided by its number of nonconstant rows, mean absolute off-diagonal correlation, and signed triangle statistic.

    f_triangle = sum_{i<j<k, Cij*Cjk*Cki<0} |Cij*Cjk*Cki|
                 / sum_{i<j<k} |Cij*Cjk*Cki|,

where only edges with absolute correlation >=0.10 participate and a zero denominator gives f=0. This is a signed **triangle** statistic, *not* the frustration index of an arbitrary signed graph or a CNF contradiction certificate.

**Exact finite invariance (P).** Flipping the orientation of any row's binary indicator maps Z_i to -Z_i. For a diagonal sign matrix D, C' = D C D. Consequently the entire eigenvalue multiset and the sign of each triangle product C_ij C_jk C_ki are invariant. This finite gauge identity is tested. It says nothing by itself about NP hardness, holonomy of a nontrivial connection, or a Kakeya bound.

## Held-out family evaluation (M)

Six seeded families: random 2-SAT, random 3-SAT, planted 3-SAT, random 3-XOR, charged cubic Tseitin graph CNFs (K4, triangular prism, cube), and pigeonhole CNFs. PHP has only three base sizes and Tseitin only three base graphs, each repeatedly relabeled; **these are not independent graph topologies**, so statistical generality is still limited.

Targets: log2(1 + deterministic lexicographic DPLL recursive calls) with unit propagation, **not modern CDCL runtime**. Nine baseline structural features include degree dispersion inspired by Canary, plus n, m/n, clause width, polarity and XOR-pattern indicators. Additional feature groups include sampled violation histograms, learned sparse-check pass/uncentered overlap, random-check matched-null overlap, and centered signed-cycle features.

All errors below are LOFO **mean absolute errors**, averaged over ten independently seeded *assignment-sampling* offsets on the same fixed formula corpus per size. Lower is better.

| CNFs | Structural only | + sampled violations | + learned uncentered overlap | + centered overlap / triangles |
|---:|---:|---:|---:|---:|
| 72 (12 per family) | **0.67735** | 0.72411 | 0.72411 | 0.71460 |
| 144 (24 per family) | **0.64016** | 0.67691 | 0.68232 | 0.68559 |
| 192 (32 per family) | **0.61441** | 0.70232 | 0.70679 | 0.70472 |

Across ten repeats, the centered variant improves on structure-only in **3/10**, **0/10**, and **0/10** cases respectively; the uncentered learned variant improves in **1/10**, **0/10**, and **0/10** cases. Random weight-matched check features are tracked separately by the script and do not rescue the predictor. The modest improvement of centered features on one initial 72-formula split was not replicated.

Illustrative local Python run (72 CNFs): median complete geometry feature extraction ~4.4 ms, structural-only extraction ~0.08 ms, reference DPLL itself ~0.09 ms. These timing readings are noisy, environment-specific and *not* throughput benchmarks. The feature extraction is already materially more expensive than the toy reference solver.

**Correction / R (bounded scope).** Retire the claim that this specific learned incidence/signed-triangle representation predicts held-out toy DPLL effort better than classical structure, on the tested generators and evaluation regime. Do NOT retire the elementary algebra or assert it cannot work with other observables. This negative result was measured after exploring feature variations; centered-feature additions were exploratory, not pre-registered confirmatory tests.

## Reproduction and exact scope

    python -m pytest -q backend/tests/test_violation_geometry.py backend/tests/test_violation_spectral_null.py backend/tests/test_violation_cross_instance.py
    python docs/ladder/scripts/violation_cross_instance_probe.py --seed-count 12 --replicates 1
    python docs/ladder/scripts/violation_cross_instance_probe.py --seed-count 24 --replicates 10 --json
    python docs/ladder/scripts/violation_cross_instance_probe.py --seed-count 32 --replicates 10 --json

The CLI outputs *every* predictor and each held-out family in JSON, plus feature extraction costs. A branch-only [GitHub Actions lane](../../.github/workflows/violation-geometry-lab.yml) runs the tests and a small reproducibility probe without installing Kissat/drat-trim. A green lane proves only bounded contracts and successful execution.

## Next admissible bridge (H)

First seek a much cheaper **unlabeled** structural projection, under matched size/width/degree controls, and test on genuinely new graph families. Next evaluate whether incremental predictive information survives **CDCL** effort, with time/memory cost charged to the predictor; no routing integration until it does. A continuous Kakeya maximal estimate or connection-Laplacian smoothing bound would require a separately constructed, typed finite-to-continuous transport theorem. No such theorem is claimed here.
