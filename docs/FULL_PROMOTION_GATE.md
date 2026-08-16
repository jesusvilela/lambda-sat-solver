# Full Promotion Gate

## Claim Discipline

  This document defines the complete promotion gate from candidate
  global sections to fully promoted, externally verified, adversarially
  separated, artifact-backed halting claims.

  Core slogans:
  *Frustration becomes theorem-bearing only through a compatibility bridge.*
  *Irregularity becomes theorem-bearing only through a stability bridge.*
  *Verification is not human recognition.*
  *A promoted section is not a candidate — it has passed all gates.*
  *No gate is closed without explicit premises.*
  *We are not collapsing to scalar hardness.*
  *We are not treating Euclidean distance as default.*
  *We are not treating human recognition as verification.*

## What This Document Contains

1. What was already proved
2. The promotion gap
3. Evidence structures
4. Fully promoted structure
5. Obstruction theorems (promotion gate)
6. Distinctions
7. Claim tiers
8. Remaining blockers

## 1. What Was Already Proved

In `FrustrationIrregularity.lean`:

  - `no_frustration_without_shift`: no frustration without sectionability shift
  - `shift_witnesses_possible_frustration`: shift implies frustration ≠ compatible
  - `stable_under_equal_transports`: equal transports produce stable irregularity field

In `CompatibilityBridge.lean`:

  - `gluing_compatibility_blocks_shift`: gluing compatibility blocks shift
  - `shift_blocks_gluing_compatibility`: shift blocks gluing compatibility
  - `stability_compatibility_blocks_transport_irregularity`: stability blocks transport irregularity
  - `transport_irregularity_blocks_stability_compatibility`: transport irregularity blocks stability
  - `frustration_irregularity_block_valid_global`: shift + stability → obstruction

In `ValidGlobalBridge.lean`:

  - `shift_blocks_valid_global_halt_section`: shift blocks valid global section
  - `transport_irregularity_blocks_valid_global_halt_section`: irregularity blocks valid global section

## 2. The Promotion Gap

### Two levels of validity

```
Level 1 (compatibility):
  ValidIntermanifoldGlobalHaltSection
    = candidate + gluing compatibility
    → blocked by: shift, transport irregularity

Level 2 (promotion):
  FullyPromotedGlobalHaltSection
    = candidate + gluing + stability + external verification
                        + adversarial separation + artifact evidence
    → blocked by: shift, transport irregularity, missing verification,
                  missing adversarial check, missing artifact
```

The promotion gate adds three evidence layers on top of compatibility.

### The σ-external invariant (from OAR.lean)

```lean
theorem σ_external_invariant (x : Fin 8 → ℝ) (h_human : HumanRecognized x)
    (h_no_ext : ¬ ExternallyVerified x) : ¬ ValidGlobalSection x
```

Human recognition is not external verification. The human is not the verifier.

## 3. Evidence Structures

### ExternalVerification

```lean
structure ExternalVerification (A : MΩ) where
  verified : A.State → Prop
  verified_dec : ∀ s, Decidable (verified s)
```

Independent check that a state satisfies the halting predicate.
Not human recognition. Not model self-evaluation.

### AdversarialSeparation

```lean
structure AdversarialSeparation (A : MΩ) where
  independentlyChecked : A.State → Prop
  independentlyChecked_dec : ∀ s, Decidable (independentlyChecked s)
```

Independent check that the candidate is not trivially self-verified.
Prevents the absorption pattern where the generator routes around
missing verification through a predictable recognizer.

### ArtifactEvidence

```lean
structure ArtifactEvidence (A : MΩ) where
  artifactExists : A.State → Prop
  artifactExists_dec : ∀ s, Decidable (artifactExists s)
```

Concrete artifact backing the halting claim. The artifact is
the proof object, not the human, not the model.

## 4. Fully Promoted Structure

```lean
structure FullyPromotedGlobalHaltSection
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (G : GlobalSectionCandidate A B V T S₁ S₂) where
  gluing : GluingCompatibility A B V T S₁ S₂ G
  stability : ∀ x, S₁.status x = S₂.status (T.transport x)
  externalVerification : ∀ x, ExternalVerification.verified x
  adversarialSeparation : ∀ x, AdversarialSeparation.independentlyChecked x
  artifactEvidence : ∀ x, ArtifactEvidence.artifactExists x
```

The complete promotion gate. Every field is a typed predicate —
no numeric scores, no Euclidean distance, no scalar hardness.

## 5. Obstruction Theorems

### Shift obstruction

| Theorem | Premises | Conclusion |
|---------|----------|------------|
| `shift_blocks_fully_promoted_global_halt_section` | hPromoted, hShift, h_regime | False |

If a sectionability shift exists at x and G assigns locally_decidable at x,
then no fully promoted section exists. Proof: shift blocks gluing
compatibility, and a fully promoted section requires gluing.

### Transport irregularity obstruction

| Theorem | Premises | Conclusion |
|---------|----------|------------|
| `transport_irregularity_blocks_fully_promoted_global_halt_section` | hPromoted, hIrr | False |

If S₁.status x ≠ S₂.status (T.transport x), then no fully promoted
section exists. Proof: stability premise in FullyPromoted gives
S₁.status x = S₂.status (T.transport x), contradiction.

### Missing external verification obstruction

| Theorem | Premises | Conclusion |
|---------|----------|------------|
| `missing_external_verification_blocks_promotion` | hPromoted, h_no_ext | False |

If ExternalVerification.verified x fails at any x, the section
is not fully promoted. Proof: FullyPromoted.externalVerification x
gives verified x, contradiction.

