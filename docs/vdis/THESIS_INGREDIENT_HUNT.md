# Hunt for the "magic ingredient" in the uploaded theses — findings

Operator believed MAX-GEO "missed the magic ingredient" and pointed to
the hypercomplex-math-thesis, manifold, skills, IGBundle, and TELOS
material. I read the actual code (not the vocabulary) hunting for one
concrete, testable branching mechanism. Honest inventory:

| Source | What it actually is | SAT-branching contract? |
|---|---|---|
| `hyperdim_protocol.py` | 13-D **agent self-scoring** rubric (grounded_identity, mutual_recognition, godelian_boundary…); its docstring: "numeric engineering signals, not consciousness claims" | none — scores an agent, not variables |
| `operators.py` | "typed scaffold… not a claim the full thesis is implemented" (lift=×2, ground=×0.5); `convex_resonate` = midpoint blending | `convex_resonate` = the blend v7 measured as *diluting* |
| `manifold/*` | a **finance** PPO portfolio optimizer | none (wrong domain) |
| `skills/evolved-dialect-*` | §-LANG Tower dialects | vocabulary |
| `hypercomplex_breathing.py` | 2-D toy: swirl + grounding pull + **time-varying curvature** κ(t)=κ_base+amp·sin(rate·t) | **the one genuinely-untried knob** |

## The one real candidate, tested: breathing curvature

MAX-GEO and every prior geometry generation held curvature FIXED. The
breathing model's contribution is an oscillating κ during the solve. I
implemented it faithfully (`breath_amp`, `breath_rate`; c oscillates
with conflict count, clamped ≥ 0) and tested MAX-GEO+breath vs MAX-GEO
vs degree vs EVSIDS on 15 fresh r3sat (seeds 600–614), correctness
verified (all SAT models valid).

**Result — breathing is noise, not magic:**
- vs fixed-c MAX-GEO: **7/15 better, 6/15 worse** (a coin flip); totals
  6 741 vs 7 079 (within variance).
- vs degree: 3/15 — degree uses **half** the decisions (3 273 vs 6 741).
- vs EVSIDS: 9/15 (EVSIDS-class, like fixed MAX-GEO).

Oscillating the curvature perturbs an already-inert signal; it adds
variance without systematic improvement, and does not approach degree
branching. `breath_amp` is retained in the code as a tested, documented
negative (default 0 = off), so "did we try time-varying curvature?" is
answered with data, not assumption.

## Adiabatic-infinitesimal follow-up (operator request)

Tested breathing in the adiabatic (breath_rate→0) / infinitesimal
(amp→0) limit, 10 fresh r3sat, total decisions:

| config | total |
|---|---|
| degree | 1 737 |
| MAXGEO fixed-c | 4 389 |
| breath rate=0.001 amp=0.5 (most adiabatic) | 12 708 |
| breath rate=0.001 amp=0.1 | 8 427 |
| breath rate=0.2 amp=0.1 (least adiabatic) | 3 473 |

The **adiabatic limit is the WORST** regime: slow breathing lets c drift
to a consistently-wrong value and sit there all solve instead of
averaging out; faster breathing recovers toward fixed-c but never near
degree. "Adiabatic infinitesimal" is precisely the direction that hurts.

## The globular-balls / holographic-screen construction — decode

"Globular Poincaré balls connected by fiber-bundled Möbius channels,
frontier as holographic screen / cellular gate" decodes to a **community
decomposition with cut-variable (separator) branching**: clusters = the
balls, inter-cluster boundary variables = the screens/gates, branch on
them first. This is a REAL SAT technique (community structure / cutset /
tree-decomposition branching).

**Why it can't be tested on the current benchmark:** random 3-SAT is the
textbook instance with *no* community structure (a flat random expander);
pigeonhole is symmetric. Our whole suite is the class engineered to have
no exploitable global structure — which is likely WHY every
manifold/geometry idea had nothing to grip, and why a local count
(degree) is the ceiling here. To test the holographic-screen idea fairly
requires **planted-community instances** (genuine clusters + sparse cut
variables). That is a legitimate, contract-bearing follow-up — pending
operator go-ahead — and is the benchmark where this construction could
actually pay off.

## Holographic-screen / cellular-gate — BUILT AND TESTED on its home turf

The globular-balls construction decoded to community + cut-variable
branching. Rather than only note the benchmark mismatch, I built the
matching testbed: `planted_community_ksat` (communities = balls, cut
clauses = screens/gates) and a `gate` trader scoring each variable by how
many communities its clauses span (boundary/screen variables high),
using **oracle** planted labels AND **detected** (label-propagation)
communities. `holographic_screen_test.py`.

- **Detection works**: label-prop recovers the planted communities
  exactly (5 planted → 5 found); oracle and detected gate scores are
  identical, so detection is NOT the bottleneck.
- **The mechanism does not help**, in any structural regime tested
  (12 seeds each):

| instances | EVSIDS | degree | gate | gate beats EV | gate beats degree |
|---|---|---|---|---|---|
| 5×30 ir3.9 cut80 (diffuse) | 3 823 | 2 171 | 3 292 | 8/12 | 0/12 |
| 5×30 ir4.0 cut25 (sharp) | 2 161 | 1 362 | 2 447 | 5/12 | 2/12 |
| 6×25 ir3.6 cut30 (SAT-heavy) | 1 334 | 1 558 | 2 164 | 3/12 | 5/12 |
| 4×35 ir4.1 cut20 | 1 263 | 1 272 | 1 595 | 4/12 | 5/12 |

Boundary-variable branching is worse than EVSIDS on balance (3–8/12) and
never beats degree on aggregate — given even oracle community labels, on
the exact community-structured instances the construction is for.
CDCL's clause learning already absorbs cross-community coupling; putting
separator variables first does not decompose the search the way the
tree-decomposition intuition suggests. The construction, tested on its
home turf with every advantage, is another negative.

## Verdict

The magic ingredient is not in the material. Every element is one of:
already-implemented (swirl = rotor channel; resonance = blending),
no-SAT-contract (the mind-quality protocol, the Tower scaffold, the
dialects), wrong-domain (finance), or tested-and-inert (breathing
curvature). The genuine gift in this body of work — the bunny kernel's
mirror-descent / EXP3 update — was already the winning infrastructure
(the v6–v8 combiner). Nine generations plus this hunt converge on the
same place: the wins are classical (degree, λ, prime, mirror-descent
weighting); the hyperbolic/hypercomplex geometry, at every curvature
schedule tried including breathing, is decoration.
