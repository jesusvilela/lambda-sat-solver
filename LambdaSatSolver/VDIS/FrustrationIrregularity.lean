import Mathlib
import LambdaSatSolver.VDIS.OmnifluidManifold
import LambdaSatSolver.VDIS.OAR

/-!
# Frustration and Irregularity Fields

## Claim Discipline

  This file defines typed diagnostic fields for computational sectionability.
  It does NOT claim to solve classical Turing Halting.

  Core slogans:
  *Frustration is not hardness. It is failed compatibility across perspectives.*
  *Irregularity is not distance. It is unstable sectionability under transport.*
  *A field value is a typed regime, not a scalar score.*
  *Frustration marks failed compatibility.*
  *Irregularity marks unstable transport.*
  *Detection must be empirical or formally verified before promotion.*

## Architecture

Three layers:

  Layer A (status types):
    `FrustrationStatus`, `IrregularityStatus` — typed regimes.

  Layer B (field structures):
    `FrustrationField`, `IrregularityField` — typed diagnostics over state spaces.

  Layer C (theorems):
    `no_frustration_without_shift`, `shift_witnesses_possible_frustration`,
    `stable_under_equal_transports` — small, clean, proved.

## Import chain

  OmnifluidManifold.lean → HaltSectionability, MΩ, HaltField, ExtVer, HolonomySystem
  OAR.lean → σ-external invariant, role separation
-/

open Real

/-!
## §A — Frustration Status

Frustration marks failed compatibility across sectionability perspectives.
Not a numeric score. A typed regime.
-/

/-- Frustration status: the compatibility state of local sections.

  * `compatible` — no conflict detected
  * `locally_frustrated` — sections conflict at this state
  * `globally_frustrated` — sections conflict across the whole space
  * `verifier_frustrated` — verifier cannot resolve the conflict
  * `observer_absorbed` — human recognition mistaken for verification
  * `unknown` — status unknown
-/
inductive FrustrationStatus
  | compatible
  | locally_frustrated
  | globally_frustrated
  | verifier_frustrated
  | observer_absorbed
  | unknown
  deriving DecidableEq, Repr

/-!
## §B — Irregularity Status

Irregularity marks unstable sectionability under transport.
Not Euclidean distance. A typed regime.
-/

/-- Irregularity status: stability under transport variation.

  * `stable` — no irregularity
  * `time_irregular` — unstable under time variation
  * `angle_irregular` — unstable under angle variation
  * `transport_irregular` — unstable under transport
  * `verifier_irregular` — unstable under verifier regime change
  * `unknown` — status unknown
-/
inductive IrregularityStatus
  | stable
  | time_irregular
  | angle_irregular
  | transport_irregular
  | verifier_irregular
  | unknown
  deriving DecidableEq, Repr

/-!
## §C — Sectionability Shift and Transport Irregularity

Definitions for typed regime transitions.
Not numeric subtraction. Typed regime changes.
-/

/-- A sectionability shift at state x between S₁ and S₂.

Two sectionability tensors disagree under transport.
This is a typed regime transition, not a numeric value. -/
def SectionabilityShift
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (x : A.State) : Prop :=
  S₁.status x ≠ S₂.status (T.transport x)

/-- Transport irregularity: S₁ and S₂ disagree at the same state.

Two sectionability tensors on the same manifold disagree without transport. -/
def HasTransportIrregularity
    (A : MΩ) (V : ExtVer A) (T₁ T₂ : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField A)
    (x : A.State) : Prop :=
  S₁.status x ≠ S₂.status x

/-!
## §D — Frustration Field

A frustration field assigns a frustration status to each state.
It is defined as the set of states where sectionability tensors disagree.
-/

/-- A frustration field over a state space.

Collects all states where two sectionability tensors disagree under transport.
The frustration field is defined by the incompatibility of local sections:
  frustration x ≠ compatible ↔ S₁.status x ≠ S₂.status (T.transport x)

This makes frustration a derived diagnostic, not an independent field.
-/
structure FrustrationField
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ S₂ : HaltField A) where
  /-- Frustration status assignment. -/
  frustration : A.State → FrustrationStatus
  /-- The defining property: frustration is nonzero exactly where sectionability tensors disagree. -/
  frustration_iff : ∀ x, (frustration x ≠ FrustrationStatus.compatible) ↔ S₁.status x ≠ S₂.status (T.transport x)

/-!
## §E — Irregularity Field

An irregularity field assigns an irregularity status to each state.
It is defined as the set of states where sectionability tensors disagree
under different transports.
-/

/-- An irregularity field over a state space.

