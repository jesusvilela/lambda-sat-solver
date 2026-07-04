# VDIS v6 pre-registration — online nudge-combiner, ascendency-gated

**Operator: "proceed" on GARRABRANT_NUDGES.md. Committed before any v6
run. This is the synthesis config: the surviving nudges as online
experts, Hedge-reweighted on LBD reward within each solve, with
ascendency setting how much the ensemble is trusted per instance.
Logical induction is inspiration only — the mechanism is Hedge/EXP3.**

## Mechanism (pinned)

Per-variable combined score, algebra C, dim 32, κ per family table:

  score(v) = base(v) + gate · ( w_θ·θ̂(v) + w_p·p̂(v) )

- **base(v)** — axis-0 (fossil) activity across both polarities,
  min-max normalized to [0,1] over currently-unassigned vars. The
  channelized EVSIDS-equivalent core; always full weight (the market
  maker).
- **θ̂(v)** = pair-angle θ_v/π ∈ [0,1] — the v3 polarity-disagreement
  trader.
- **p̂(v)** = (p_v mod 360)/360 ∈ [0,1), p_v the v-th prime — a static
  per-variable identity trader (the de-precessed v4 prime signal;
  helped php ties in MF3).
- **gate** = clip(1 − α/0.3, 0, 1), α = relative ascendency A/C of the
  instance's variable co-occurrence graph (ASCENDENCY.md), computed
  once at construction. Diffuse (low-α) instances → gate≈0.4–0.9 (let
  nudges breathe); structured (high-α) → gate→0 (collapse to core).
- **Hedge update** (deferred-reward, on each conflict with LBD ℓ):
  for the variable d chosen at the most recent decision,
  w_t ·= exp(η·adv·(t̂(d)−½)), renormalize to the 2-simplex, η = 0.5.
  See correction 1 for `adv`.

### Correction 1 (dated before benchmark, caught at the Y0 probe)

The originally-pinned reward r = 1/max(ℓ,1) is **unconditionally
positive**, so whichever trader dominates endorses its own picks and
runs away regardless of decision quality — the Y0 probe measured
w collapsing to [0.008, 0.992] on r3sat, pure rich-get-richer, not
learning. Corrected before any benchmark run (same discipline as the
W1/R1/Q1 pre-benchmark dispositions): reward is the **normalized
advantage** adv = (ema_lbd − ℓ)/max(ema_lbd,1), ema_lbd a 0.95-EMA of
LBD. adv is positive only when the endorsed decision produced a
tighter-than-typical clause, negative when worse — so a dominating
trader that starts picking badly loses weight. η, α0, the gate map,
and all configs are otherwise unchanged.

## Configs (κ per family table, dim 32, seeds 0–4)

| Label | Description |
|---|---|
| EVSIDS / LRB / Random | baselines |
| C-plain | corrected incumbent (algebra C, no nudges) |
| **COMBO** | the combiner above (algebra C, α-gate on) |
| COMBO-nogate | gate fixed at 1.0 — ablates the ascendency gate |

Per-trader ablations (θ-only, p-only) run ONLY if COMBO shows life at
the X-gates, to bound compute — declared here so that staging is not a
post-hoc choice.

## Instance set B50 (fresh, never used in the track)

- random-3sat: n=90, ratio 4.267, seeds 200–249 (**50 instances** — the
  scale v5 flagged as the real requirement; the win family, at size).
- pigeonhole: n = 5,6,7,8 (deterministic; cannot be freshened or
  scaled — declared, carried as the structured-family wall).

## Gates and pre-registered predictions

- **Y0 (liveness)**: before benchmark — COMBO's weights move from
  [½,½] and gate ∈ (0,1) differs across families. Fail → halt.
- **Y1 (primary, win-count)**: COMBO beats EVSIDS on decisions on
  ≥ 60% of the 50 r3sat instances (median over seeds). 60% not 7/13:
  at n=50 the binomial noise band is tight enough that >50% is
  meaningful; 60% is a real edge, pre-committed.
- **Y2 (the aggregate, never once taken in the track)**: COMBO's total
  median decisions over the 50 r3sat instances < EVSIDS's. This is the
  hard one — the honest target the track has never hit.
- **Y3 (gate matters)**: COMBO beats COMBO-nogate on r3sat aggregate,
  AND COMBO ≥ C-plain on php (gate should protect structured instances
  the nogate variant harms).
- **Y4 (learning happens)**: mean final w_θ or w_p ≠ ½ ± 0.05 across
  r3sat, i.e. the Hedge update converges somewhere, not noise around
  uniform.
- **Floor**: ≥ EVSIDS's own Random-beat-count on B50 (v5's corrected
  floor definition — Random luck is measured relative to EVSIDS, not
  absolute).
- **No-rescue**: grid + η + α0 + gate map final. COMBO failing Y1/Y2
  at these settings is the result.
