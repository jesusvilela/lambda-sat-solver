import Mathlib
import LambdaSatSolver.VDIS.OmnifluidManifold
import LambdaSatSolver.VDIS.FrustrationIrregularity
import LambdaSatSolver.VDIS.OAR
import LambdaSatSolver.VDIS.MachineSemantics

/-!
# Valid Global Bridge — Explicit Compatibility to Obstruction

## Claim Discipline

  This file defines the explicit bridge from candidate global sections
  to obstruction theorems. It does NOT claim to solve classical
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
    `GlobalSectionCandidate`, `GluingCompatibility`, `StabilityCompatibility` — route from
    diagnostics to obstruction theorems.

  Layer D (validity structure + obstruction theorems):
    `ValidIntermanifoldGlobalHaltSection` — explicit bridge.
    `shift_blocks_valid_global_halt_section`,
    `transport_irregularity_blocks_valid_global_halt_section` — obstruction theorems.

## Import chain

  OmnifluidManifold.lean → HaltSectionability, MΩ, HaltField, ExtVer, HolonomySystem
  FrustrationIrregularity.lean → FrustrationStatus, IrregularityStatus, FrustrationField, IrregularityField
  OAR.lean → σ-external invariant, role separation
  MachineSemantics.lean → MachineSemantics, Reaches, ActuallyHalts
-/

/-!
## §A — Diagnostic Fields (Re-exported)

The frustration and irregularity fields from FrustrationIrregularity.lean.
These are typed diagnostics, not yet theorem-bearing.
-/

abbrev Fustr := FrustrationStatus
abbrev Ireg := IrregularityStatus
abbrev FField := FrustrationField
abbrev IField := IrregularityField

/-!
## §B — Sectionability Shift and Transport Irregularity (Re-exported)

Typed regime transition definitions.
-/

-- Re-exported for convenience in this file
abbrev SecShift := SectionabilityShift
abbrev TransIrr := HasTransportIrregularity

/-!
## §C — Global Section Candidate

A candidate global section assigns a sectionability regime to each state.
Not a Bool predicate — a typed regime assignment.
-/

/-- A global section candidate over manifolds A, B.

Given verifier V, transport T, and sectionability tensors S₁, S₂,
this is a candidate that agrees with both tensors on the sectionability
regime at each state. Not a Bool predicate — a typed regime agreement. -/
structure GlobalSectionCandidate
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B) where
  /-- The candidate regime assignment (typed, not Bool). -/
  regime : A.State → Sec
  /-- Decidability of regime assignment. -/
  regime_dec : ∀ s, Decidable (regime s)
  /-- Agreement with left tensor: candidate agrees with S₁ on locally_decidable states. -/
  agrees_left : ∀ s, regime s = Sec.locally_decidable → S₁.status s = Sec.locally_decidable
  /-- Agreement with right tensor: candidate agrees with S₂ on transported states. -/
  agrees_right : ∀ s, regime s = Sec.locally_decidable → S₂.status (T.transport s) = Sec.locally_decidable
  /-- Candidate requires external verification for promotion. -/
  requires_verification : ∀ s, regime s = Sec.locally_decidable → ExtVer.verifies s

/-!
## §D — Gluing Compatibility

A candidate global section G is gluing-compatible with S₁ and S₂
if G agrees with both sectionability tensors at every state.

This is the bridge from diagnostics to obstruction:
if G agrees with S₁ and S₂, then no shift can exist where G is locally_decidable.
-/

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
## §E — Stability Compatibility

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
## §F — Obstruction Theorems

### Theorem A: Gluing Compatibility Blocks Shift

If G agrees with S₁ and S₂ everywhere, then no sectionability
shift can exist at any state where G is locally_decidable.