Collects all states where two sectionability tensors disagree under
different transports. The irregularity field is defined by:
  irregularity x ≠ stable ↔ S₁.status x ≠ S₂.status x
-/
structure IrregularityField
    (A B : MΩ) (V : ExtVer A)
    (T₁ T₂ : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B) where
  /-- Irregularity status assignment. -/
  irregularity : A.State → IrregularityStatus
  /-- The defining property: irregularity is nonzero exactly where sectionability tensors disagree. -/
  irregularity_iff : ∀ x, (irregularity x ≠ IrregularityStatus.stable) ↔ S₁.status x ≠ S₂.status x

/-!
## §F — Proved Theorems

### Theorem A: No Frustration Without Shift

If no sectionability shift exists at x, then the frustration field
must be compatible at x.

Proof: If frustration x ≠ compatible, then by frustration_iff,
S₁.status x ≠ S₂.status (T.transport x), which is exactly a shift.
Contradiction.
-/

theorem no_frustration_without_shift
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ S₂ : HaltField A)
    (F : FrustrationField A B V T S₁ S₂)
    (x : A.State)
    (h_no_shift : ¬ SectionabilityShift A B V T S₁ S₂ x) :
    F.frustration x = FrustrationStatus.compatible := by
  unfold SectionabilityShift at h_no_shift
  -- h_no_shift : ¬ (S₁.status x ≠ S₂.status (T.transport x))
  -- So S₁.status x = S₂.status (T.transport x)
  have h_eq : S₁.status x = S₂.status (T.transport x) := by
    exact not_not.mp h_no_shift
  by_contra! h_not_compat
  -- Then frustration x ≠ compatible, so by frustration_iff, shift exists
  have h_shift : S₁.status x ≠ S₂.status (T.transport x) :=
    (F.frustration_iff x).mpr h_not_compat
  exact h_shift h_eq

/-!
## §G — Shift Witnesses Possible Frustration

If a sectionability shift exists at x, then the frustration field
at x is not compatible.

This does not prove the exact frustration status (it could be
locally_frustrated, globally_frustrated, etc.). It proves only
that compatibility is impossible.

Proof: A shift means S₁.status x ≠ S₂.status (T.transport x).
By frustration_iff, this implies frustration x ≠ compatible.
-/

theorem shift_witnesses_possible_frustration
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ S₂ : HaltField A)
    (F : FrustrationField A B V T S₁ S₂)
    (x : A.State)
    (h_shift : SectionabilityShift A B V T S₁ S₂ x) :
    F.frustration x ≠ FrustrationStatus.compatible :=
  (F.frustration_iff x).mpr h_shift

/-!
## §H — Stable Under Equal Transports

If two transports T₁ and T₂ produce equal sectionability statuses
everywhere, then the irregularity field must be stable everywhere.

Proof: If irregularity x ≠ stable, then by irregularity_iff,
S₁.status x ≠ S₂.status x. But transport equality gives S₁.status x = S₂.status x.
Contradiction.
-/

theorem stable_under_equal_transports
    (A B : MΩ) (V : ExtVer A) (T₁ T₂ : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (F : IrregularityField A B V T₁ T₂ S₁ S₂)
    (hStable : ∀ x, S₁.status x = S₂.status x)
    (x : A.State) :
    F.irregularity x = IrregularityStatus.stable := by
  have h_eq : S₁.status x = S₂.status x := hStable x
  by_contra! h_not_stable
  -- Then irregularity x ≠ stable, so by irregularity_iff, S₁.status x ≠ S₂.status x
  have h_neq : S₁.status x ≠ S₂.status x :=
    (F.irregularity_iff x).mpr h_not_stable
  exact h_neq h_eq

/-!
## §I — What Is Proved

| # | Theorem | Premises | Conclusion |
|---|---------|----------|------------|
| A | `no_frustration_without_shift` | h_no_shift | frustration = compatible |
| B | `shift_witnesses_possible_frustration` | h_shift | frustration ≠ compatible |
| C | `stable_under_equal_transports` | hStable, x | irregularity = stable |

### Unsafe / patched

  - No claim that frustration/irregularity solve halting
  - No claim that sectionability shift implies undecidability
  - No scalar hardness
  - No Euclidean distance as default
  - No human recognition as verification

## §J — Claim Tiers

| Tier | Objects |
|------|---------|
| PROVED | `no_frustration_without_shift`, `shift_witnesses_possible_frustration`, `stable_under_equal_transports` |
| LENS | `SectionabilityShift`, `HasTransportIrregularity` (definitions) |
| UNSAFE/PATCHED | scalar hardness, Euclidean distance, human=verification, solves classical halting |
