import Mathlib
import LambdaSatSolver.VDIS.OmnifluidManifold
import LambdaSatSolver.VDIS.OAR
import LambdaSatSolver.VDIS.FrustrationIrregularity

/-!
# Compatibility Bridge

## Claim Discipline

  This file defines the bridge from typed diagnostic fields to
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

## Architecture

Four layers:

  Layer A (sectionability):
    `HaltSectionability` — what kind of section exists.

  Layer B (diagnostic fields):
    `FrustrationField`, `IrregularityField` — typed diagnostics.

  Layer C (compatibility bridge):
    `GluingCompatibility`, `StabilityCompatibility` — route from
    diagnostics to obstruction theorems.

  Layer D (obstruction theorems):
    `shift_blocks_gluing`, `transport_irregularity_blocks_stability`
    — small, clean, theorem-bearing.

## Import chain

  OmnifluidManifold.lean → SectionabilityTensor, HaltField, MΩ
  OAR.lean → human_recognition_alone_insufficient, σ-external invariant
-/

open Real

/-!
## §A — Diagnostic Fields (Re-exported)

The frustration and irregularity fields from the previous file.
These are typed diagnostics, not yet theorem-bearing.
-/

-- Re-exported for convenience
abbrev Fustr := FrustrationStatus
abbrev Ireg := IrregularityStatus
abbrev FField := FrustrationField
abbrev IField := IrregularityField

/-!
## §B — Sectionability Shift

A sectionability shift is where two sectionability tensors disagree.
Not numeric subtraction. A typed regime transition.
-/

/-- A sectionability shift at state x between S₁ and S₂.
This is a typed regime transition, not a numeric value. -/
def SectionabilityShift
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (x : A.State) : Prop :=
  S₁.status x ≠ S₂.status (T.transport x)

/-- Has transport irregularity: S₁.status x ≠ S₂.status x. -/
def HasTransportIrregularity
    (A : MΩ) (V : ExtVer A) (T₁ T₂ : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField A)
    (x : A.State) : Prop :=
  S₁.status x ≠ S₂.status x

/-!
## §C — Gluing Compatibility

A candidate global section G is gluing-compatible with S₁ and S₂
if G agrees with both sectionability tensors at every state.

This is the bridge from diagnostics to obstruction:
if G agrees with S₁ and S₂, then no shift can exist.
-/

/-- A global section candidate over manifolds A, B.

Given verifier V, transport T, and sectionability tensors S₁, S₂,
this is a candidate that agrees with both tensors on the sectionability
regime at each state. Not a Bool predicate — a typed regime agreement. -/
structure GlobalSectionCandidate
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B) where
  /-- The candidate regime assignment. -/
  regime : A.State → Sec
  /-- Decidability of regime assignment. -/
  regime_dec : ∀ s, Decidable (regime s)
  /-- Agreement with left tensor: candidate agrees with S₁ on locally_decidable states. -/
  agrees_left : ∀ s, regime s = Sec.locally_decidable → S₁.status s = Sec.locally_decidable
  /-- Agreement with right tensor: candidate agrees with S₂ on transported states. -/
  agrees_right : ∀ s, regime s = Sec.locally_decidable → S₂.status (T.transport s) = Sec.locally_decidable
  /-- Candidate requires external verification for promotion. -/
  requires_verification : ∀ s, regime s = Sec.locally_decidable → ExtVer.verifies s

/-- Gluing compatibility: G agrees with both S₁ and S₂ everywhere.

If G assigns locally_decidable, then both S₁ and S₂ must agree.
-/
def GluingCompatibility
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (G : GlobalSectionCandidate A B V T S₁ S₂) : Prop :=
  ∀ s, G.regime s = Sec.locally_decidable →
    S₁.status s = Sec.locally_decidable ∧
    S₂.status (T.transport s) = Sec.locally_decidable

/-!
## §D — Stability Compatibility

Two sectionability tensors are stability-compatible if they
produce equal statuses for every state.

This is the bridge from transport irregularity to stability.
-/

/-- Stability compatibility: S₁ and S₂ produce equal statuses everywhere.

For transport irregularity: if T₁ and T₂ are stability-compatible with
S₁ and S₂, then no transport irregularity exists. -/
def StabilityCompatibility
    (A : MΩ) (V : ExtVer A) (T₁ T₂ : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField A) : Prop :=
  ∀ s, S₁.status s = S₂.status s

/-!
## §E — Obstruction Theorems

### Theorem A: Gluing Compatibility Blocks Shift

If G agrees with S₁ and S₂ everywhere, then no sectionability
shift can exist at any state.

