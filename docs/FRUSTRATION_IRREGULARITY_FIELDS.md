# Frustration and Irregularity Fields

## Claim Discipline

  This document characterizes frustration and irregularity fields
  as typed measures over the multi-perspectival sectionability tensor.

  Core slogans:
  *Frustration is not hardness.*
  *Irregularity is not distance.*
  *A field value is a typed regime, not a scalar score.*
  *Frustration marks failed compatibility across perspectives.*
  *Irregularity marks unstable transport.*
  *Detection must be empirical or formally verified before promotion.*

## What This Document Contains

1. Why frustration fields
2. Why irregularity fields
3. Difference from scalar hardness
4. Relation to sectionability tensor
5. CDCL ↔ GF(2) example
6. Observer ↔ verifier example
7. Time/angle/transport instability
8. What is formalized
9. What remains empirical

## 1. Why Frustration Fields

We do not start from "undecidable = absolute wall."
We open the halting problem as a field-range characterization.

The frustration field measures where local sectionability assignments
cannot be made mutually compatible. This is not hardness — it is
failed compatibility across perspectives.

### The incompatibility pattern

```
Local sections exist → but they cannot jointly satisfy overlap constraints → frustration
```

Examples:
  - CDCL says search explosion; GF(2) says linear structure
  - Observer says plausible; Verifier says unverified
  - Local chart says decidable; Transported chart says obstructed

## 2. Why Irregularity Fields

The irregularity field measures where transport produces unstable,
discontinuous, non-smooth, non-monotone, or non-gluable changes
in sectionability. This is not Euclidean distance — it is a typed
regime of sectionability shift under motion.

### The instability pattern

```
Tiny change in chart/time/transport/verifier → large sectionability shift → irregularity
```

Examples:
  - Transport across manifold boundary changes halting status
  - Time evolution creates new holonomy obstructions
  - Verifier regime change flips sectionability class

## 3. Difference from Scalar Hardness

The failed scalar hardness trap:

  hardness = some numeric score

The field approach:

  sectionability = typed regime (not numeric)
  frustration = compatibility failure (not hardness)
  irregularity = transport instability (not distance)

### What scalar hardness gets wrong

- Treats "hard to solve" as a single number
- Collapses the entire field into one Boolean wall
- Cannot distinguish between different kinds of failure
- Cannot detect where local structure exists but global gluing fails

### What the field approach captures

| Object | Captures |
|--------|----------|
| Sectionability tensor | What kind of halting section exists |
| Frustration field | Where local sections conflict |
| Irregularity field | Where transport destabilizes sectionability |

## 4. Relation to Sectionability Tensor

### Three-layer architecture

```
Layer A (sectionability):
  F_halting : MΩ → Sec
  where Sec = {total_decidable, semi_decidable, locally_decidable,
               externally_verifiable, holonomy_obstructed,
               observer_absorbed, unknown}

Layer B (frustration):
  F_frustration : (A, B, V, T, S₁, S₂) → Fustr
  where Fustr = {compatible, locally_frustrated, globally_frustrated,
                 verifier_frustrated, observer_absorbed, unknown}

Layer C (irregularity):
  F_irregularity : (A, V, T₁, T₂, S₁, S₂) → Ireg
  where Ireg = {stable, time_irregular, angle_irregular,
                 transport_irregular, verifier_irregular, unknown}
```

### Sectionability shift ≠ numeric subtraction

```
S₁.status x ≠ S₂.status x
```

This is a typed regime transition, not a numeric value.
Examples:
  - total_decidable → locally_decidable (global section lost)
  - externally_verifiable → holonomy_obstructed (verifier disagrees with holonomy)
  - locally_decidable → holonomy_obstructed (chart transport fails)

### Frustration ≠ hardness

```
Fustr.globally_frustrated(x) = true
```

This says: local sections exist but cannot be globally glued.
Not: "this program is hard to decide."

### Irregularity ≠ distance

```
Ireg.transport_irregular(x) = true
```

This says: sectionability shifts when transport varies.
Not: "the distance between manifolds is large."

## 5. CDCL ↔ GF(2) Example

### xor-chain instances

| Manifold | Sectionability | Frustration | Irregularity |
|----------|---------------|------------|-------------|
| CDCL | holonomy_obstructed (search explosion) | globally_frustrated | transport_irregular |
| GF(2) | locally_decidable (linear structure) | compatible | stable |
| Connection Laplacian | externally_verifiable (parity invariant) | verifier_frustrated | verifier_irregular |

### The frustration pattern