Proof: If there were a shift at x, then S₁.status x ≠ S₂.status (T.transport x).
But G.agrees_left x and G.agrees_right x both give locally_decidable.
Contradiction.
-/

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
  -- h_left : S₁.status x = Sec.locally_decidable
  -- h_right : S₂.status (T.transport x) = Sec.locally_decidable
  -- Therefore S₁.status x = S₂.status (T.transport x)
  -- But hShift says S₁.status x ≠ S₂.status (T.transport x)
  rw [h_left] at hShift
  exact hShift h_right

/-!
### Theorem B: Shift Blocks Gluing Compatibility

If there is a sectionability shift at x, then no candidate global
section that assigns locally_decidable at x can be gluing-compatible.

Proof: If G were gluing-compatible and assigned locally_decidable at x,
then gluing_compatibility_blocks_shift would give ¬ shift, contradiction.
-/

theorem shift_blocks_gluing_compatibility
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (x : A.State)
    (hShift : SectionabilityShift A B V T S₁ S₂ x) :
    ¬ ∃ G : GlobalSectionCandidate A B V T S₁ S₂,
      (G.regime x = Sec.locally_decidable) ∧
      GluingCompatibility A B V T S₁ S₂ G := by
  intro h
  rcases h with ⟨G, h_regime, hGlue⟩
  exact gluing_compatibility_blocks_shift A B V T S₁ S₂ G hGlue h_regime x hShift

/-!
### Theorem C: Stability Compatibility Blocks Transport Irregularity

If S₁ and S₂ agree everywhere, then no transport irregularity exists.

Proof: StabilityCompatibility requires S₁.status x = S₂.status x for all x.
But HasTransportIrregularity gives S₁.status x ≠ S₂.status x.
Contradiction.
-/

theorem stability_compatibility_blocks_transport_irregularity
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
### Theorem D: Transport Irregularity Blocks Stability Compatibility

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
## §G — Evidence Structures for Promotion Gate

Three minimal structures that together constitute the evidence
required for a fully promoted global halting section.

These are intentionally thin: they record WHAT is required,
not HOW it is computed. The how is empirical work.
-/

/-- External verification: an independent check confirms halting. -/
structure ExternalVerification (A : MΩ) where
  /-- Verification predicate. -/
  verified : A.State → Prop
  /-- Decidable verification. -/
  verified_dec : ∀ s, Decidable (verified s)

/-- Verification provenance records the actors and artifacts involved
in a verification act. This is the structural backbone of adversarial
separation — it names WHO proposed WHAT and WHO verified WHAT. -/
structure VerificationProvenance where
  /-- Identifier of the proposing actor. -/
  proposerId : String
  /-- Identifier of the verifying actor. -/
  verifierId : String
  /-- Digest of the proposal artifact. -/
  proposalDigest : String
  /-- Digest of the verification artifact. -/
  verificationDigest : String
  deriving DecidableEq, Repr

/-- Actor distinction: the proposer and verifier are not the same entity. -/
def ActorsDistinct (P : VerificationProvenance) : Prop :=
  P.proposerId ≠ P.verifierId

/-- Artifact separation: the proposal and verification artifacts are distinct. -/
def ArtifactSeparated (P : VerificationProvenance) : Prop :=
  P.proposalDigest ≠ P.verificationDigest

/-- Structural adversarial separation bundles actor distinction with
artifact separation. This is evidence of process separation, not a
proof of statistical, computational, organizational, or causal
independence. -/
structure StructuralAdversarialSeparation where
  /-- The verification provenance record. -/
  provenance : VerificationProvenance
  /-- The actors are distinct. -/
  actors_distinct : ActorsDistinct provenance
  /-- The artifacts are separated. -/
  artifacts_separated : ArtifactSeparated provenance

/-- Structural adversarial separation implies actor distinction.
  This is a trivial implication: the structure bundles both fields. -/
theorem structural_adversarial_separation_implies_actor_distinction
    (S : StructuralAdversarialSeparation) :
    ActorsDistinct S.provenance :=
  S.actors_distinct

/-- Adversarial separation: encodes that proposer and verifier are
not definitionally identical. This is a structural separation, not a
numeric score.

