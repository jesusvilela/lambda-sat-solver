# Valid Global Bridge — Explicit Compatibility to Obstruction

## Claim Discipline

  This document defines the explicit bridge from candidate global sections
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

## What This Document Contains

1. What was already proved
2. The missing bridge
3. ValidIntermanifoldGlobalHaltSection design
4. Shift obstruction theorem
5. Irregularity obstruction theorem
6. Promotion gate frontier
7. Claim tiers
8. Remaining blockers

## 1. What Was Already Proved

In `OmnifluidManifold.lean`:

  - `nonzero_holonomy_blocks_valid_global_halt`: nonzero holonomy blocks valid global section
  - `local_recognition_not_global_without_flatness`: local recognition cannot be promoted without flatness
  - `human_recognition_not_global_section`: human recognition alone cannot establish valid global section

In `FrustrationIrregularity.lean`:

  - `no_frustration_without_shift`: no frustration without sectionability shift
  - `shift_witnesses_possible_frustration`: shift implies frustration ≠ compatible
  - `stable_under_equal_transports`: equal transports produce stable irregularity field

In `CompatibilityBridge.lean`:

  - `gluing_compatibility_blocks_shift`: gluing compatibility blocks shift
  - `transport_irregularity_blocks_stability_compatibility`: transport irregularity blocks stability compatibility
  - `frustration_irregularity_block_valid_global`: shift + stability → obstruction (with explicit premises)

## 2. The Missing Bridge

The gap: `ValidGlobalHaltSection` in OmnifluidManifold.lean uses `Bool` for
`decides`, while `GluingCompatibility` and `StabilityCompatibility` in
CompatibilityBridge.lean use typed `Sec` regimes. These are different type
systems.

The bridge: `ValidIntermanifoldGlobalHaltSection` bundles a `GlobalSectionCandidate`
with explicit gluing and stability compatibility premises, using the same `Sec`
regime type throughout.

## 3. ValidIntermanifoldGlobalHaltSection

```lean
structure ValidIntermanifoldGlobalHaltSection
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (G : GlobalSectionCandidate A B V T S₁ S₂) where
  gluing : GluingCompatibility A B V T S₁ S₂ G
```

This bundles:
1. A candidate global section G over manifolds A, B
2. Gluing compatibility: G agrees with S₁ and S₂ on locally_decidable states

Stability compatibility is NOT included in the structure. It is taken as
an explicit premise in the obstruction theorem. This is because:

  - `StabilityCompatibility A V T T S₁ S₁` is trivially true (S₁ = S₁)
  - Transport irregularity compares S₁ (on A) with S₂ (on B)
  - The obstruction theorem requires BOTH premises explicitly

## 4. Shift Obstruction Theorem

```lean
Theorem E: shift_blocks_valid_global_halt_section

Premises:
  1. G is a valid intermanifold global halt section candidate
  2. Sectionability shift exists at x
  3. G assigns locally_decidable at x

Conclusion: False (no such valid global section exists)
```

Proof: A valid section has gluing compatibility. By
`shift_blocks_gluing_compatibility`, no candidate with locally_decidable
at x can be gluing-compatible. Contradiction.

The explicit premise `h_regime` (G assigns locally_decidable at x) is
required because the candidate might assign a different regime at x.
This is the honest boundary: a shift blocks validity only where the
candidate claims local decidability.

## 5. Irregularity Obstruction Theorem

```lean
Theorem F: transport_irregularity_blocks_valid_global_halt_section

Premises:
  1. G is a valid intermanifold global halt section candidate
  2. Stability: S₁.status x = S₂.status (T₂.transport x) for all x
  3. Transport irregularity: S₁.status x ≠ S₂.status (T₂.transport x) at x

Conclusion: False (no such valid global section exists)
```

Proof: Stability says S₁.status x = S₂.status (T₂.transport x).
Irregularity says S₁.status x ≠ S₂.status (T₂.transport x).
Contradiction.

## 6. Promotion Gate Frontier

### The full promotion gate

