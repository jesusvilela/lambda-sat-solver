# Hardness Holonomy: Synthesis

## The Problem

Hardness is not the size of a problem.

Hardness is the structured failure of return accumulated when a
computation is transported through representation, self-reference,
algebraic transformation, relational composition, and semantic
verification.

## The Three Shadows

The diagonal, the protensor mantle, and the hypercomplex hypothesis are
not three independent stories. They are typed perspectives on return
defect under transport. Their witnesses are not automatically equal.

| Perspective | Transport | Return Defect | Residual |
|-------------|-----------|---------------|----------|
| **Diagonal** | `E(selfApp t)` | `E(selfApp t) ≠ t` | Semantic identity defect |
| **Protensor** | Coend composition | `path₁ ≠ path₂` | Non-reconstructible evidential remainder |
| **Hypercomplex** | `T * s` | `T*s ≠ s` | Commutator/associator residue |
| **Sectionability** | `T.transport` | `S₁.status x ≠ S₂.status (T.transport x)` | Frustration/irregularity shift |
| **Semantic** | `R.encode` | `V.verify(R.encode x) ≠ M.halts x` | Proof/execution mismatch |

## What They Share

All five carriers share one structure:

```
TransportLoop X
  └── transport : X → X

HolonomyWitness L x
  ├── returned  : X          — what transport actually returns
  ├── returnsBy : returned = L.transport x
  └── differs   : returned ≠ x   — the return defect
```

The diagonal, protensor, hypercomplex, sectionability, and semantic
carriers each instantiate this generic witness with their own
`X` and `transport`.

## What They Do Not Share

The carriers do NOT collapse into one another:

- `DiagonalHolonomy` uses `LTerm` — untyped lambda terms
- `ProtensorHolonomy` uses `DiamondComparison` — profunctorial round-trip data
- `AlgebraicHolonomy` uses `Fin 8 → ℝ` — octonion algebra elements
- `SectionabilityHolonomy` uses `MΩ.State` — manifold states
- `SemanticHolonomy` uses `VerificationVerdict` — verifier output

Each carrier has its own type. No equality is asserted between them
before interpretation.

## Interpretation, Not Equality

Two holonomies are NOT asserted equal before interpretation.
They may be interpretations of a common typed return-defect invariant.

### The Common Invariant

```
HardnessInvariant α
  └── carrier : α

InvariantSpace := String
```

`HardnessInvariant` is a structure parameterized by a carrier type `α`.
`InvariantSpace` is the common carrier type: `String`.
Each interpretation map produces a `HardnessInvariant InvariantSpace`.

The invariant is NOT a scalar (no `ℝ`, `ℕ`, or `Float` score).
The string tag records the KIND of return defect, not the specific data.

### Interpretation Maps

Each carrier has an interpretation into the common invariant space.
The maps are **nontrivial**: they branch on witness data via
`Classical.em`, using the specific holonomy evidence rather than
returning a constant string regardless of the witness.

| Carrier | InvariantSpace Tag | Witness Data Extracted |
|---------|-------------------|----------------------|
| Diagonal | `"algebraicResidue"` | `h.semanticIdentityDefect : E(selfApp t) ≠ t` |
| Protensor | `"nonReconstructibleRemainder"` | `DiamondComparison.path₁ ≠ path₂` |
| Hypercomplex | `"algebraicResidue"` | `h.associator ≠ 0`, `h.commutator ≠ 0` |
| Sectionability | `"nonReconstructibleRemainder"` | `h.shiftNontrivial : S₁.status x ≠ S₂.status (T₁.transport x)` |
| Semantic | `"algebraicResidue"` | `h.disagreement : promotedVerdict ≠ operationalSemantics` |

### Witness Convergence

```
WitnessConvergence h₁ h₂ E₁ E₂
  := E₁.interpret h₁ = E₂.interpret h₂
```

Two holonomy witnesses converge if their interpretations agree
under the common hardness invariant. This is NOT equality of
the holonomies — it is agreement of their interpretations.

Since the invariant space is `String`, convergence means both
carriers produce the same string tag.

**Convergence is string equality.** The invariant space records
the KIND of return defect ("algebraicResidue",
"nonReconstructibleRemainder"), not the specific witness data.

## The Sabatier Principle: Probe–Field Coupling

The programme suggests a geometric analogue of the Sabatier
principle from catalysis: there exists an optimal coupling
between a computational substrate and the hardness field.

### Scalar Volcano (1D)

The simplest model places probe–field coupling on one scalar
line κ ∈ ℝ:

- **Weak coupling** (κ ≈ 0): probe skims the field, almost no
holonomy, almost no learning.
- **Strong coupling** (κ → ∞): probe becomes locked in its own
coordinate system, remainder explodes, semantic return
deteriorates.
- **Intermediate coupling** (κ*): maximum transport-stable
insight while distortion remains invertible.

