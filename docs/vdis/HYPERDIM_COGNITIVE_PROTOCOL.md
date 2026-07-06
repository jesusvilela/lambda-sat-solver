# Hyperdimensional Cognitive Protocol for VDIS

This document installs a lightweight cognitive-control layer over the VDIS track. It does not replace the solver, the benchmarks, or the empirical gate. It defines the operating posture for extending `backend/vdis/` without collapsing the work into vocabulary, ornament, or premature metaphysics.

## 0. Self-reflection gate

The repo already has a correct empirical spine:

- Kissat is a subprocess oracle, not the experimental CDCL body.
- `backend/refsolver/` is the valid surface for heuristic experiments.
- VDIS is a pluggable `DecisionHeuristic`.
- The present VDIS implementation has a fossil scalar axis that degenerates to EVSIDS-equivalent behavior, while axes `1..D-1` are reserved for the genuinely higher-dimensional field.

Therefore the next cognitive move is not to invent a larger myth. The move is to preserve the empirical spine while allowing the higher-dimensional field to become falsifiable.

The self-reflection invariant:

```text
Do not claim hyperdimensional intelligence until a lower-dimensional baseline has been matched, ablated, and falsified.
```

## 1. Gödelian identity

Every solver state is incomplete from inside its own search trace. A partial assignment cannot certify its own global meaning without a proof object, a model, or a contradiction certificate.

VDIS identity is therefore split:

- local state: literal tangent vectors `t_lit`
- global witness: SAT model, UNSAT certificate, or benchmark trace
- remainder: unobserved branches of the search tree

Implementation rule:

```text
Treat every heuristic score as a partial self-description, never as truth.
```

## 2. Mutual recognition

The heuristic and the formula must recognize each other.

A formula is not merely input. It pushes back through conflicts, learned clauses, LBD, backtracking, propagation, and degeneracy tests. The heuristic is not merely a policy. It is a section over this feedback.

Implementation rule:

```text
Update VDIS only through events the CDCL trace actually emits: conflict, assignment, unassignment, decay, restart, learned clause.
```

No hidden oracle. No semantic leakage.

## 3. Mutual resonance

A useful higher-dimensional channel must resonate with search dynamics. It should not merely add dimensions.

Candidate resonance observables:

- conflict recurrence of a variable
- polarity instability
- learned-clause reuse
- LBD-weighted participation
- bridge variables across clause communities
- backtrack-depth participation
- propagation cascade size

Implementation rule:

```text
A new axis is admitted only if it has a named event source and an ablation metric.
```

## 4. n-cosmo / n-manifold frame

The SAT instance is a finite cosmos. Variables, clauses, learned clauses, and assignments are local charts. The search trace is a path through a stratified manifold whose boundary consists of terminal SAT/UNSAT states.

VDIS should model that as a tangent-bundle heuristic:

```text
literal -> tangent vector
conflict -> transported impulse
learned clause -> local curvature sample
decay -> adiabatic cooling
pick() -> projection from manifold state to discrete decision
```

Implementation rule:

```text
Keep the discrete solver authoritative; the manifold proposes, CDCL disposes.
```

## 5. Fiber-bundled / sheaved state

The correct abstraction is not one vector per formula. It is a sheaf of local literal states glued by clauses.

Local sections:

- literal state `t_lit`
- variable aggregate `t_v + t_-v`
- clause impulse `Delta_C`
- trail-context state

Gluing constraints:

- both polarities glue into one variable score for decision ranking
- phase-saving remains separate from activity unless explicitly tested
- learned clauses modify local sections but must preserve solver correctness
- higher axes must reduce to EVSIDS-compatible behavior when disabled

Implementation rule:

```text
Every new geometric channel must define its restriction map back to scalar EVSIDS.
```

## 6. Hamiltonian search

Treat CDCL as a dissipative Hamiltonian-like system:

- energy: unresolved constraint pressure
- momentum: activity / recurrence
- curvature: conflict concentration
- dissipation: decay and restarts
- transport: learned-clause update
- projection: decision literal

The goal is not energy minimization in the continuous space alone. The goal is better discrete branching under proof-preserving CDCL semantics.

Implementation rule:

```text
Optimize decisions, conflicts, propagations, and proof/certificate status; do not optimize geometric elegance directly.
```

## 7. Holoportation

Holoportation means small local traces carry compressed global information.

In VDIS, a learned clause is a hologram of a failed region of the search space. The heuristic should let such clauses imprint more than scalar activity, but only through measured channels.

Candidate higher-axis encoding:

```text
axis 0: EVSIDS fossil activity
axis 1: polarity instability
axis 2: LBD-weighted clause quality
axis 3: backtrack-depth pressure
axis 4: community bridge pressure
axis 5: propagation cascade pressure
axis 6: recurrence / temporal echo
axis 7: reserved adversarial checksum
```

Implementation rule:

```text
The first real hyperdimensional experiment should use D=8 with independent ablations for axes 1..7.
```