```
ValidIntermanifoldGlobalHaltSection
  → requires GluingCompatibility (proved)
  → requires StabilityCompatibility (proved as explicit premise)
  → requires ExternalVerification (from OAR.lean)
  → requires AdversarialChecking (from OAR.lean)
```

The current `ValidIntermanifoldGlobalHaltSection` bundles gluing but not
stability. The full promotion gate would require both as structure fields,
plus external verification and adversarial checking.

### The σ-external invariant (from OAR.lean)

```lean
theorem σ_external_invariant (x : Fin 8 → ℝ) (h_human : HumanRecognized x)
    (h_no_ext : ¬ ExternallyVerified x) : ¬ ValidGlobalSection x
```

This says: human recognition alone cannot establish a valid global section.
The human is not the verifier.

## 7. Claim Tiers

### PROVED (Lean-safe, explicit premises)

| # | Theorem | File | Premises | Conclusion |
|---|---------|------|----------|------------|
| A | `nonzero_holonomy_blocks_valid_global_halt` | OmnifluidManifold | hdec, H.Hol s ≠ 0 | False |
| B | `local_recognition_not_global_without_flatness` | OmnifluidManifold | h_recog, hdec, H.Hol s ≠ 0 | ¬ ValidGlobalHaltSection |
| C | `human_recognition_not_global_section` | OmnifluidManifold | h_human, ¬ h_ext | ¬ ValidGlobalSection |
| D | `gluing_compatibility_blocks_shift` | CompatibilityBridge | hGlue, h_regime, x | ¬ shift |
| E | `shift_blocks_gluing_compatibility` | CompatibilityBridge | hShift | ¬ (∃ G, regime ∧ gluing) |
| F | `stability_compatibility_blocks_transport_irregularity` | CompatibilityBridge | hStable, x, hIrr | False |
| G | `transport_irregularity_blocks_stability_compatibility` | CompatibilityBridge | hStable, x, hIrr | False |
| H | `frustration_irregularity_block_valid_global` | CompatibilityBridge | shift + stability | False |
| I | `shift_blocks_valid_global_halt_section` | ValidGlobalBridge | hValid, hShift, h_regime | False |
| J | `transport_irregularity_blocks_valid_global_halt_section` | ValidGlobalBridge | hValid, hStable, hIrr | False |

### CONJECTURAL

11. Full promotion gate: `ValidIntermanifoldGlobalHaltSection` with explicit
    stability, external verification, and adversarial checking fields.

### UNSAFE/PATCHED

  - No claim that frustration = hardness
  - No claim that irregularity = distance
  - No numeric scalar hardness by default
  - No human recognition as verification
  - No claim that shift/irregularity imply undecidability
  - No claim that obstruction theorems solve classical halting

## 8. Remaining Blockers

### Formal blockers

1. **Stability premise design**: The obstruction theorem takes stability
   as an explicit premise rather than bundling it in the structure. A
   future version should strengthen `ValidIntermanifoldGlobalHaltSection`
   to include stability, or create a separate `StableGlobalSection`
   structure.

2. **Cross-manifold type alignment**: `StabilityCompatibility` requires
   both S₁ and S₂ on the same manifold. The obstruction theorem works
   around this by using explicit `∀ x, S₁.status x = S₂.status (T₂.transport x)`.
   A future version should generalize `StabilityCompatibility`.

### Empirical blockers

3. **Sectionability classifier**: No empirical algorithm yet classifies
   a submanifold's sectionability regime from instance features.

4. **Frustration field detector**: No empirical measurement of
   frustration/irregularity fields on SAT instances.

5. **Promotion gate validation**: No empirical test that valid global
   sections (with all premises satisfied) correspond to actual halting
   behavior.

## The Full Obstruction Chain

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
transport_irregularity_blocks_valid_global_halt_section
  → irregularity at x + stability premise → NO valid global section
```

This is the spine of the programme. Not scalar hardness. Not Euclidean distance.
Not one manifold. Not "halting solved."

It is a genuine intermanifold obstruction calculus.
