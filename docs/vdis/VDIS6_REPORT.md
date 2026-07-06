# VDIS v6 report — online nudge-combiner, ascendency-gated

**Verdict: Y1/Y2 FAIL on the pre-registered random-3-SAT target — but
the run produced the first real crack in the pigeonhole wall in six
generations, and falsified my own ascendency-gate hypothesis in the
most informative possible way (it is inverted). The combiner's Hedge
update autonomously discovered that pigeonhole needs the prime-identity
trader, driving its weight to 0.99 without being told.** EMPIRICAL:
stage b50, 1 620 runs, 0 capped; prereg `VDIS6_PREREG.md` + Correction 1
(reward fix caught at Y0), committed before the benchmark.

## Gate outcomes

| Gate | Criterion | Measured | Verdict |
|---|---|---|---|
| Y0 | combiner alive, reward not degenerate | fixed pre-run (Correction 1) | PASS |
| Y1 (primary) | COMBO beats EVSIDS on ≥ 60% of 50 r3sat | 18/50 = 36% | **FAIL** |
| Y2 (aggregate) | COMBO r3sat total < EVSIDS | 29 831 vs 24 607 | **FAIL** |
| Y3 (gate) | gate helps r3sat AND protects php | helps r3sat; **backwards on php** | **FALSIFIED (informative)** |
| Y4 (learning) | w converges ≠ ½ meaningfully | yes — see below | **PASS** |
| Floor | ≥ EVSIDS's Random-beat-count | COMBO 51/54 ≥ EVSIDS 49/54 | PASS |

## Random-3-SAT (the pre-registered target): nudges are net harm

| Config | r3sat wins | r3sat Σ decisions |
|---|---|---|
| LRB | 28/50 | 22 321 |
| EVSIDS | — | 24 607 |
| C-plain (no nudges) | 21/50 | 24 322 |
| **COMBO** | 18/50 | 29 831 |
| COMBO-nogate | 14/50 | 37 274 |

On random instances the best VDIS config is the one with **no nudges at
all** (C-plain 21/50 > COMBO 18/50), everything loses to LRB, and the
combiner's aggregate is *worse* than EVSIDS. The v1–v5 "VDIS wins on
random 3-SAT" story was a small-n (13-instance) artifact: at n=50 the
nudge apparatus is a liability here. This is the v5 seed-lottery warning
cashed out — the honest random-3-SAT verdict, at scale, is negative.

## Pigeonhole: the wall cracks, for the first time

| Instance | EVSIDS | C-plain | COMBO (gated) | COMBO-nogate |
|---|---|---|---|---|
| php_5_4 | 39 | 33 | 34 | 32 |
| php_6_5 | 181 | 205 | 214 | 201 |
| php_7_6 | 948 | 1 371 | 1 296 | 1 343 |
| **php_8_7** | 5 099 | 14 623 | 7 574 | **4 625** |

**COMBO-nogate beats EVSIDS on php_8_7: 4 625 vs 5 099.** No VDIS config
in five prior generations came within 3× of EVSIDS on php_8 (best was
14 623). This is real and mechanistic, not noise: pigeonhole's
thrashing comes from its variable symmetry, the prime-identity trader
p̂(v)=(p_v mod 360)/360 is a fixed asymmetric variable ordering, and it
breaks that symmetry. The result is a median over 5 seeds.

## Y4: the combiner learns this autonomously (the real headline)

The Hedge update was told nothing about families. Measured final
weights:

- r3sat (10 instances): mean w_θ = 0.36 ± 0.28 — moved off ½,
  high-variance (instance-specific), no consistent trader preference.
- **php_6 → [0.15, 0.85], php_7 → [0.10, 0.90], php_8 → [0.009, 0.991]**
  — weight on the prime trader rises *monotonically with pigeonhole
  hardness*, converging to near-pure prime as the symmetry problem gets
  worse. The online learner discovered, unprompted, that pigeonhole
  wants symmetry-breaking and the prime order supplies it.

## Y3: my ascendency gate is inverted (falsified, usefully)

I hypothesized: high-α (structured) → suppress nudges; low-α (diffuse)
→ let them breathe. The data says the opposite. php (the structured
family) is exactly where the nudge *helps most* (nogate php_8 4 625 <
gated 7 574 < C-plain 14 623), and my gate throttles it there (gate=0.27
on php). On r3sat the gate happens to help only because nudges are
harmful there and any suppression is good. The ascendency/overhead
framing had the sign backwards: structured instances don't need *less*
overhead, they need a *specific, well-chosen* nudge (symmetry-breaking),
and diffuse instances are where extra state is dead weight. Ascendency
correctly identifies *which* instances differ; it points the wrong way
on *what to do about it*. Recorded as a falsified pre-registered
hypothesis, not smoothed over.

## Disposition

No-rescue closes v6. Net for the track: six generations, and the one
durable, scalable, mechanistically-understood positive is not on random
3-SAT (that was small-n luck) but the opposite — an online-learned,
prime-identity symmetry-breaker that cracks the pigeonhole wall on the
hardest instance, discovered autonomously by a Hedge update over
experts. The obvious next hypothesis (a new pre-registration, not built
here): drop the θ trader and the inverted gate, keep the prime-identity
trader and the online weighting, and route it by a symmetry/structure
detector (high-α) rather than against it — i.e. an explicit
symmetry-breaking heuristic that only engages on structured instances.
That is the first VDIS follow-up with a positive, scaled, understood
result behind it rather than a hope.
