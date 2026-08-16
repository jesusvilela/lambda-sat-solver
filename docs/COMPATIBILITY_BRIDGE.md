# Compatibility Bridge

## Claim Discipline

  This document defines the bridge from typed diagnostic fields to
  valid global sections. It does not claim to solve classical
  Turing Halting.

  Core slogans:
  *Frustration becomes theorem-bearing only through a compatibility bridge.*
  *Irregularity becomes theorem-bearing only through a stability bridge.*
  *A typed diagnostic is not yet a proof obstruction.*
  *No global section is blocked without explicit premises.*
  *We are not collapsing to scalar hardness.*
  *We are not treating Euclidean distance as default.*
  *We are not treating human recognition as verification.*

## What This Document Contains

1. Why diagnostic fields are not enough
2. Gluing compatibility
3. Stability compatibility
4. Shift blocks gluing
5. Transport irregularity blocks stability
6. What remains frontier
7. Claim tiers

## 1. Why Diagnostic Fields Are Not Enough

The frustration and irregularity fields from `FrustrationIrregularity.lean`
are typed diagnostics. They record:

  - Frustration: where local sections conflict
  - Irregularity: where transport destabilizes sectionability

But they do not yet prove that these conflicts block valid global sections.
A typed diagnostic is not yet a proof obstruction.

To make frustration and irregularity theorem-bearing, we need
a compatibility bridge: a structure that links candidate global
sections to the sectionability tensors, and proves that
incompatibility implies invalidity.

## 2. Gluing Compatibility

### The problem

Two sectionability tensors S₁ and S₂ may disagree on the regime
at a state. A candidate global section G must assign a single
regime. If G agrees with both S₁ and S₂, then no disagreement
exists.

### The bridge

```lean
structure GlobalSectionCandidate (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B) where
  regime : A.State → Sec
  agrees_left : regime s = locally_decidable → S₁.status s = locally_decidable
  agrees_right : regime s = locally_decidable → S₂.status (T.transport s) = locally_decidable
```

### GluingCompatibility

```lean
def GluingCompatibility A B V T S₁ S₂ G : Prop :=
  ∀ s, G.regime s = locally_decidable →
    S₁.status s = locally_decidable ∧ S₂.status (T.transport s) = locally_decidable
```

## 3. Stability Compatibility

### The problem

Two transports T₁ and T₂ may produce different sectionability
statuses. If they are stability-compatible, they produce equal
statuses everywhere.

### The bridge

```lean
def StabilityCompatibility A V T₁ T₂ S₁ S₂ : Prop :=
  ∀ s, S₁.status s = S₂.status s
```

## 4. Shift Blocks Gluing

### Theorem

If G is gluing-compatible with S₁ and S₂, and G assigns
locally_decidable at x, then no sectionability shift exists
at x.

### Proof

```lean
theorem gluing_compatibility_blocks_shift
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (G : GlobalSectionCandidate A B V T S₁ S₂)
    (hGlue : GluingCompatibility A B V T S₁ S₂ G)
    (h_regime : G.regime x = Fustr.locally_decidable)
    (x : A.State) :
    ¬ SectionabilityShift A B V T S₁ S₂ x := by
  intro hShift
  have h_agree := hGlue x h_regime
  rcases h_agree with ⟨h_left, h_right⟩
  rw [h_left] at hShift
  exact hShift h_right
```

### Meaning

Gluing compatibility + regime assignment → no shift.
This is a small, clean, theorem-bearing result.

## 5. Transport Irregularity Blocks Stability

### Theorem

If S₁ and S₂ disagree at x, then no stability compatibility exists.

### Proof

```lean
theorem transport_irregularity_blocks_stability_compatibility
    (A : MΩ) (V : ExtVer A) (T₁ T₂ : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField A)
    (hStable : StabilityCompatibility A V T₁ T₂ S₁ S₂)
    (x : A.State)
    (hIrr : HasTransportIrregularity A V T₁ T₂ S₁ S₂ x) :
    False := by
  unfold StabilityCompatibility at hStable
  unfold HasTransportIrregularity at hIrr
  exact hIrr (hStable x)
```

### Meaning

Transport irregularity → instability → no stability compatibility.
This is also small, clean, and theorem-bearing.

## 6. What Remains Frontier

### The missing link

The theorem `frustration_irregularity_block_valid_global` was
the original frontier target. It required:

  - Gluing compatibility between G and S₁/S₂
  - Stability compatibility between T₁ and T₂ with S₁/S₂
  - Sectionability shift at x
  - Transport irregularity at x
  - Nonzero holonomy at x

With the compatibility bridge now in place, the proof
reduces to: shift + stability → contradiction.

The remaining gap is the explicit link between
`GlobalSectionCandidate` and `ValidGlobalHaltSection`:
how does regime assignment translate to a Bool-valued
decision predicate that flatness and external verification
can test against?

## 7. Claim Tiers

| Tier | Objects |
|------|---------|
| PROVED | `gluing_compatibility_blocks_shift`, `transport_irregularity_blocks_stability_compatibility` |
| CONJECTURAL | `frustration_irregularity_block_valid_global` (frontier) |
| LENS | `SectionabilityShift`, `HasTransportIrregularity` (definitions) |
| UNSAFE/PATCHED | scalar hardness, Euclidean distance, human=verification |

## The Final Slogan

Frustration becomes theorem-bearing only through a compatibility bridge.
Irregularity becomes theorem-bearing only through a stability bridge.
A typed diagnostic is not yet a proof obstruction.
No global section is blocked without explicit premises.

The wall is not a wall everywhere. It is a curvature field.
Some regions close, some locally shimmer, some require external
verification, and the omni-fluid whole refuses one final Boolean
flattening.