### Missing adversarial separation obstruction

| Theorem | Premises | Conclusion |
|---------|----------|------------|
| `missing_adversarial_separation_blocks_promotion` | hPromoted, h_no_adv | False |

If AdversarialSeparation.independentlyChecked x fails, the section
is not fully promoted. Proof: FullyPromoted.adversarialSeparation x
gives independentlyChecked x, contradiction.

### Missing artifact obstruction

| Theorem | Premises | Conclusion |
|---------|----------|------------|
| `missing_artifact_blocks_promotion` | hPromoted, h_no_art | False |

If ArtifactEvidence.artifactExists x fails, the section is not
fully promoted. Proof: FullyPromoted.artifactEvidence x gives
artifactExists x, contradiction.

## 6. Required Distinctions

### compatible ≠ verified

A section can be gluing-compatible (all local sections agree)
but not externally verified. Example:
  - CDCL manifold: locally_decidable (compatible)
  - Human says "looks halting" (recognized but not verified)
  - GF(2) manifold: externally_verifiable (verified)

### stable ≠ verified

Transport stability means S₁.status = S₂.status under transport.
External verification means an independent check confirms halting.
These are independent predicates.

### recognized ≠ verified

`HumanRecognized x` does not imply `ExternallyVerified x`.
The σ-external invariant encodes this separation.

### artifact-mentioned ≠ artifact-present

`requires_verification` in GlobalSectionCandidate says the candidate
NEEDS verification. `artifactEvidence` in FullyPromoted says the
artifact EXISTS. These are different states of affairs.

### candidate global section ≠ fully promoted global section

A candidate assigns regimes. A fully promoted section has passed
all evidence gates. Promotion is not automatic.

## 7. Claim Tiers

### PROVED (11 theorems)

| # | Theorem | Layer |
|---|---------|-------|
| 1 | `gluing_compatibility_blocks_shift` | Compatibility |
| 2 | `shift_blocks_gluing_compatibility` | Compatibility |
| 3 | `stability_compatibility_blocks_transport_irregularity` | Compatibility |
| 4 | `transport_irregularity_blocks_stability_compatibility` | Compatibility |
| 5 | `frustration_irregularity_block_valid_global` | Compatibility |
| 6 | `shift_blocks_valid_global_halt_section` | Compatibility |
| 7 | `transport_irregularity_blocks_valid_global_halt_section` | Compatibility |
| 8 | `shift_blocks_fully_promoted_global_halt_section` | Promotion |
| 9 | `transport_irregularity_blocks_fully_promoted_global_halt_section` | Promotion |
| 10 | `missing_external_verification_blocks_promotion` | Promotion |
| 11 | `missing_adversarial_separation_blocks_promotion` | Promotion |
| 12 | `missing_artifact_blocks_promotion` | Promotion |

### MARKER (1)

  13. `classical_halting_interface_marker` — classical undecidability
      boundary. Not proved. Not claimed. Future proof obligation only.

### FRONTIER (1)

  14. Full integration of adversarial checking + artifact evidence with
      empirical promotion gate validation.

### LENS (definitions)

  `FrustrationStatus`, `IrregularityStatus`, `SectionabilityShift`,
  `HasTransportIrregularity`, `FrustrationField`, `IrregularityField`,
  `GlobalSectionCandidate`, `GluingCompatibility`, `StabilityCompatibility`,
  `ExternalVerification`, `AdversarialSeparation`, `ArtifactEvidence`,
  `ValidIntermanifoldGlobalHaltSection`, `FullyPromotedGlobalHaltSection`

### UNSAFE/PATCHED

  - scalar hardness
  - Euclidean distance as default
  - human recognition as verification
  - solves classical halting

## 8. Remaining Blockers

### Formal blockers

1. **Promotion gate validation**: No empirical test that fully
   promoted sections (with all 5 premises satisfied) correspond to
   actual halting behavior in a computational system.

2. **Adversarial separation strength**: The current
   `AdversarialSeparation` is a thin predicate. A stronger formulation
   would require the adversary to be computationally independent of
   the candidate generator.

### Empirical blockers

3. **Sectionability classifier**: No empirical algorithm yet
   classifies a submanifold's sectionability regime from instance features.

4. **Frustration field detector**: No empirical measurement of
   frustration/irregularity fields on SAT instances.

5. **Promotion gate calibration**: No empirical test that the
   5-premise promotion gate has the right specificity for halting
   detection.

## The Complete Obstruction Chain

```
SectionabilityTensor S₁, S₂
  ↓
SectionabilityShift / HasTransportIrregularity
  ↓
FrustrationField / IrregularityField
  ↓
GluingCompatibility / StabilityCompatibility
  ↓
ValidIntermanifoldGlobalHaltSection (candidate + gluing)
  ↓
shift_blocks_valid_global_halt_section
  → shift at x + locally_decidable at x → NO valid global section
  ↓
FullyPromotedGlobalHaltSection (candidate + gluing + stability + verification + adversarial + artifact)
  ↓
shift_blocks_fully_promoted_global_halt_section
  → shift + locally_decidable → NO fully promoted section
  ↓
transport_irregularity_blocks_fully_promoted_global_halt_section
  → irregularity → NO fully promoted section
  ↓
missing_external_verification_blocks_promotion
  → no verification → NO promotion
  ↓
missing_adversarial_separation_blocks_promotion
  → no adversarial check → NO promotion
  ↓
missing_artifact_blocks_promotion
  → no artifact → NO promotion
```

Every block is explicit. Every premise is named. No gate is closed
without typed justification.