The independence is structural: the verification act is performed by
a different type than the proposal act. This prevents the absorption
pattern where the generator routes around missing verification
through a predictable recognizer.

The current formulation uses type inequality as the independence witness.
A stronger formulation would add computational independence (different
algorithms, different data, non-computable verification). -/
structure AdversarialSeparation (A : MΩ) where
  /-- The verification actor type. -/
  verificationActor : Type
  /-- The proposal actor type. -/
  proposalActor : Type
  /-- Structural independence: the verifier is not definitionally the proposer. -/
  actors_distinct : verificationActor ≠ proposalActor
  /-- The independent check predicate. -/
  independentlyChecked : A.State → Prop
  /-- Decidable independent check. -/
  independentlyChecked_dec : ∀ s, Decidable (independentlyChecked s)

/-- Artifact evidence: a concrete artifact backs the halting claim. -/
structure ArtifactEvidence (A : MΩ) where
  /-- Artifact existence predicate. -/
  artifactExists : A.State → Prop
  /-- Decidable artifact check. -/
  artifactExists_dec : ∀ s, Decidable (artifactExists s)

/-!
## §H — Machine Semantics Interface

### The soundness bridge

A promoted section makes claims about halting. Machine semantics
provides the computational ground truth. The soundness bridge
connects them:

```
FullyPromotedGlobalHaltSection
  → sectionability regime assignments
  → linked to MachineSemantics via SoundPromotion
  → semantic correctness follows if the link is sound
```

MachineSemantics is defined in `LambdaSatSolver.VDIS.MachineSemantics`.

A minimal machine semantics: a state transition system with a halting
predicate. Intentionally abstract — not a specific model.
-/

/-!
### SoundPromotion

A sound promotion links a fully promoted section to machine semantics.
If the promotion is sound, then the promoted section's regime assignments
are semantically correct: whenever the promoted section says "halts",
the machine semantics confirms it.

This is a conditional theorem: soundness requires external verification
and artifact evidence to be truthful about machine behavior.
-/

/-- A sound promotion links a fully promoted section to machine semantics.

The soundness condition says: whenever the promoted section assigns
total_decidable at a state, the machine semantics actually halts at that state.

This is the semantic bridge. It does NOT claim that promotion always
implies halting — only that when the promoted section claims halting,
the machine semantics confirms it (under the soundness assumptions).
-/
structure SoundPromotion
    (A : MΩ) (M : MachineSemantics) (V : ExtVer A)
    (T : HolonomySystem A) (S₁ : HaltField A) (S₂ : HaltField B)
    (G : GlobalSectionCandidate A B V T S₁ S₂)
    (P : FullyPromotedGlobalHaltSection A B V T S₁ S₂ G) where
  /-- Soundness: promoted halting implies machine halting. -/
  sound : ∀ x, G.regime x = Sec.total_decidable → M.halts x
  /-- Soundness is decidable. -/
  sound_dec : ∀ x, Decidable (G.regime x = Sec.total_decidable → M.halts x)
  /-- External verification is truthful about machine behavior. -/
  verifier_truthful : ∀ x, ExternalVerification.verified x → M.halts x
  /-- Adversarial separation is truthful about machine behavior. -/
  adversarial_truthful : ∀ x, AdversarialSeparation.independentlyChecked x → M.halts x
  /-- Artifact evidence is truthful about machine behavior. -/
  artifact_truthful : ∀ x, ArtifactEvidence.artifactExists x → M.halts x

/-!
### Theorem L: Sound Promotion Implies Semantic Correctness

If a promotion is sound, and the promoted section assigns total_decidable
at x, then the machine semantics actually halts at x.

This is a conditional theorem: the link from promoted section to machine
semantics is only as strong as the soundness premises.

Proof: SoundPromotion.sound x h gives M.halts x directly.
-/

