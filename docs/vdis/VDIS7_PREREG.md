# VDIS v7 pre-registration — Lagrangian symmetry-breaking, generalization test

**Operator: "proceed, and consider Lagrange." Committed before any v7
run. v6's one durable positive was a prime-identity order cracking
pigeonhole via symmetry-breaking, online-discovered. The honest open
question: was that a real principle or a one-family fluke of an arbitrary
order? v7 answers it with a *principled* Lagrangian symmetry-breaker,
tested on a SECOND symmetric family it was not tuned for.**

## The Lagrange mechanism (pinned)

Per-variable dual multiplier λ_v ≥ 0 — the shadow price of variable v's
non-commitment, in a Lagrangian relaxation whose relaxed constraint is
"do not keep re-litigating v in conflicts":

- **Dual ascent** (constraint violated — v still in conflicts): on each
  conflict, for v in the learned clause, λ_v ← λ_v + 1.
- **Relaxation decay**: all λ ← 0.95·λ each conflict (bounded, EMA-like).
- **Primal coupling / dual descent** (constraint addressed by
  committing): when v is *chosen as a decision*, λ_v ← 0.5·λ_v. **This
  is the load-bearing distinction from EVSIDS** — deciding a variable
  pays down its multiplier, so the search addresses the most-violated
  constraint then moves on, and λ *cycles* like a dual variable instead
  of monotonically accumulating. EVSIDS never reduces a score for being
  decided.
- trader score = min-max-normalized λ over unassigned vars, fed into the
  v6 combiner as an additional expert (base + gate·Σ_t w_t·trader_t,
  Hedge-reweighted on advantage-baselined LBD reward, per v6).

## Configs (algebra C, dim 32, κ per family, seeds 0–4)

| Label | Traders |
|---|---|
| EVSIDS | baseline |
| C-plain | none (incumbent) |
| COMBO | θ + prime (the v6 config) |
| COMBO+λ | θ + prime + Lagrange |
| λ-only | Lagrange only |

Gate fixed at 1.0 for all combiner configs (v6 falsified the ascendency
gate as inverted; not carried forward).

## Instance set (calibrated; trivial families excluded, declared)

Structured / symmetric (where symmetry-breaking should matter):
- pigeonhole: n = 5,6,7,8 (the v6 family — in-sample for prime).
- **mutilated-chessboard: n = 8, 10** (the OUT-OF-SAMPLE symmetric
  family — board symmetry, no reason an arbitrary prime order aligns;
  mutil_8 = 1217 dec, mutil_10 = 24 412 dec under EVSIDS, both real
  symmetry-thrash instances). Graph-coloring excluded: calibration
  showed it trivial (≤ 14 decisions even dense) — no thrash to break.

Negative control:
- random-3sat: n = 90, seeds 300–314 (15 fresh) — no symmetry, so
  symmetry-breaking must NOT help here or it isn't symmetry-breaking.

## Gates and pre-registered predictions

- **Z0 (liveness)**: λ moves and *cycles* (ascent then descent, not
  monotone), and its variable ranking is not identical to EVSIDS's on a
  probe. Fail → halt.
- **Z1 (generalization — THE question)**: a symmetry-breaking combiner
  (COMBO+λ or λ-only) beats EVSIDS on decisions on **mutilated-
  chessboard** (both mutil_8 and mutil_10, median over seeds). This is
  the out-of-sample family; passing means symmetry-breaking is a real
  transferable principle, not a pigeonhole-specific fluke.
- **Z2 (Lagrange vs static prime)**: λ-only ≥ COMBO (θ+prime) on the
  structured-set aggregate — does the principled learned multiplier
  match/beat the arbitrary static order, especially on mutilated where
  the prime order has no reason to align?
- **Z3 (negative control)**: on r3sat, C-plain ≤ every combiner
  (nudges do not help where there is no symmetry). If λ *helps* r3sat,
  it is a generic activity booster, not a symmetry-breaker — that would
  undercut the whole Z1 interpretation, so it is pre-registered as a
  falsifier.
- **Floor**: ≥ EVSIDS's own Random-beat-count on the union set.
- **No-rescue**: mechanism constants (step 1, decay 0.95, descent 0.5,
  η 0.5) and the grid are final.
