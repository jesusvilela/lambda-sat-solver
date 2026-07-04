# MAX-GEO one-shot — report

**Verdict: the strong-negative prior HELD, cleanly. Maximal hyperbolic-
hypercomplex spinning geometry is EVSIDS-class at best on random 3-SAT
(far behind the degree winner and LRB), and does not crack pigeonhole.
The geometry line closes, indulgence honored with a clean, correctness-
verified negative — plus one honest, small wrinkle worth stating.**
EMPIRICAL: stage maxgeo, 300 runs, 0 capped, all MAX-GEO SAT models
independently verified valid. Config frozen per
`MAXGEO_ONESHOT_PREREG.md`, committed before the run.

## Prediction ledger — all three held

| Pred | Statement | Result | Held? |
|---|---|---|---|
| M1 | MAX-GEO does not beat degree on random-3sat aggregate | 5 374 vs degree 2 272 (2.4× worse) | ✓ |
| M2 | MAX-GEO does not beat EVSIDS ≥ 6/10 on random | 5/10 (EVSIDS-tied, 5 374 vs 5 706) | ✓ |
| M3 | no pigeonhole crack | php_8 12 267 vs EVSIDS 5 099 (2.4× worse) | ✓ |

## Random-3-SAT (10 fresh, seeds 500–509)

| Config | Σ decisions | beats EVSIDS | beats degree |
|---|---|---|---|
| degree | 2 272 | 9/10 | — |
| LRB | 3 852 | 6/10 | 1/10 |
| MAX-GEO | 5 374 | 5/10 | 1/10 |
| EVSIDS | 5 706 | — | 1/10 |

Maximal geometry lands essentially at EVSIDS level — marginally fewer
decisions in aggregate (5 374 vs 5 706), 5/10 win-count — and is
**2.4× worse than plain degree branching**, the mechanism that costs a
one-time occurrence count. Every per-decision flop of quaternion rotor
sandwiches, moving-frame transport, and torsion readout buys nothing
over EVSIDS here, and loses decisively to counting clause occurrences.

## Pigeonhole — the one honest wrinkle

| Instance | EVSIDS | degree | MAX-GEO |
|---|---|---|---|
| php_7_6 | 948 | 1 667 | 1 594 |
| php_8_7 | 5 099 | 15 175 | 12 267 |

MAX-GEO beats degree on all 4 pigeonhole instances, and is the
**best geometry config on php in the whole track** (php_8 12 267 vs v4
MF3's ~17 647). But this is not the geometry working — it is the
**prime-anchor component** (present in MAX-GEO) breaking pigeonhole's
symmetry, exactly as v6 established. Degree is *uniform* on pigeonhole
(same automorphism symmetry that flattened centrality), so it has no
signal there and does poorly; the prime precession does. So MAX-GEO's
only relative strength traces to the one non-hyperbolic, non-rotor
ingredient in it. And it still loses to EVSIDS by 2.4× on php_8 — no
crack.

## What this closes

Nine generations (v1–v8 + this), and the maximal, everything-on,
genuinely-curved, fully-spinning hypercomplex configuration:
- never beats the simplest classical mechanism (degree) on random,
- is only EVSIDS-class where degree isn't uniform,
- and its lone relative edge (pigeonhole vs degree) comes from the
  prime symmetry-breaker, not from any hyperbolic/rotor/torsion part.

The hyperbolic gyrovector geometry is, on all measured evidence,
decoration: it composes, it spins (|F_biv| 0.58–0.84), it is
numerically clean, and it moves the decision scalar to no measurable
benefit. The indulgence was worth running — it converts "we believe the
geometry doesn't help" into "we measured the maximal geometry and it
doesn't," with the config frozen and the prior pre-stated so the
negative is unimpeachable.

## Disposition

The geometry line is closed on evidence. The three signals worth
keeping are unchanged and all classical: **degree** (random),
**Lagrange dual-descent λ** (diversification), **prime order**
(symmetry-breaking on the families where degree/centrality go uniform).
The honest next artifact remains their replication study — `{degree, λ,
prime-router}` vs EVSIDS/LRB/CaDiCaL across sizes × ≥50 seeds,
wall-clock, gyrovector stack dropped.