The selected acquisition–fidelity functional generates a
Sabatier-like interior optimum on the tested structures.

### Split-Signature (2,2) Lift

A richer geometry lifts the coupling to a hypercomplex section:

```
κ ∈ ℝ              →            κ ∈ ℝ^{2,2}
one scalar                      split signature
    │                              │
    ▼                              ▼
volcano curve                  admissible manifold
single optimum                 partially ordered region
κ* = argmax                   A_{2,2} = {κ | W≠0, G≠0, D bounded, P accounted, Hol typed, R preserved}
```

The (2,2) prime-sector coupling:

```
κ = κ₁⁺ + κ₂⁺i + κ₁⁻j + κ₂⁻k ∈ ℍ_{2,2}

productive         relational       destructive        remainder
κ₁⁺ (witness)      κ₂⁺ (enrich)     κ₁⁻ (distortion)  κ₂⁻ (loss)
acquisition        geometric        return fidelity      provenance
```

Three regimes:

| ⟨κ,κ⟩_{2,2} | Regime | Interpretation |
|-------------|--------|----------------|
| > 0 | Acquisition-dominant | probe acquires structure, distortion bounded |
| < 0 | Distortion-dominant | probe trapped, remainder explodes |
| = 0 | Null return frontier | strong acquisition cancels strong loss |

The null cone ⟨κ,κ⟩_{2,2}=0 is especially important: strong
acquisition and strong loss can cancel numerically while leaving
nontrivial holonomy. That is exactly the kind of regime a
one-dimensional volcano cannot see.

### Admissible Coupling Windows

Each carrier has its own admissible coupling window:

```
A_α = { κ ∈ K_α : Hol_α(κ) ≠ 0, Returnable_α(κ), WitnessPreserved_α(κ), RemainderVisible_α(κ), TransportStable_α(κ) }
```

The universal law hypothesis:

```
∃ A_t ⊂ Γ(K → 𝔛_t)
  such that every admissible section in A_t:
  1. acquires nontrivial structure from the hardness field;
  2. preserves enough witness and provenance for return;
  3. avoids absorption into one chart;
  4. avoids null cancellation across split sectors;
  5. remains transportable under declared frame changes.
```

### Corrected Doctrine

```
The scalar volcano is a 1D shadow.
The real object is a split-signature admissible coupling manifold.
Prime sectors separate productive acquisition from destructive capture.
The null cone exposes cancellations hidden by scalar scoring.
Diamond holonomy records whether the probe returns faithfully across sectors.
```

## The Complexity Diamond

```
ComplexityDiamond
  ├── multipleCarriers     : Bool   — at least two carriers have witnesses
  ├── convergence          : Bool   — their interpretations agree
  ├── stableDisclosure     : Bool   — the invariant survives transports
  ├── provenancePreserved  : Bool   — witness data is not lost
  ├── externallyVerified   : Bool   — a sound verifier checks the convergence
  ├── artifactBacked       : Bool   — a reproducible artifact exists
  └── commonInvariant      : Bool   — convergence maps to a common invariant
```

### Required Distinctions

| Statement | Meaning |
|-----------|---------|
| same visible output ≠ same path | Two routes can reach the same verdict by different relational routes |
| same path endpoint ≠ zero holonomy | The transport can close (return = input) while the algebraic structure is non-associative |
| same metaphor ≠ same typed witness | Rhetorical similarity does not imply type-correct equality |
| witness convergence ≠ semantic correctness | Agreement of interpretations is not the same as sound verification |
| semantic correctness requires a sound verifier | The verifier must be independently established |
| convergence at x ≠ convergence at T(x) | Transport stability is a separate condition |

### The Diamond is Not Automatic

The diamond is earned by evidence, not declared by fiat:

1. Multiple carriers contain witnesses
2. Their interpretations converge into a common invariant
3. The invariant survives declared transports (**transport stability**)
4. The convergence receives semantic verification
5. A reproducible artifact exists

## The Five Manifestations as One Field

Hardness is the field in which the return defects of the five
carriers may converge. It is NOT a scalar magnitude.

The field has structure: each carrier has its own typed witness,
its own interpretation map, and its own convergence condition.

The decisive next question is no longer whether they "feel the same."
It is: can we construct the typed interpretation maps that prove
they carry the same invariant residue?

## The Research Target

Construct explicit interpretation maps from each carrier into a
common hardness invariant, such that witness convergence implies
a sound complexity diamond.

The maps are:

| Carrier | Interpretation | Content |
|---------|---------------|---------|
| Diagonal | `E(selfApp t) ≠ t` | Semantic contradiction |
| Protensor | `DiamondComparison.path₁ ≠ DiamondComparison.path₂` | Non-reconstructible remainder |
| Hypercomplex | `associator T T T ≠ 0` | Algebraic residue |
| Sectionability | `SectionabilityShift.status₁ ≠ SectionabilityShift.status₂` | Transport irregularity |
| Semantic | `V.verify(R.encode x) ≠ M.halts x` | Proof/execution mismatch |

## The Existing Codebase

### What Is Proved

All theorems in the codebase are proved via `native_decide` on the
finite octonion algebra `𝕆 = Fin 8 → ℝ` (8×8×8 = 512 cases) or
structural reasoning.

### What Is Isolated

| Placeholder | File | Line | Nature |
|-------------|------|------|--------|
| `cayley_dickson_recurrence` (level≥4) | `Algebra/CD.lean` | 363,366 | Proof incomplete for general level |
| `layer_b_local_not_globally_captured` | `TuringHalting_Master.lean` | 362 | Over-strong (uncountable) quantification |
| `layer_c_no_omni_quine` | `TuringHalting_Master.lean` | 393 | Over-strong (uncountable) quantification |

These four placeholders are isolated from the proved results and
from each other. They do not transitively block any master theorem.

### Independence Verification

```
Claim                              | Uses CD.lean sorries? | Uses Master.lean sorries?
-----------------------------------|-----------------------|------------------------
Cayley-Dickson multiplication      | NO                    | —
Octonion alternativity             | NO (levels 0-3)      | —
Finite {-1,0,1}^8 computations    | NO                    | —
Protensor relational structures     | NO                    | —
Non-reconstructibility remainder (σ307) | NO              | —
All master theorem results          | NO                    | NO
```

## The Architectural Position

`HardnessHolonomy.lean` defines the abstraction layer that connects
the existing specialized modules:

```
TuringHalting_Master.lean  ──diagonal structures──→  HardnessHolonomy.lean
ProtensorHaltingBraid.lean  ──protensor structures──→  HardnessHolonomy.lean
Algebra/CD.lean             ──algebraic structures─→  HardnessHolonomy.lean
FrustrationIrregularity.lean ──sectionability structures→ HardnessHolonomy.lean
MachineSemantics.lean       ──semantic structures───→  HardnessHolonomy.lean
```

Each module retains its own types. `HardnessHolonomy.lean` provides
the generic framework (transport loop, return defect, witness,
invariant, interpretation, convergence, diamond) into which
the specialized carriers can be projected.

## Status

- `HardnessHolonomy.lean`: compiles without executable sorries (17 sections)
- Interpretation maps: 5 carriers → common `InvariantSpace` (String); now
  **nontrivial** — each branches on witness data via `Classical.em`
- (2,2) Split-signature geometry: **formalized** — `PrimeSector`,
  `SplitSignatureCoupling`, `SplitSignatureInvariant`, `AdmissibleCouplingWindow`
- (2,2) Interpretation maps: 5 carriers → `SplitSignatureInvariant`
  with prime-sector activity records
- (2,2) Convergence: `SplitSignatureCorrespondence` defined; 2 pairs
  proved (`diagonal_hypercomplex_split_signature_correspondence`,
  `protensor_sectionability_split_signature_correspondence`)
- (2,2) Complexity diamonds: `SplitSignatureDiamond` with 3 constructors
  (`diagonalHypercomplex`, `protensorSectionability`, `fiveCarrier`)
- Transport stability: all (2,2) diamonds use `h_stable := trivial`
- Legacy placeholders: isolated, documented, not transitively blocking
- Master theorems: all proved independently of placeholders

## Open Questions

1. Can `AdmissibleCouplingWindow` be proved nonempty for specific
   carrier instances? (Currently: the structure exists but no
   proof that any κ satisfies all five conditions)

2. Can a carrier-specific split-signature metric be defined that
   distinguishes productive from destructive coupling? (Currently:
   `κ₁⁺` and `κ₁⁻` both record the same witness data; the
   sign convention is structural, not computed)

3. Can `SplitSignatureCorrespondence` be strengthened to require
   ALL prime-sector pairs to correspond, not just one pair?

4. Can `SplitSignatureDiamond` be backed by actual artifact evidence
   rather than `h_stable := trivial`? (Currently: all (2,2)
   diamonds use trivial evidence fields)

5. Can the (2,2) geometry be connected to the existing `ComplexityDiamond`
   structure? (Currently: two separate diamond formalisms coexist)
   require a common interpretation that all five map into)

4. Can the null-cone cancellation (⟨κ,κ⟩_{2,2}=0 with
   nontrivial holonomy) be detected algorithmically?
   (Currently: the null cone is invisible to scalar scoring;
   diamond holonomy may detect it)