```
CDCL is frustrated because it cannot decide xor-chains efficiently.
GF(2) is flat because parity structure is locally decidable.
The connection Laplacian verifies the parity structure.
But CDCL's frustration is not hardness — it is incompatibility
with the GF(2) flat manifold.
```

### The irregularity pattern

```
Transport from CDCL manifold to GF(2) manifold shifts sectionability:
total_decidable → locally_decidable.
This is a sectionability shift, not a distance measurement.
```

## 6. Observer ↔ Verifier Example

### The absorption boundary

```
HumanRecognized(x) = true
ExternallyVerified(x) = false
ValidGlobalSection(x) = false
```

### The frustration pattern

```
Observer_absorbed = the human is treated as the verifier
Verifier_frustrated = the verifier disagrees with local consensus
```

### The irregularity pattern

```
Verifier_irregular = sectionability shifts when verifier changes
```

## 7. Time/Angle/Transport Instability

### Time irregularity

```
Sectionability at time t ≠ sectionability at time t+ε
```

This captures where computation time creates unstable sectionability.
Not: "this instance takes longer to solve."
But: "the sectionability class changes with computation time."

### Angle/chart irregularity

```
Sectionability under chart rotation ≠ sectionability under original chart
```

This captures where local chart choice affects sectionability.
Not: "the angle is different."
But: "sectionability is unstable under chart variation."

### Transport irregularity

```
Sectionability after parallel transport ≠ sectionability before
```

This captures where moving through the manifold changes sectionability.
Not: "the transport distance is large."
But: "sectionability is unstable under manifold transport."

## 8. What Is Formalized

### Definitions

| Object | Type | Description |
|--------|------|-------------|
| `FrustrationStatus` | inductive (6 values) | Compatibility failure regime |
| `FrustrationField` | structure | Field over (A,B,V,T,S₁,S₂) |
| `IrregularityStatus` | inductive (6 values) | Transport instability regime |
| `IrregularityField` | structure | Field over (A,V,T₁,T₂,S₁,S₂) |

### Proved lemmas

| # | Lemma | Premises | Conclusion |
|---|-------|----------|------------|
| A | `no_frustration_without_shift` | S₁.status = S₂.status everywhere | No globally_frustrated state |
| B | `shift_witnesses_possible_frustration` | S₁.status ≠ S₂.status somewhere | ∃ locally_frustrated state |
| C | `stable_under_equal_transports` | S₁.status = S₂.status everywhere | ∀ stable under transport |

### Conjectural

4. `frustration_irregularity_block_valid_global` — needs explicit
   compatibility link between S₁/S₂ and G. Left as frontier target.

### Unsafe / patched

  - No claim that frustration = hardness
  - No claim that irregularity = distance
  - No numeric scalar hardness by default
  - No human recognition as verification

## 9. What Remains Empirical

### The three empirical gaps

1. **Instantiation**: Concrete State/Chart/Trace types for specific
   computational families (Turing machines, SAT instances, etc.)

2. **Sectionability classifier**: Empirical algorithm to classify
   a submanifold's sectionability regime from instance features.
   Currently: classifier fix detects XOR/parity structure.
   Next: full sectionability classifier across all 8 regimes.

3. **Frustration/irregularity detectors**: Empirical measurement
   of frustration and irregularity fields on SAT instances.
   The SAT analogy table above is the target.

### The detection table (target)

| Instance | Source manifold | Target manifold | Transport | Sectionability shift | Frustration | Irregularity | Verifier status |
|----------|----------------|-----------------|-----------|---------------------|------------|-------------|----------------|
| xor-chain | CDCL | GF(2) | parity | high | low | high | parity invariant |
| random 3-SAT | CDCL | GF(2) | random | unknown | diffuse | low/noisy | unverified |
| hardware/crypto | CDCL | GF(2) | conjugation | high | high | transport-sensitive | verifier frustrated |

### Required next steps

1. Define concrete sectionability classifier with 8 regimes
2. Implement frustration field detector on transport between manifolds
3. Implement irregularity field detector on time/angle variation
4. Build the detection table above
5. Validate that frustration/irregularity predict solver regime changes

## The Final Slogan

Frustration is not hardness. It marks failed compatibility across perspectives.
Irregularity is not distance. It marks unstable sectionability under transport.
Detection must be empirical or formally verified before promotion.

The wall is not a wall everywhere. It is a curvature field. Some regions close,
some locally shimmer, some require external verification, and the omni-fluid whole
refuses one final Boolean flattening.