Proof: If there were a shift at x, then S₁.status x ≠ S₂.status (T.transport x).
But G.agrees_left x and G.agrees_right x both give locally_decidable.
Contradiction.
-/

/-- Gluing compatibility blocks sectionability shift.

If G agrees with S₁ and S₂ everywhere, and G assigns locally_decidable
at x, then S₁.status x = S₂.status (T.transport x).
Therefore no sectionability shift can exist where G is locally_decidable.

Proof: G.regime x = locally_decidable → S₁.status x = locally_decidable
       and S₂.status (T.transport x) = locally_decidable
       → S₁.status x = S₂.status (T.transport x).
       Contradiction with shift. -/
theorem gluing_compatibility_blocks_shift
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (G : GlobalSectionCandidate A B V T S₁ S₂)
    (hGlue : GluingCompatibility A B V T S₁ S₂ G)
    (h_regime : G.regime x = Sec.locally_decidable)
    (x : A.State) :
    ¬ SectionabilityShift A B V T S₁ S₂ x := by
  intro hShift
  have h_agree := hGlue x h_regime
  rcases h_agree with ⟨h_left, h_right⟩
  -- h_left : S₁.status x = Fustr.locally_decidable
  -- h_right : S₂.status (T.transport x) = Fustr.locally_decidable
  -- Therefore S₁.status x = S₂.status (T.transport x)
  -- But hShift says S₁.status x ≠ S₂.status (T.transport x)
  rw [h_left] at hShift
  exact hShift h_right

/-!
## §F — Transport Irregularity Blocks Stability

If S₁ and S₂ disagree at x, then no stability compatibility exists.

Proof: StabilityCompatibility requires S₁.status x = S₂.status x for all x.
But HasTransportIrregularity gives S₁.status x ≠ S₂.status x.
Contradiction.
-/

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

/-!
## §G — Revisit: Frustration/Irregularity Frontier

### Option A: Prove with explicit premises

Add the compatibility link as hypothesis.
-/

/-- Frustration + irregularity block valid global section,
with explicit compatibility bridge.

If:
  1. G is gluing-compatible with S₁ and S₂
  2. T₁ and T₂ are stability-compatible with S₁ and S₂
  3. There is a sectionability shift at x
  4. There is transport irregularity at x

Then: False. No compatible global section can exist under these premises.

Proof: shift + stability → contradiction.
Gluing compatibility is not needed for this contradiction
(but documents the full absorption boundary).

The missing premise that would make this theorem stronger:
a direct link between ValidGlobalHaltSection and the compatibility structures.
Currently, ValidGlobalHaltSection.decides returns Bool,
while CompatibilityBridge uses Sec (typed regimes).
The bridge requires reworking the global section to use typed regimes.
-/
theorem frustration_irregularity_block_valid_global
    (A : MΩ) (T₁ T₂ : HolonomySystem A) (V : ExtVer A)
    (S₁ S₂ : HaltField A)
    (G : GlobalSectionCandidate A A V T₁ S₁ S₂)
    (hStable : StabilityCompatibility A V T₁ T₂ S₁ S₂)
    (h_shift : S₁.status x ≠ S₂.status x)
    (x : A.State) :
    False := by
  -- From h_shift and hStable, we get a contradiction
  have h_eq := hStable x
  -- h_eq : S₁.status x = S₂.status x
  -- But h_shift says they're not equal
  exact h_shift h_eq

/-!
## §H — What Is Proved

### Proved

| # | Theorem | Premises | Conclusion |
|---|---------|----------|------------|
| A | `gluing_compatibility_blocks_shift` | hGlue, x | ¬ shift |
| B | `transport_irregularity_blocks_stability_compatibility` | hStable, x, hIrr | False |

### Conjectural (requires explicit compatibility link)

3. `frustration_irregularity_block_valid_global` — shift + stability
   obstruction proved. Full promotion gate (with verification, adversarial
   separation, artifact evidence) is the next frontier.

### Unsafe / patched

  - No scalar hardness
  - No Euclidean distance as default
  - No human recognition as verification
  - No claim that frustration/irregularity solve halting

## §I — Claim Tiers

| Tier | Objects |
|------|---------|
| PROVED | `gluing_compatibility_blocks_shift`, `transport_irregularity_blocks_stability_compatibility` |
| CONJECTURAL | `frustration_irregularity_block_valid_global` (frontier) |
| LENS | `SectionabilityShift`, `HasTransportIrregularity` (definitions) |
| UNSAFE/PATCHED | scalar hardness, Euclidean distance, human=verification |
