# Semantic Kernel Consolidation

## 1. Duplicate Definitions Found

Two distinct `MachineSemantics` definitions existed in the VDIS layer:

| File | Line | Definition |
|------|------|------------|
| `LambdaSatSolver/VDIS/ValidGlobalBridge.lean` | 312 | `MachineSemantics` (structure) |
| `LambdaSatSolver/VDIS/MachineSemanticBridge.lean` | 74 | `MachineSemantics` (structure) |

Both definitions were identical in structure (4 fields: `State`, `halts`, `halts_dec`, `step`, `step_functional`).

## 2. Canonical Semantic Kernel

Created `LambdaSatSolver/VDIS/MachineSemantics.lean` containing exactly one shared definition:

```lean
structure MachineSemantics where
  State : Type u
  halts : State → Prop
  halts_dec : ∀ s, Decidable (halts s)
  step : State → State → Prop
  step_functional : ∀ s₁ s₂ s₃, step s₁ s₂ → step s₁ s₃ → s₂ = s₃
```

Plus all dependent definitions:
- `Reaches` (inductive)
- `ActuallyHalts` (def)
- `SemanticRepresentation` (structure)
- `RepresentationPreservesHalting` (def)
- `RepresentationReflectsHalting` (def)
- `VerificationVerdict` (inductive)
- `SemanticVerifier` (structure)
- `HaltVerifierSound` (def)

## 3. Refactoring Performed

### Files modified

1. **`LambdaSatSolver/VDIS/MachineSemantics.lean`** (NEW)
   - Single canonical source for all machine semantics definitions

2. **`LambdaSatSolver/VDIS/ValidGlobalBridge.lean`**
   - Added `import LambdaSatSolver.VDIS.MachineSemantics`
   - Removed duplicate `MachineSemantics` definition (was lines 312-322)
   - Removed dead `open Real` (unused in file)
   - Updated import chain documentation
   - Updated §H doc to reference canonical import

3. **`LambdaSatSolver/VDIS/MachineSemanticBridge.lean`**
   - Added `import LambdaSatSolver.VDIS.MachineSemantics`
   - Removed duplicate `MachineSemantics` definition (was lines 74-84)
   - Removed duplicate `Reaches` definition (was lines 90-93)
   - Removed duplicate `ActuallyHalts` definition (was lines 101-102)
   - Removed duplicate `SemanticRepresentation` definition (was lines 120-125)
   - Removed duplicate `VerificationVerdict` definition (was lines 158-162)
   - Removed duplicate `SemanticVerifier` definition (was lines 169-174)
   - Removed duplicate `HaltVerifierSound` definition (was lines 188-191)
   - Removed §A, §B, §C section headers (definitions now in canonical file)
   - Renamed §D → §A (section renumbered)
   - Updated architecture section to reference canonical file
   - Updated import chain documentation

## 4. Explicit Adapters

No adapters required. Both files now import from the same canonical definition.
`SoundPromotion` (in ValidGlobalBridge) and `PromotedSemanticInterpretation` (in MachineSemanticBridge)
use the same `MachineSemantics` type from `MachineSemantics.lean`.

## 5. Independent Compilation Results

### `MachineSemantics.lean`
- LSP diagnostics: 0 errors
- `lake env lean`: compiles clean (exit code 0)
- Status: **INDEPENDENTLY COMPILED**

### `ValidGlobalBridge.lean`
- LSP diagnostics: 0 errors (before import changes)
- `lake env lean`: failed — depends on `OmnifluidManifold.olean` which was removed by `lake clean`
- Status: **BLOCKED** (full rebuild in progress)

### `MachineSemanticBridge.lean`
- LSP diagnostics: imports out of date (after import changes)
- `lake env lean`: failed — depends on `OmnifluidManifold.olean` which was removed by `lake clean`
- Status: **BLOCKED** (full rebuild in progress)

## 6. Full-Build Status

`lake build` is currently rebuilding mathlib from scratch (17298 modules) after `lake clean`.
The build was at step 6181/17298 (36%) when last checked.

Build blocker: `LambdaSatSolver/VDIS/Algebra/CD.lean` has pre-existing errors
(unresolved goals, type mismatches, `sorry` usage) unrelated to this refactoring.

## 7. Remaining Semantic Frontiers

| Frontier | Description |
|----------|-------------|
| Soundness bridge calibration | When does `HaltVerifierSound` hold for real verifiers? |
| Adversarial separation strength | `actors_distinct` (type inequality) vs genuine computational independence |
| Empirical promotion gate validation | Do fully promoted sections correspond to actual machine behavior? |
| Machine semantics instantiation | Concrete `MachineSemantics` for specific computation families (Turing, SAT, lambda) |

## Required Invariant

  Same name is not same semantics.
  One semantic kernel, many manifold representations.
  Representation transport must be explicit.
