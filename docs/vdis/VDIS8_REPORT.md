# VDIS v8 report — self-reference centrality prior: the strongest result in the track

**Verdict: V1 PASS emphatically, V2 PASS where signals apply, V0b/V3
confirmed. The Gödelian-self-reference lens, pursued honestly, produced
a static structural prior (eigenvector centrality) that beats BOTH
EVSIDS and LRB by more than 2× on fewest-decisions on fresh random
3-SAT — the first strongly-positive, correctness-verified,
baseline-beating result in eight generations. Foregrounded caveat: this
is decisions on a Python reference solver, at one scale, and
centrality/degree branching is a KNOWN idea — the honesty section is not
optional here.** EMPIRICAL: stage b8, 630 runs, 5 caps (all Random on
mutil_10). Prereg `VDIS8_PREREG.md` committed before the run;
correctness independently re-verified (below).

## Gate outcomes

| Gate | Criterion | Measured | Verdict |
|---|---|---|---|
| V0 | centrality decorrelated from activity | rank-corr +0.15/−0.07 (vs λ's 0.94) | PASS |
| V0b | centrality near-uniform on php (symmetry-respecting) | php CoV = **0.0000** | CONFIRMED |
| V1 (primary) | cent beats EVSIDS ≥ 60% of r3sat | cent-only 14/15, cent+λ 14/15 | **PASS** |
| V2 | cent+λ beats λ-only where both apply | yes on r3sat & mutil (below) | PASS (applicability-gated) |
| V3 | centrality dead on php | cent-only ≈ C-plain, both ≫ EVSIDS | CONFIRMED |
| Floor | ≥ EVSIDS Random-beat-count | met | PASS |

## The result, verified against real baselines

Fresh random-3-SAT, n=90, seeds 300–314 (15 instances), median decisions:

| Config | wins vs EVSIDS | wins vs LRB | Σ decisions |
|---|---|---|---|
| EVSIDS | — | — | 8 788 |
| LRB | — | — | 8 047 |
| C-plain | 6/15 | — | 8 158 |
| λ-only (v7) | 11/15 | 8/15 | 7 315 |
| **cent-only** | **14/15** | 13/15 | **3 821** |
| **cent+λ** | **14/15** | 14/15 | **3 480** |

cent+λ solves in **40% of EVSIDS's and 43% of LRB's** decisions.
**Correctness independently re-verified**: every SAT model checked
against its formula (all valid), UNSAT answers consistent — this is not
"fast because wrong." The effect isolates cleanly to centrality:
cent-only and λ-only share the identical combiner base and differ only
in the trader, so 7 315 → 3 821 is the centrality trader alone.

## V2 — two orthogonal signals DO combine (the recognition/resonance unlock)

The note flagged that recognition/resonance need ≥2 decorrelated
signals. Centrality supplies the second (orthogonal to activity by
construction). Where both signals have content, combining beats either
alone:

| family | cent-only | λ-only | **cent+λ** |
|---|---|---|---|
| random-3sat (Σ) | 3 821 | 7 315 | **3 480** |
| mutil_10 | 25 444 (loses) | 15 366 | **11 981** (wins) |
| mutil_8 | 1 224 | 1 524 | **1 209** |

On mutilated, cent-only *loses* (centrality alone insufficient) and
λ-only wins modestly, but **cent+λ wins both instances and beats each
component** — a genuine synergy, not a blend average. This is the first
positive evidence in the track that coupling decorrelated signals helps;
recognition/resonance are now worth reviving, *gated by applicability*
(on pigeonhole, where centrality is dead, adding it to λ hurts — 19 428
vs λ-only 11 481).

## V0b/V3 — the symmetry prediction held exactly

Pigeonhole centrality CoV = 0.0000: every variable identical by
automorphism symmetry, so centrality carries zero signal there, exactly
as pre-registered. cent-only on php (17 114) ≈ C-plain (16 232), both
far worse than EVSIDS (6 267). Centrality is a symmetry-*reader*, not a
symmetry-*breaker* — the prime order still owns pigeonhole (v6). The two
mechanisms are complementary by construction, not competing.
(Operational note: my pre-registered V3 check "cent-only == C-plain
per-seed" was flawed — the two use different base-scoring paths, so they
differ for reasons unrelated to centrality; the substantive prediction —
centrality gives no php benefit — holds via the aggregates.)

## Honesty section (mandatory given the magnitude)

1. **Decisions, not wall-clock.** This is decisions-to-solve in a Python
   reference CDCL, not time vs Kissat. Centrality is a one-time O(edges·
   iters) precompute; whether the decision savings survive as wall-clock
   wins — and whether the precompute amortizes — is untested. The claim
   is "centrality is a dramatically better *branching order* on these
   instances," not "faster solver."
2. **Not novel.** Static structural / degree / centrality-based variable
   ordering is a known idea in the SAT literature. The self-reference
   framing led here honestly, but the mechanism is classical. The
   contribution is empirical (magnitude, on fresh instances, vs two
   baselines, verified) and integrative (it's the orthogonal second
   signal the ensemble lacked), not a new algorithm.
3. **One scale, 15 seeds.** n=90 only; the v5 seed-lottery lesson binds.
   Needs sizes × ≥50 seeds before load-bearing.
4. **Family-specific.** cent-only is dead on php and loses mutilated;
   only cent+λ is broadly robust. A router remains the right architecture.
5. **The meta-point, stated plainly.** Eight generations of hyperbolic /
   hypercomplex geometry, and the thing that finally beat both standard
   heuristics by 2× is eigenvector centrality — a 1950s idea, computed on
   a plain co-occurrence graph, with none of the gyrovector machinery
   involved. The geometry was the journey; a classical structural prior
   was the destination.

## Disposition

This is the result that has unambiguously earned a real replication
study — now doubly so, and the design sharpens: pre-register {centrality,
λ, prime-router} vs EVSIDS/LRB/CaDiCaL across sizes n∈{50,90,150,250} ×
≥50 seeds, **wall-clock instrumented**, correctness-checked, with the
centrality precompute cost measured against its decision savings. Drop
the entire gyrovector stack from the replication — v1–v8 established it
was never the source of any win. That study is the honest next artifact;
everything before it in this track was the search that found the two
signals worth keeping (centrality, λ) and the one symmetry-breaker
(prime).
