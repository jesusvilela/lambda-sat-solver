# VDIS Track B1 — Phase 3 pre-registration

**Committed BEFORE any Phase 3 benchmark run. Per §7: "Record before
Phase 3 runs; do not edit after."** Code under test: the Phase 2
implementation as of commit `8cfc329` (branch
`claude/2026-sota-benchmark-xyp1zh`). The predictions P1–P4 and stop
conditions S1–S4 are the spec's own (§7), restated here with every
degree of freedom pinned.

## Instance sets

### B13′ — scaled analogue of the prior session's 13-instance set (DEVIATION, declared here)

The spec says "the 13-instance set from the prior session." That set
(pigeonhole with 9–12 pigeons; random 3-SAT at ratio 4.267 with
n ∈ {150, 200, 250} × seeds {1, 2, 3}) was built to benchmark
**Kissat**, where its hardest instance took ~92 s ≈ tens of millions of
conflicts. It is infeasible for the Python reference solver: a sizing
probe (this session) measured php_9_8 alone at 355 s / 74 282 conflicts
under EVSIDS, and the original set *starts* above that and ends ~3
orders of magnitude harder. Running it would take weeks per config.

B13′ keeps the exact shape (4 pigeonhole + 9 phase-transition random
3-SAT, same ratio, same seed convention) at reference-solver scale:

- `pigeonhole(n)` for n ∈ {5, 6, 7, 8} (n pigeons, n−1 holes; repo
  generator).
- `random_ksat(n, int(n·4.267), k=3, seed=s)` for
  n ∈ {50, 75, 100} × s ∈ {1, 2, 3}.

Probed hardest cell: php_8_7 ≈ 25 s under VDIS. Probe runs used config
(C, λ_τ=0.1, λ_χ=0.1) and EVSIDS on php_{5,6,7,8} and 4 r3sat cells
only; no other Phase 3 data has been generated at pre-registration
time.

### Suite component (DEVIATION, declared here)

"Full suite" is evaluated as quick + medium (93 instances), consistent
with the Phase 0 and Phase 2 precedent (both documented the same
deviation; `StandardSuites.full()`'s 500 instances at 300 s Kissat-scale
timeouts are out of reach for the Python solver).

### Held-out P4 set

The κ table was fit on quick+medium — evaluating P4 on those same
instances would be in-sample and biased toward passing. P4 therefore
uses **fresh instances**: the medium suite's seeded-family parameters
with seeds 1000–1004 —

- random-3sat: (n=50, m=213) × 5 seeds and (n=100, m=426) × 5 seeds
- random-4sat: (n=40, m=397) × 5 seeds
- graph-coloring: (10 vertices, 3 colors, p=0.5) × 5 seeds and
  (15, 4, 0.4) × 5 seeds

Deterministic families (pigeonhole, mutilated-chessboard, ladder,
xor-chain with fixed seeds) cannot be held out and are **excluded from
P4**, so P4 is judged over 3 families: random-3sat, random-4sat,
graph-coloring. The spec's "≥ 2 families" threshold is kept: **P4
passes iff per-family κ beats global κ=−1 on ≥ 2 of these 3.**

## Configurations

- **VDIS sweep** (8 configs): algebra ∈ {C, H} × λ_τ ∈ {0, 0.1} ×
  λ_χ ∈ {0, 0.1}; fixed: dim=32, β=0.1, η=1, γ=0.95, ε=10⁻³, μ=0.05,
  κ per (algebra, family) from the frozen `kappa_table.py`
  (DEFAULT_KAPPA=−1 for families not in the table). χ from
  `compute_chi`.
- **Baselines**: EVSIDS (defaults), LRB (defaults), Random.
- **Seeds**: 0–4 for every heuristic on every run (EVSIDS and LRB are
  seed-insensitive by construction; the median over seeds is then the
  single deterministic value — noted, not hidden).
- **Conflict cap**: 100 000 per run. A capped run = unsolved =
  +∞ decisions for all comparisons.

## Metric and decision rules

Metric: **decisions-to-solve** (`stats.decisions`), summarized per
(instance, config) as the **median over the 5 seeds**.

- **Winner selection**: the single sweep config maximizing the number
  of B13′ instances where its median decisions < EVSIDS's median;
  ties broken by smaller total median decisions over the 13. (The spec
  itself defines P1 as "best of C/H at swept λ", i.e. it sanctions
  selecting the winner on the same data P1 is scored on. This
  selection bias is acknowledged here rather than discovered later.)
- **P1 (primary)**: winner beats EVSIDS (median decisions, strictly
  fewer) on **≥ 7/13** of B13′.
- **P2**: winner beats Random on **≥ 12/13** of B13′.
- **P3**: rerun the winner with β=0, all else identical. P3 holds iff
  the β=0 ablation's P1-count drops by ≥ 1 instance. Note recorded in
  advance: for algebra C the ablation isolates Ψ-drift only (τ ≡ 1 for
  C is PROVED — Phase 2); for H it removes Ψ-drift and τ jointly.
- **P4**: winner's (algebra, λ) with per-family κ vs same config with
  global κ=−1, on the held-out set; a family is "won" iff the summed
  per-instance median decisions are strictly lower. Pass iff ≥ 2/3
  families won.
- **Suite context run** (no prediction attached): winner vs EVSIDS vs
  LRB vs Random on quick+medium × 5 seeds — correctness cross-check
  and per-family context for the report.

## Stop conditions (§7, restated)

- S3: P2 fails after one debugging pass → halt, report negative.
- S4: P1 fails but P2 holds → publishable negative result, written as
  such. **No hyperparameter iteration beyond the grid above.** The λ
  grid, κ table, β, dim, and all constants are frozen as of this
  commit; if VDIS loses at these settings, that is the result.

## Reporting

`docs/vdis/PHASE_3.md` (run log + tables) and
`docs/vdis/TRACK_B1_REPORT.md` per §9: P1–P4 table tagged EMPIRICAL,
ablation, per-family breakdown, seeds + commit hashes, and the "What
VSIDS's scalar fossil was actually missing" paragraph written only
from measured deltas.
