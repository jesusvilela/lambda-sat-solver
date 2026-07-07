# Edge-tail stress — the tails of the omni distributions

*After the tock/fix cycle (2300+ fuzzed instances + a degenerate corpus: 0
crashes, 0 unsound), a stress sweep into the extremes. Harness
`docs/ladder/scripts/edge_tails.py`. Headline: **0 soundness violations across
all four tails**, and two honest boundaries made explicit.*

## 1. Phase-transition tail (random 3-SAT, α = 1 → 8)

| α | frames decided | middleware | vs Kissat |
|---|---|---|---|
| 1.0 … 4.26 … 8.0 | **0/6 at every α** | solved, ~2–11 ms | 0 disagreements |

The honest boundary, stated plainly: **the frames never fire on pure random
3-SAT, anywhere across the transition.** Random 3-SAT is structureless — no
parity, no cardinality, no 2-SAT collapse — at *every* ratio, including the 4.26
ridge. The middleware solves all of it, but via the certified Kissat fallback, at
CDCL speed. This is the frames' scope drawn exactly: they are for *structured*
instances; on the structureless omni-tail they add nothing but the certificate,
and they never lie (0 disagreements with Kissat across the whole sweep).

## 2. Symmetry tail (pigeonhole, up the isotropy tail)

| php | vars | middleware | Kissat |
|---|---|---|---|
| php8 | 56 | UNSAT · 1.3 ms | UNSAT · 25 ms |
| php10 | 90 | UNSAT · 2.1 ms | UNSAT · 365 ms |
| php11 | 110 | UNSAT · 2.5 ms | UNSAT · 2345 ms |
| **php12** | 132 | **UNSAT · 3.2 ms** | **TIMEOUT** |
| **php13** | 156 | **UNSAT · 4.1 ms** | **TIMEOUT** |

The high-isotropy tail is where the middleware crushes CDCL: the counting frame
refutes php13 (156 variables) in **4 ms** while Kissat times out from php12. Kissat
grows exponentially (25 ms → 365 → 2345 → timeout); the frame is flat, because it
computes on the symmetric orbifold's quotient (`ORBIFOLD_NOTE.md`) instead of
breaking the symmetry clause by clause.

## 3. Coverage tail (a pure XOR system diluted with noise)

| noise clauses | xor coverage | middleware | frame |
|---|---|---|---|
| 0 | 1.00 | SAT | parity |
| 2 | 0.98 | SAT | **coupled** |
| 5 … 40 | 0.95 → 0.71 | UNSAT | **coupled** |

Walking the parity frame off its decision boundary: at full coverage the pure
parity frame decides it (SAT); the moment noise dilutes the coverage below 1.0 the
pure frame can no longer cover the formula, and **the coupled router takes over** —
exchanging the XOR rows' entailments with the noise clauses to a verdict (and the
extra constraints flip it UNSAT). Every verdict agrees with Kissat. This is the
coupling earning its keep exactly at the frame boundary.

## 4. Coupling tail (parity + units, jointly UNSAT)

| arity | middleware | frame | rounds |
|---|---|---|---|
| 3 … 10 | UNSAT | coupled | 1 |

The coupling's home: `XOR(v₁…vₖ)=1` (SAT alone) plus units `vᵢ=0` (SAT alone),
jointly UNSAT — no single frame sees it, and the coupled router refutes it in one
propagation round at every arity, all sound (brute-checked).

## What the tails confirm

- **Soundness holds at every extreme** — 0 violations across the transition, the
  symmetry tail, the coverage boundary, and the coupling home.
- **The frames' scope is honest**: structured tails (symmetry, parity, coupling)
  are where they win, by large margins; the structureless tail (random 3-SAT at
  every α) is handled only by the certified fallback, and the middleware says so
  rather than pretending a frame applies.
- **The coupled/breathing router is the tail-worker**: it is what carries the
  coverage boundary and the mixed-UNSAT home that no single frame reaches.
