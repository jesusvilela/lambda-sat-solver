# Violation-space geometry: ETH x Kakeya (experimental)

**2026-10-29 | development branch only | H: hypothesis, S: geometric translation, M: bounded pilot.** This is a research probe, not a new certified solver frame.

Sources: OpenAI, [ETH manuscript](https://github.com/openai/math/blob/main/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026/paper.pdf), especially clause-violation parity tests and sparse common-zero systems; [local smoothing manuscript](https://github.com/openai/math/blob/main/preprints/Local-smoothing-for-the-Euclidean-wave-equation-October-25-2026/paper.pdf), especially spherical extension and Kakeya tube overlap. See [Lean ETH scope](https://github.com/openai/math/blob/main/lean/docs/378.md) and [Lean local smoothing scope](https://github.com/openai/math/blob/main/lean/docs/079.md). External verification of research claims is separate from released formal statements.

## Finite mathematical object

For a CNF F with n **declared** Boolean variables and m clauses, let the violation signature v_F(x) in GF(2)^m have j-th bit 1 iff x violates clause j. A binary matrix A of check rows defines H_A(F) = {x : A v_F(x) = 0}. All models of F lie in H_A(F), but the converse is false in general. Equivalence on the complete assignment domain holds exactly if

    ker(A) intersect (im(v_F) minus {0}) = empty.

A retained nonsatisfying assignment is a **spurious survivor**, not evidence of satisfiability. This experimental code enumerates up to 2^12 assignments and never returns a solver verdict. It is not OpenAI's deterministic parity construction, expander coding, interpolation counter or claimed subexponential algorithm.

For each check row a, define a finite *nonmodel survivor set* T_a = {x : v_F(x) != 0 and <a,v_F(x)> = 0 mod 2}. Exclude genuine models, which would otherwise occur in every pass set. Define the incidence operator I[a,x] = 1[x in T_a] / sqrt(|T_a|) for nonempty T_a, otherwise 0; and Gram G = I I^T. Thus G[a,b] = |T_a intersect T_b| / sqrt(|T_a||T_b|), whenever both sets are nonempty. Record the top eigenvalue, mean pairwise overlap cosine and maximum multiplicity. **These sets are not Euclidean tubes; no Kakeya maximal inequality, wave equation estimate, or Hausdorff-dimension theorem applies without an entirely new bridge.**

## Pre-registered discriminating pilot

- **Object:** finite clause-violation signatures, with n<=12 and m<=128; count all declared variables, including unused ones.
- **Candidate action:** seeded greedy selection of up to 8 rows from singleton checks and bounded samples of weight-2 and weight-3 checks. Train only on two-thirds of assignment states.
- **Controls:** a trained singleton-only greedy baseline and four seeded row-weight-matched random check matrices. Evaluate all on identical held-out states and report the full truth-table equivalence audit separately.
- **Prediction H:** learned sparse checks may decrease spurious held-out survivors relative to weight-matched random rows; Gram spectral features might independently predict difficulty beyond classical density, XOR rank and frame count.
- **Kill conditions:** withdraw the empirical generalization claim if repeated held-out instance and split seeds erase the effect. Retire the *Kakeya-inspired predictive lift* if Gram statistics offer no incremental out-of-sample predictive signal over ordinary structural features. A low survivor count alone is NOT such a prediction.
- **Promotion:** all observations remain M on specified small instances. A theorem needs its exact statement and proof. A solver win needs controlled runtime including feature computation; a general complexity result is not implied.
- **Safety:** no production router, scout, certified SAT/UNSAT branch, DRAT or trusted-base changes.

## Reproduction

    python -m pytest backend/tests/test_violation_geometry.py -q
    python docs/ladder/scripts/violation_geometry_probe.py
    python docs/ladder/scripts/violation_geometry_probe.py --json
    python docs/ladder/scripts/violation_geometry_probe.py --split-seed 5

This requires neither Kissat nor drat-trim. All random sources are local and seeded. Included families: odd-charge K4 Tseitin, pigeonhole 4-to-3, two XOR triples, random 3-SAT, planted 3-SAT.

**One split exploratory local run** (split seed 41, candidate seed 19, four random controls):

| Family | #SAT | Learned held-out spurious | Greedy singleton held-out spurious | Matched random mean |
|---|---:|---:|---:|---:|
| Odd-charge K4 | 0 | 5 | 15 | 5.00 |
| Pigeonhole 4-to-3 | 0 | 4 | 126 | 35.00 |
| Two XOR triples | 16 | 1 | 13 | 5.00 |
| Random 3-SAT | 4 | 1 | 20 | 10.75 |
| Planted 3-SAT | 6 | 4 | 22 | 9.00 |

These are toy cases. One family **ties** the random null. Twelve additional local assignment-split seeds show K4 beats the four-null mean on 6 splits and loses on 6, so there is no stable K4 advantage yet. Learned checks use labelled training assignments—unavailable to a scalable solver without equivalent work—so better hold-out rejection than random checks does not establish useful solver performance.

## Cross-instance continuation and correction (2026-10-29)

The above proposed bridge has now been implemented and tested, including sampling, leave-one-generator-family-out ridge prediction, centered incidence, a signed triangle statistic and matched random controls. The result is **negative for the proposed hardness predictor in this bounded regime**: see [VIOLATION_CROSS_INSTANCE_REPORT.md](VIOLATION_CROSS_INSTANCE_REPORT.md) for full numbers, seed repetitions and Canary provenance. The finite parity and gauge identities survive; predictive advantage and scalability have not been established. Do not promote the earlier five-instance pilot into a solver result.