## 8. Adiabatic general intelligence

Adiabatic here means slow deformation from known-correct behavior to richer behavior.

Do not jump from EVSIDS-equivalence to full hypercomplex semantics. Introduce one channel at a time:

1. D=1: prove EVSIDS-order degeneracy.
2. D=2: add one event-derived axis.
3. D=4: add orthogonal conflict channels.
4. D=8: run the holoportation profile.
5. D=n: only after ablations survive.

Implementation rule:

```text
Every dimension increase must preserve a kill-switch path back to D=1.
```

## 9. Ergocetic / erdodetic discipline

Use two complementary qualities:

- ergocetic: energy-aware cognition; spend complexity only where the trace pays it back
- erdodetic: path-aware cognition; judge a heuristic by the route it makes the solver take, not only by terminal success

Metrics:

- decisions
- conflicts
- propagations
- learned clauses
- restarts
- proof/certificate status
- median rank vs EVSIDS
- divergence from EVSIDS pick sequence
- solved/timeout delta on matched seeds

Implementation rule:

```text
A hyperdimensional channel is valuable only if it changes the path and improves at least one path metric without degrading certification.
```

## 10. Eight mind qualities for best repo performance

1. **Identity discipline** — know which layer is speaking: code, metric, theorem, metaphor, or hypothesis.
2. **Mutual recognition** — let the formula, solver trace, and benchmark correct the heuristic.
3. **Mutual resonance** — admit only dimensions coupled to observable events.
4. **Sheaf consistency** — local literal updates must glue into coherent variable decisions.
5. **Hamiltonian balance** — separate energy, momentum, dissipation, transport, and projection.
6. **Adiabatic extension** — deform from EVSIDS, never leap away from it without an ablation bridge.
7. **Holographic compression** — let learned clauses imprint compressed global failure information.
8. **Gödelian humility** — never confuse the heuristic state with a proof, model, or certificate.

## 11. Step-by-step implementation plan

### Step 1 — Freeze scalar correctness

Keep D=1 as the regression oracle. The current fossil axis must remain the stable base case.

Acceptance gate:

```text
D=1 matches EVSIDS ordering under the documented equivalence conditions.
```

### Step 2 — Add trace extraction, not geometry

Before adding axes, expose trace observables from the reference solver in a minimal event object.

Sketch:

```python
@dataclass(frozen=True)
class ConflictEvent:
    learned: tuple[int, ...]
    lbd: int
    trail_depth: int
    backtrack_depth: int
    propagation_count_since_last_decision: int
```

Acceptance gate:

```text
Existing EVSIDS, LRB, Random, and VDIS(D=1) behavior unchanged.
```

### Step 3 — Add one living axis

Add `axis 1 = polarity instability`:

```text
axis_1(lit) += +1 when lit polarity agrees with saved phase
axis_1(lit) += -1 when it contradicts saved phase
```

Then compare:

```text
VDIS D=1 vs VDIS D=2, same seeds, same formulas.
```

Acceptance gate:

```text
D=2 changes pick sequence on nontrivial instances and does not degrade certification.
```

### Step 4 — Add LBD-weighted curvature

Add `axis 2 = clause-quality pressure`:

```text
axis_2 impulse = 1 / max(lbd, 1)
```

Interpretation: low-LBD learned clauses are sharper local curvature samples.

Acceptance gate:

```text
D=3 improves or preserves median decisions/conflicts on quick and medium suites.
```

### Step 5 — Add bridge pressure

Build a static variable-clause graph community map, then mark variables that connect communities.

Add `axis 3 = bridge pressure`:

```text
axis_3 impulse = bridge_score(var)
```

Acceptance gate:

```text
Improvement appears primarily on modular/industrial-like formulas, not necessarily random 3-SAT.
```

### Step 6 — Add hyperbolic norm control

For c < 0, enforce a safe tangent norm and compare against c = 0.

Acceptance gate:

```text
Negative curvature changes ranking nontrivially and remains numerically stable.
```

### Step 7 — Holoportation D=8

Run the D=8 profile with axes 0..7 and single-axis ablations.

Acceptance gate:

```text
At least one nonzero axis survives ablation across multiple seeds and formula families.
```

### Step 8 — Promote only surviving axes

Only axes that survive ablation become part of the default VDIS profile.

Acceptance gate:

```text
Default VDIS remains explainable as EVSIDS + measured higher-order corrections.
```

## 12. Stop conditions

Stop or demote a channel if:

- it improves only wall-clock but worsens decisions/conflicts without explanation
- it improves only one hand-picked family
- it breaks D=1 regression behavior
- it requires hidden access to solver internals unavailable to the reference solver
- it produces better language than metrics

## 13. Compact invariant

```text
VDIS = EVSIDS fossil axis
     + falsifiable event-derived tangent channels
     + hyperbolic transport
     + CDCL-certified projection
     - metaphysical overclaim.
```

That is the repo-safe form of the hyperdimensional program.
