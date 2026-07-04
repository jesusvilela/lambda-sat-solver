# PARKED — ideas outside the §5 phase plan (per §0 anti-drift rule)

Each entry records why it was parked and what would un-park it, so
nothing gets silently dropped or silently implemented.

## Connection-Laplacian frustration feature as a per-instance κ policy (parked 2026-07-03)

**The one parked idea here with a complete contract.** Input: the
binary-clause implication graph as a ℤ/2 gain graph. Invariant:
smallest eigenvalue of its connection Laplacian (frustration/imbalance
measure — math already verified in the connection_laplacian_lean
review). Action: select κ per instance from the feature, replacing the
per-family lookup in `backend/vdis/kappa_table.py`. Benchmark: held-out
κ-selection accuracy / decisions-to-solve vs. the frozen family-keyed
table. Data path exists: the Phase 2 sweep ran 93 instances × 4 κ × 2
algebras; per-instance winners just need a re-run with per-instance
(not per-family) aggregation (~15 min).

Parked because: (1) §8 parks connection-Laplacian work for Track B1;
(2) 93 instances / 14 family cells cannot support fitting a feature→κ
map without overfitting; (3) any adaptive config selection introduced
during Phase 3 would violate §7's no-hyperparameter-rescue rule.
Un-parks: after Phase 3 reports, as a new pre-registered experiment
with held-out instance generation.

## Multiplicative-weights config bandit — the implementable kernel of "Garrabrant induction for tuning" (parked 2026-07-03)

The executable content of logical-induction-style tuning is a
multiplicative-weights ensemble (Hedge/EXP3 — the bunny kernel). The
distinctively-Garrabrant machinery (market prices over undecidable
sentences, self-referential coherence) adds nothing over EXP3 for a
finite grid where every arm is directly measurable: you don't need a
market to price a sentence you can evaluate.

Parked because the current config grid is exhaustively sweepable
(Phase 2 sweep: 858 s total) — a bandit would add estimation variance
to save compute that doesn't need saving. Un-parks: if the config
space outgrows exhaustive sweep (continuous λ, more algebras,
per-instance configs), as standard bandit machinery with pre-registered
budgets, credited to the bandit literature.

## Payor's Lemma for hyperparameter search (parked 2026-07-03, no contract)

No input→invariant→action→benchmark contract was constructible. The
lemma's engine is a self-referential trust structure — something must
play the role of □(□x → x), a reasoner conditioning on provability of
its own or another's claim. A hyperparameter sweep has no such
structure: configurations do not reason about one another, they get
measured. If Payor-style reasoning applies anywhere in this system it
is the portfolio-orchestration layer (co-running solvers making
commitments conditional on each other's behavior — the three-layer
coordination discussion from the prior session), which is not tuning.
Un-parks: only with a concrete construction showing what object plays
the modal role — resemblance at the "choosing under uncertainty" level
is exactly what this file exists to catch.
