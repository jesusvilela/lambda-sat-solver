# Ascendency — contemplation, made empirical, and its verdict

Operator prompt: "contemplate the concept of ascendancy." Handled the
way this track handles every concept — turned into a computable
quantity with an input→invariant→action→benchmark contract, tested
against the track's biggest measured lever, and reported at whatever
the test said, not at what the word suggested.

## The concept, rigorously

"Ascendancy" has a precise definition (Robert Ulanowicz, ecological
network analysis): for a flow network T_ij, ascendency
A = TST · AMI = Σ_ij T_ij · log( T_ij·T_·· / (T_i··T_·j) ) — the
organized power of the network, size (throughput) times organization
(average mutual information). Its complement, **overhead** = C − A
(C = development capacity, the same sum with H in place of AMI), is the
network's unconstrained reserve. Ulanowicz's thesis: living systems
climb in ascendency but need overhead to survive perturbation; health
is a *balance* (the "window of vitality"), not maximal ascendency.

(The uploaded manifold document does not contain this concept — its
"ascend" tokens mean agent-migration-up-a-tower. This is the operator's
concept on its own merits, not a doc citation.)

## Made empirical: relative ascendency as a per-instance feature

α = A/C = AMI/H ∈ [0,1] of the variable co-occurrence flow network
(T_ij = #clauses sharing vars i, j) — scale-free, no solving, O(clauses·
width²). `docs/vdis/scripts/ascendency_probe.py`. Measured per family
(κ = the frozen per-family curvature, the track's single biggest lever):

| family (κ mattered) | mean α | frozen κ |
|---|---|---|
| random-4sat | 0.026 | −2.0 |
| random-3sat | 0.173 | −0.25 |
| pigeonhole | 0.217 | −2.0 |
| graph-coloring | 0.294 | −1.0 |
| mutilated-chessboard | 0.423 | −0.5 |

## Verdict: FALSIFIED as a κ-selection rule

α separates families cleanly, but does **not** monotonically predict κ.
Clean counterexample: random-4sat has the *lowest* α of all (0.026) yet
wants the *same* κ=−2 as pigeonhole, while random-3sat sits between them
in α but wants κ=−0.25. No monotone α→κ map exists. As a single
curvature feature, ascendency is dead — reported as such, not adopted.
(Trivial families xor/ladder show high α ≈ 0.6–0.7 but their κ was a
sweep-order tie artifact, so they carry no κ signal and are excluded
above.)

## Where ascendency is NOT dead: it re-describes the whole track's result

The one genuinely load-bearing use is as a *lens on what already
happened*, and here it is not vocabulary — it is the measured pattern
of five generations:

- **EVSIDS is a maximal-ascendency heuristic**: one scalar score, all
  activity channelized into a single sharply-focused ranking. Minimal
  overhead.
- **VDIS's living field is added overhead**: distributed hypercomplex
  state, ε-init noise, multiple axes — unconstrained reserve capacity.
- **The measured five-generation result is exactly Ulanowicz's
  trade-off.** Overhead (diffuse VDIS state) *buys resilience* precisely
  where diffuse search helps — VDIS beats EVSIDS 8–9/13 on fresh
  phase-transition random 3-SAT (v5, held out). Overhead *costs* exactly
  where channelized focus wins — EVSIDS's 2× aggregate dominance is
  entirely pigeonhole, the most rigidly structured family. High
  ascendency wins on structured constraints; overhead wins on diffuse
  ones. This is not an analogy imposed on the data; it is the data.

- **And it explains why the anti-ambiguous tie-break is the mechanism
  that survived falsification.** PA/MF3 keep EVSIDS's full ascendency on
  confident decisions (untouched channelized ranking) and spend overhead
  *only inside near-ties*, where the channel has no information anyway
  (EVSIDS breaks ties by index). That is a tuned ascendency/overhead
  ratio — high order where order pays, reserve where it doesn't — and it
  is the only VDIS mechanism that ever cleared the primary bar. Every
  falsified mechanism (additive torsion, fixed-frame rotors) did the
  opposite: it lowered ascendency *everywhere*, spending overhead on
  confident decisions where it only smeared a good ranking.

## Disposition (disciplined)

No new mechanism is built from this. The κ-feature use is falsified and
parked; the reframing is recorded because it is measured, not imported,
and it sharpens the one forward hypothesis the data already demanded:
the productive VDIS is not "more geometry" but a *selective-overhead*
heuristic — full order by default, reserve spent only at genuine
ambiguity. The v3–v5 tie-break is the first instance of that principle;
a principled next step is an explicit ascendency/overhead controller for
*when* to consult the living field, tested at the ~50-instance/family
scale the v5 report already flagged as the real requirement (n=13 is
exhausted; seed-lottery noise exceeds every mechanism effect). That is a
pre-registration for another session, not an unpinned build in this one.