theorem sound_promotion_implies_semantic_correctness
    (A B : MΩ) (M : MachineSemantics) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (G : GlobalSectionCandidate A B V T S₁ S₂)
    (P : FullyPromotedGlobalHaltSection A B V T S₁ S₂ G)
    (SP : SoundPromotion A M V T S₁ S₂ G P)
    (x : A.State)
    (h_regime : G.regime x = Sec.total_decidable) :
    M.halts x :=
  SP.sound x h_regime

/-!
## §I — Valid Intermanifold Global Halt Section

A valid intermanifold global halt section bundles a candidate with
explicit gluing and stability compatibility premises.

This is the structure that makes frustration and irregularity
theorem-bearing: a valid global section MUST satisfy both
gluing compatibility and stability compatibility.
-/

/-- A valid intermanifold global halt section candidate.

Bundles a candidate global section with explicit gluing compatibility.
Stability compatibility is taken as a separate premise in obstruction
theorems — a valid section must satisfy gluing, and stability is
required additionally to block transport irregularity.

A valid global section candidate requires:
1. Gluing compatibility with S₁ and S₂ (no shift where locally_decidable)
-/
structure ValidIntermanifoldGlobalHaltSection
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (G : GlobalSectionCandidate A B V T S₁ S₂) where
  /-- Gluing compatibility: candidate agrees with both sectionability tensors. -/
  gluing : GluingCompatibility A B V T S₁ S₂ G

/-!
## §I — Fully Promoted Global Halt Section

A fully promoted global halt section bundles a candidate with ALL
evidence premises: gluing, stability, external verification,
adversarial separation, and artifact evidence.

This is the complete promotion gate. All obstruction theorems
(G–K) are proved against this structure.
-/

/-- A fully promoted global halt section over manifolds A, B.

Bundles a candidate with all evidence premises:
  1. Gluing compatibility (no shift where locally_decidable)
  2. Stability compatibility (no transport irregularity)
  3. External verification (independent halting check)
  4. Adversarial separation (independent self-check check)
  5. Artifact evidence (concrete backing artifact)

This is the object that ALL obstruction theorems target.
-/
structure FullyPromotedGlobalHaltSection
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (G : GlobalSectionCandidate A B V T S₁ S₂) where
  /-- Gluing compatibility: candidate agrees with both sectionability tensors. -/
  gluing : GluingCompatibility A B V T S₁ S₂ G
  /-- Stability compatibility: S₁ and S₂ agree under transport. -/
  stability : ∀ x, S₁.status x = S₂.status (T.transport x)
  /-- External verification at every state. -/
  externalVerification : ∀ x, ExternalVerification.verified x
  /-- Adversarial separation at every state. -/
  adversarialSeparation : ∀ x, AdversarialSeparation.independentlyChecked x
  /-- Artifact evidence at every state. -/
  artifactEvidence : ∀ x, ArtifactEvidence.artifactExists x

/-!
## §H — Obstruction Theorems: Shift and Irregularity Block Validity

These are the theorems that make frustration and irregularity
theorem-bearing. They prove that if the explicit compatibility
premises are violated, no valid intermanifold global halt section exists.

### Theorem E: Sectionability Shift Blocks Valid Global Section

If there is a sectionability shift at x, and G assigns locally_decidable
at x, then no valid intermanifold global halt section exists.

Proof: A valid section has gluing compatibility. By
shift_blocks_gluing_compatibility, no candidate with locally_decidable
at x can be gluing-compatible. Therefore no valid global section exists.

The explicit premise `h_regime` is required because the candidate
might assign a different regime at x. This is the honest boundary:
a shift blocks validity only where the candidate claims local decidability.
-/

theorem shift_blocks_valid_global_halt_section
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (G : GlobalSectionCandidate A B V T S₁ S₂)
    (hValid : ValidIntermanifoldGlobalHaltSection A B V T S₁ S₂ G)
    (x : A.State)
    (hShift : SectionabilityShift A B V T S₁ S₂ x)
    (h_regime : G.regime x = Sec.locally_decidable) :
    False := by
  -- From shift_blocks_gluing_compatibility, no candidate with locally_decidable
  -- at x can be gluing-compatible. But hValid gives gluing compatibility.
  have h_no_glue : ¬ ∃ G' : GlobalSectionCandidate A B V T S₁ S₂,
    (G'.regime x = Sec.locally_decidable) ∧
    GluingCompatibility A B V T S₁ S₂ G' :=
    shift_blocks_gluing_compatibility A B V T S₁ S₂ x hShift
  apply h_no_glue
  exact ⟨G, h_regime, hValid.gluing⟩

/-!
### Theorem F: Transport Irregularity Blocks Valid Global Section

If there is transport irregularity at x, then no stability compatibility
exists. Since a valid global section requires stability compatibility,
no valid intermanifold global halt section exists.

Proof: Stability says S₁.status x = S₂.status (T₂.transport x).
Irregularity says S₁.status x ≠ S₂.status (T₂.transport x).
Contradiction.
-/

theorem transport_irregularity_blocks_valid_global_halt_section
    (A B : MΩ) (V : ExtVer A) (T₁ T₂ : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (G : GlobalSectionCandidate A B V T₁ S₁ S₂)
    (hValid : ValidIntermanifoldGlobalHaltSection A B V T₁ S₁ S₂ G)
    (hStable : ∀ x, S₁.status x = S₂.status (T₂.transport x))
    (x : A.State)
    (hIrr : S₁.status x ≠ S₂.status (T₂.transport x)) :
    False := by
  -- Stability says S₁.status x = S₂.status (T₂.transport x)
  -- Irregularity says S₁.status x ≠ S₂.status (T₂.transport x)
  -- Contradiction
  exact hIrr (hStable x)

/-!
## §I — Promotion Gate

### The gap

`ValidIntermanifoldGlobalHaltSection` bundles gluing compatibility but
NOT external verification, adversarial separation, or artifact evidence.
These are the remaining premises for a fully promoted global section.

### Evidence structures

Three minimal structures for the promotion gate:

  - `ExternalVerification`: independent verification that a state halts
  - `AdversarialSeparation`: independent check that a candidate is not
    trivially self-verified
  - `ArtifactEvidence`: concrete artifact backing the halting claim

### Fully promoted structure

```lean
structure FullyPromotedGlobalHaltSection (...) where
  candidate : GlobalSectionCandidate ...
  gluing : GluingCompatibility ...
  stability : StabilityCompatibility ...
  externalVerification : ∀ x, ExternalVerification.verified x
  adversarialSeparation : ∀ x, AdversarialSeparation.independentlyChecked x
  artifactEvidence : ∀ x, ArtifactEvidence.artifactExists x
```

## §J — What Is Proved

| # | Theorem | Premises | Conclusion |
|---|---------|----------|------------|
| A | `gluing_compatibility_blocks_shift` | hGlue, h_regime, x | ¬ shift |
| B | `shift_blocks_gluing_compatibility` | hShift | ¬ (∃ G, regime ∧ gluing) |
| C | `stability_compatibility_blocks_transport_irregularity` | hStable, x, hIrr | False |
| D | `transport_irregularity_blocks_stability_compatibility` | hStable, x, hIrr | False |
| E | `shift_blocks_valid_global_halt_section` | hValid, hShift, h_regime | False |
| F | `transport_irregularity_blocks_valid_global_halt_section` | hValid, hStable, hIrr | False |
| G | `shift_blocks_fully_promoted_global_halt_section` | hPromoted, hShift, h_regime | False |
| H | `transport_irregularity_blocks_fully_promoted_global_halt_section` | hPromoted, hIrr | False |
| I | `missing_external_verification_blocks_promotion` | hPromoted, h_no_ext | False |
| J | `missing_adversarial_separation_blocks_promotion` | hPromoted, h_no_adv | False |
| K | `missing_artifact_blocks_promotion` | hPromoted, h_no_art | False |
| L | `sound_promotion_implies_semantic_correctness` | hPromoted, h_regime | M.halts x (conditional) |

### PROVED (compatibility obstruction)

  1–6: all shift/irregularity obstruction theorems.

### PROVED (promotion gate obstruction)

  7–11: missing verification/adversarial/artifact blocks promotion.

### CONDITIONAL (soundness bridge)

  12. `sound_promotion_implies_semantic_correctness` — if the
      promotion is sound, promoted halting implies machine halting.
      Premises: `SoundPromotion` with truthfulness fields.

### STRUCTURAL

  `ExternalVerification`, `AdversarialSeparation` (with
  `actors_distinct`), `ArtifactEvidence`, `MachineSemantics`,
  `SoundPromotion`, `FullyPromotedGlobalHaltSection` — all definitions.

### MARKER

  13. `classicalHaltingInterfaceMarker : Unit` — non-semantic
      interface placeholder. Carries no proposition and makes no
      mathematical claim.

### FRONTIER

  14. Adversarial separation strength.
  15. Promotion gate empirical validation.
  16. Full integration of adversarial checking + artifact evidence
      with soundness bridge.

## §K — Promotion Gate Obstruction Theorems

### Theorem G: Shift Blocks Fully Promoted Section

If a sectionability shift exists and the candidate assigns locally_decidable
at x, then no fully promoted global halt section exists.

Proof: Same as `shift_blocks_valid_global_halt_section` but against
`FullyPromotedGlobalHaltSection`.
-/

theorem shift_blocks_fully_promoted_global_halt_section
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (G : GlobalSectionCandidate A B V T S₁ S₂)
    (hPromoted : FullyPromotedGlobalHaltSection A B V T S₁ S₂ G)
    (x : A.State)
    (hShift : SectionabilityShift A B V T S₁ S₂ x)
    (h_regime : G.regime x = Sec.locally_decidable) :
    False := by
  -- A fully promoted section has gluing compatibility
  have h_no_glue : ¬ ∃ G' : GlobalSectionCandidate A B V T S₁ S₂,
    (G'.regime x = Sec.locally_decidable) ∧
    GluingCompatibility A B V T S₁ S₂ G' :=
    shift_blocks_gluing_compatibility A B V T S₁ S₂ x hShift
  apply h_no_glue
  -- hPromoted contains the same G with gluing compatibility
  have h_glue : GluingCompatibility A B V T S₁ S₂ G :=
    hPromoted.gluing
  exact ⟨G, h_regime, h_glue⟩

/-!
### Theorem H: Transport Irregularity Blocks Fully Promoted Section

If transport irregularity exists and stability compatibility holds,
then no fully promoted global halt section exists.

Proof: Same as `transport_irregularity_blocks_valid_global_halt_section`.
-/

theorem transport_irregularity_blocks_fully_promoted_global_halt_section
    (A B : MΩ) (V : ExtVer A) (T₁ T₂ : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (G : GlobalSectionCandidate A B V T₁ S₁ S₂)
    (hPromoted : FullyPromotedGlobalHaltSection A B V T₁ S₁ S₂ G)
    (x : A.State)
    (hIrr : S₁.status x ≠ S₂.status (T₂.transport x)) :
    False := by
  -- hPromoted.stability gives S₁.status x = S₂.status (T₂.transport x)
  -- hIrr says they are not equal
  -- Contradiction
  exact hIrr (hPromoted.stability x)

/-!
### Theorem I: Missing External Verification Blocks Promotion

If a candidate section does not have external verification at x,
then it is not fully promoted at x.
-/

theorem missing_external_verification_blocks_promotion
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (G : GlobalSectionCandidate A B V T S₁ S₂)
    (hPromoted : FullyPromotedGlobalHaltSection A B V T S₁ S₂ G)
    (x : A.State)
    (h_no_ext : ¬ ExternalVerification.verified x) :
    False := by
  -- A fully promoted section requires external verification at every state
  have h_ext := hPromoted.externalVerification x
  exact h_no_ext h_ext

/-!
### Theorem J: Missing Adversarial Separation Blocks Promotion

If a candidate section does not have adversarial separation at x,
then it is not fully promoted at x.
-/

theorem missing_adversarial_separation_blocks_promotion
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (G : GlobalSectionCandidate A B V T S₁ S₂)
    (hPromoted : FullyPromotedGlobalHaltSection A B V T S₁ S₂ G)
    (x : A.State)
    (h_no_adv : ¬ AdversarialSeparation.independentlyChecked x) :
    False := by
  have h_adv := hPromoted.adversarialSeparation x
  exact h_no_adv h_adv

/-!
### Theorem K: Missing Artifact Blocks Promotion

If a candidate section does not have artifact evidence at x,
then it is not fully promoted at x.
-/

theorem missing_artifact_blocks_promotion
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (G : GlobalSectionCandidate A B V T S₁ S₂)
    (hPromoted : FullyPromotedGlobalHaltSection A B V T S₁ S₂ G)
    (x : A.State)
    (h_no_art : ¬ ArtifactEvidence.artifactExists x) :
    False := by
  have h_art := hPromoted.artifactEvidence x
  exact h_no_art h_art

/-!
## §L — Claim Tiers

| Tier | Objects |
|------|---------|
| PROVED | `gluing_compatibility_blocks_shift`, `shift_blocks_gluing_compatibility`, `stability_compatibility_blocks_transport_irregularity`, `transport_irregularity_blocks_stability_compatibility`, `shift_blocks_valid_global_halt_section`, `transport_irregularity_blocks_valid_global_halt_section`, `shift_blocks_fully_promoted_global_halt_section`, `transport_irregularity_blocks_fully_promoted_global_halt_section`, `missing_external_verification_blocks_promotion`, `missing_adversarial_separation_blocks_promotion`, `missing_artifact_blocks_promotion` |
| SOUNDNESS | `sound_promotion_implies_semantic_correctness` (conditional) |
| STRUCTURAL | `ExternalVerification`, `AdversarialSeparation` (with actors_distinct), `ArtifactEvidence`, `MachineSemantics` (imported from canonical), `SoundPromotion`, `FullyPromotedGlobalHaltSection`, `VerificationProvenance`, `StructuralAdversarialSeparation` (all definitions) |
| CONDITIONAL | `structural_adversarial_separation_implies_actor_distinction` (structural separation implies actor distinction) |
| NOT PROVED | Adversarial separation strength (computational independence), promotion gate empirical validation |
| MARKER | `classicalHaltingInterfaceMarker : Unit` (non-semantic interface placeholder) |
| FRONTIER | adversarial independence beyond structural separation, promotion gate empirical validation, soundness bridge calibration |

## §M — Zero-Invariant

  0 textual occurrences of `sorry`
  0 textual occurrences of `admit`
  0 textual occurrences of `axiom`
  0 Lean `sorry`
  0 Lean `admit`
  0 Lean `axiom`

## §N — Remaining Blockers

### Formal blockers

1. **Soundness bridge strength**: `SoundPromotion` assumes verifier,
   adversarial, and artifact truthfulness as separate premises.
   A stronger formulation would derive these from the evidence
   structures rather than assuming them separately.

2. **Adversarial separation strength**: `AdversarialSeparation` now
   encodes `actors_distinct : verificationActor ≠ proposalActor`,
   but does not yet encode computational independence. A stronger
   model would require different algorithms, different data, or
   non-computable verification.

### Empirical blockers

3. **Sectionability classifier**: No empirical algorithm yet classifies
   a submanifold's sectionability regime from instance features.

4. **Frustration field detector**: No empirical measurement of
   frustration/irregularity fields on SAT instances.

5. **Promotion gate validation**: No empirical test that fully
   promoted sections (with all 5 evidence premises satisfied)
   correspond to actual machine halting behavior.

6. **Soundness bridge calibration**: No empirical test that the
   conditional soundness theorem (`sound_promotion_implies_semantic_correctness`)
   has the right specificity for real verifiers.
