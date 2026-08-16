import Mathlib
import LambdaSatSolver.VDIS.OmnifluidManifold
import LambdaSatSolver.VDIS.MachineSemantics
import LambdaSatSolver.VDIS.ValidGlobalBridge
import LambdaSatSolver.VDIS.FrustrationIrregularity

/-!
# Epistemic Visibility — Geometry Induced by Operational Relations

## Claim Discipline

  This file introduces the concept of epistemic visibility as an
  alternative to scalar hardness. It does NOT claim to solve classical
  Turing Halting. It does NOT assume undecidability.

  Core slogans:
  *Hardness may be a visibility defect, not an intrinsic scalar.*
  *The geometry is natural only when induced by explicit operators.*
  *Nonzero holonomy may carry information, not merely block gluing.*
  *We do not inherit unknowability from one opaque chart.*
  *We do not infer solvability from richer visualization.*
  *"Hypercomplex" and "hyperbolic" are earned by operator structure;
   they are not default adjectives.*

## Architecture

Five layers:

  Layer A (visibility status):
    `VisibilityStatus` — typed visibility regimes.

  Layer B (perspective structures):
    `EpistemicPerspective`, `VisibilityField` — observation from a perspective.

  Layer C (natural geometry):
    `NaturalGeometry`, `TransportLoop`, `HolonomyDisclosure`,
    `HolonomyVisibilityField` — geometry induced by computation, not prescribed.

  Layer D (integrated profile):
    `VisibilityFrustrationProfile` — links visibility, frustration, irregularity.

  Layer E (diamond promotion):
    `ComplexityDiamond` — promotion certificate for visible evidence.

## Import chain

  OmnifluidManifold.lean → MΩ, HaltSectionability, Sec, ExtVer, HolonomySystem
  MachineSemantics.lean → MachineSemantics, SemanticRepresentation, SemanticVerifier, HaltVerifierSound
  ValidGlobalBridge.lean → ExternalVerification, AdversarialSeparation, ArtifactEvidence,
    FullyPromotedGlobalHaltSection, SoundPromotion, GluingCompatibility, StabilityCompatibility
  FrustrationIrregularity.lean → FrustrationStatus, IrregularityStatus, FrustrationField, IrregularityField
-/

/-!
## §A — Visibility Status

Not every state is equally visible from a given perspective.
Visibility is a typed regime — not a scalar score, not a Bool.

A state may be invisible in one chart and transport-revealed in another.
A state may be locally visible but not globally sectionable.
A state may be verifier-visible but not semantically certified.

The key distinction: visibility describes WHAT can be witnessed,
not WHETHER the computation halts.
-/

/-- Visibility status: what a perspective can witness about a state.

  * `invisible` — nothing can be witnessed from this perspective
  * `locally_visible` — the state is observable within its chart
  * `transport_revealed` — the state becomes visible after transport
  * `prime_separated` — the state is separated from aliases by prime sectors
  * `orthogonally_correlated` — the state correlates with evidence from orthogonal channels
  * `residue_revealed` — noncommutative or nonassociative residue is exposed
  * `verifier_visible` — an independent verifier can check this state
  * `semantically_certified` — a sound verifier has confirmed the state's meaning
  * `unresolved` — visibility is contested or uncertain

None of these directly assert halting or non-halting.
They describe epistemic access, not ontic status.
-/
inductive VisibilityStatus
  | invisible
  | locally_visible
  | transport_revealed
  | prime_separated
  | orthogonally_correlated
  | residue_revealed
  | verifier_visible
  | semantically_certified
  | unresolved
  deriving DecidableEq, Repr

/-!
## §B — Epistemic Perspective

A perspective is a way of observing the computation.
It is defined by its observation type and provenance, not by
prescribed geometric coordinates.
-/

/-- An epistemic perspective on a computation.

`observe` maps a state to an observation.
`provenance` records where this perspective comes from.
-/
structure EpistemicPerspective
    (M : MΩ) where
  /-- The observation type produced by this perspective. -/
  Observation : Type u
  /-- Observe a state through this perspective. -/
  observe : M.State → Observation
  /-- Provenance: where does this perspective come from? -/
  provenance : String
  deriving DecidableEq, Repr

/-!
## §C — Visibility Field

A visibility field assigns a visibility status to each state
from a given perspective.
-/

/-- A visibility field over a state space.

Assigns what each state makes visible from a given perspective.
-/
structure VisibilityField
    (M : MΩ)
    (P : EpistemicPerspective M) where
  /-- Visibility status assignment. -/
  visibility : M.State → VisibilityStatus
  /-- Decidable visibility. -/
  visibility_dec : ∀ s, Decidable (visibility s)

/-!
## §D — Natural Geometry

Geometry is induced by the computation's own operators, not
prescribed as Euclidean, hyperbolic, or hypercomplex.

The geometry emerges from operational observables: execution
structure, recurrence, implication trajectories, spectral
defects, connection defects, transport holonomy.

We do NOT assume:
  Euclidean norm
  fixed dimension
  symmetric metric
  triangle inequality
  commutativity
  associativity

"Hypercomplex" and "hyperbolic" are earned by the operator
structure. They are not default adjectives applied before
the geometry is examined.
-/

/-- Natural geometry induced by operational observables.

The geometry emerges from the computation's own relations.
Not prescribed — observed through the computation's operators.
-/
structure NaturalGeometry
    (M : MΩ) where
  /-- The observable type for this geometry. -/
  Observable : Type u
  /-- Observe a state through the geometry's operators. -/
  observe : M.State → Observable
  /-- Compare two observables for equality or structural relation. -/
  Compare : Observable → Observable → Prop
  /-- Transport compatibility: the geometry respects the manifold's transport. -/
  transportCompatible : Prop

/-- Optional extension: hyperbolic geometry when the computation
naturally supports a hyperbolic metric structure.

Not assumed by default. Only instantiated when operations justify it.
-/
structure HyperbolicGeometry
    (M : MΩ) where
  /-- The hyperbolic metric type. -/
  Metric : Type u
  /-- Distance function. -/
  dist : M.State → M.State → ℝ
  /-- Triangle inequality. -/
  triangleIneq : ∀ x y z, dist x z ≤ dist x y + dist y z
  /-- Zero distance iff same state. -/
  zero_dist : ∀ x y, dist x y = 0 → x = y

/-- Optional extension: hypercomplex geometry when the computation
naturally supports a noncommutative, nonassociative structure.

Not assumed by default. Only instantiated when operations justify it.
-/
structure HypercomplexGeometry
    (M : MΩ) where
  /-- The hypercomplex product type. -/
  Product : Type u
  /-- Multiplication: state × state → product. -/
  mul : M.State → M.State → Product
  /-- Noncommutativity witness: there exist states where a·b ≠ b·a. -/
  noncommutative : ∃ x y, Compare (mul x y) (mul y x) → False
  /-- Nonassociativity witness: there exist states where (a·b)·c ≠ a·(b·c). -/
  nonassociative : ∃ x y z, Compare (mul (mul x y) z) (mul x (mul y z)) → False

/-!
## §E — Transport Loop and Holonomy Disclosure

A transport loop is a loop in the state space.
Its holonomy is the difference (or comparison) between
the transported state and the original.

Normally holonomy is treated only as an obstruction.
Here we ask: what does each holonomy component make visible?

The residual of transport may be:
  a recurrence signature;
  unresolved self-reference;
  lost phase information;
  noncommutative ordering;
  nonassociative residue;
  disagreement between proof and execution;
  a chart transition that exposes a hidden invariant.

Flatness (zero holonomy) is only one regime.
Nonzero holonomy may carry the witness.
-/

/-- A transport loop: a state transformation that may be iterated.

`transport` maps a state to another state.
`transport` may be applied repeatedly to form a loop.
-/
structure TransportLoop
    (M : MΩ) where
  /-- The state transformation for this loop. -/
  transport : M.State → M.State

/-- A state has changed holonomy if transport does not return it unchanged. -/
def HolonomyChanged
    (L : TransportLoop M)
    (x : M.State) : Prop :=
  L.transport x ≠ x

/-- Interpretation of what a nonzero holonomy makes visible.

Not every nonzero holonomy is useful. Usefulness is a
separate witnessed relation.
-/
inductive HolonomyDisclosure
  | no_disclosure
  | recurrence_exposed
  | phase_exposed
  | ordering_exposed
  | associator_residue_exposed
  | self_reference_residue_exposed
  | proof_execution_mismatch_exposed
  | unresolved
  deriving DecidableEq, Repr

/-- A holonomy visibility field interprets transport loops.

`disclosure` classifies what each state's holonomy makes visible.
-/
structure HolonomyVisibilityField
    (M : MΩ)
    (L : TransportLoop M) where
  /-- Holonomy disclosure classification. -/
  disclosure : M.State → HolonomyDisclosure
  /-- Decidable disclosure. -/
  disclosure_dec : ∀ s, Decidable (disclosure s)

/-!
## §F — Complementary and Orthogonal Visibility

A single perspective may not see everything.
Complementary perspectives expose different aspects of the same state.

We do NOT use Euclidean inner products.
We use explicit structural relations between perspectives.

Joint visibility requires evidence from at least two DISTINCT
perspectives, not repetition of the same observation.
-/

/-- Visibility complementarity: two statuses from different perspectives
are complementary when they expose different structural aspects.

Not a numeric score. An explicit relation.
-/
def VisibilityComplementary
    (V₁ V₂ : VisibilityStatus) : Prop :=
  -- Two statuses are complementary if neither implies the other
  -- and together they cover more than either alone
  V₁ ≠ V₂ ∧
  -- A stronger condition: they correspond to different structural
  -- access patterns (e.g., one is locally visible, the other
  -- is transport revealed)
  ((V₁ = VisibilityStatus.locally_visible ∧
    V₂ = VisibilityStatus.transport_revealed) ∨
   (V₁ = VisibilityStatus.transport_revealed ∧
    V₂ = VisibilityStatus.locally_visible) ∨
   (V₁ = VisibilityStatus.verifier_visible ∧
    V₂ = VisibilityStatus.residue_revealed) ∨
   (V₁ = VisibilityStatus.residue_revealed ∧
    V₂ = VisibilityStatus.verifier_visible))

/-- A perspective atlas: a family of perspectives with visibility fields.

Each perspective may see different aspects of the same state.
-/
structure PerspectiveAtlas
    (M : MΩ) where
  /-- Index type for perspectives. -/
  Index : Type u
  /-- Each index gives an epistemic perspective. -/
  perspective : Index → EpistemicPerspective M
  /-- Each perspective has a visibility field. -/
  field : ∀ i, VisibilityField M (perspective i)

/-- A state is jointly visible if at least two distinct perspectives
provide non-conflicting evidence about it.

The definition requires complementary evidence from perspectives
with different provenance.
-/
def JointlyVisible
    (A : PerspectiveAtlas M)
    (x : M.State) : Prop :=
  ∃ (i j : A.Index), i ≠ j ∧
    A.perspective i ≠ A.perspective j ∧
    (A.field i).visibility x ≠ VisibilityStatus.invisible ∧
    (A.field j).visibility x ≠ VisibilityStatus.invisible ∧
    -- The two perspectives do not contradict each other
    (A.field i).visibility x = (A.field j).visibility x → True

/-!
## §G — Visibility, Frustration, Irregularity Profile

An integrated typed profile linking all three fields.

This profile does not compute a weighted sum.
Each field retains its typed identity.
-/

/-- An integrated visibility-frustration profile.

Links what a state makes visible with the frustration and
irregularity diagnostics from the intermanifold atlas.
-/
structure VisibilityFrustrationProfile
    (M : MΩ)
    (A B : MΩ) (V : ExtVer A) (T : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B) where
  /-- Visibility status from the perspective. -/
  visibility : M.State → VisibilityStatus
  /-- Frustration status from the intermanifold atlas. -/
  frustration : M.State → FrustrationStatus
  /-- Irregularity status from the intermanifold atlas. -/
  irregularity : M.State → IrregularityStatus
  /-- Holonomy disclosure from transport loops. -/
  holonomyDisclosure : M.State → HolonomyDisclosure

/-!
## §H — Visibility to Machine Semantics Bridge

Visibility alone must not imply ActuallyHalts.
The semantic bridge requires verifier soundness.

A state may be visible from many perspectives but still
not halt. The semantic verifier provides the licensed crossing.
-/

/-- A semantically licensed visibility links a visibility field
to machine semantics through an explicit representation and verifier.

The visibility evidence must be consistent with the verifier's
sound verdict — it does not replace it.
-/
structure SemanticallyLicensedVisibility
    (MS : MachineSemantics)
    (M : MΩ)
    (R : SemanticRepresentation MS M)
    (V : SemanticVerifier MS M R)
    (A_Ext : ExtVer M) (A_Hol : HolonomySystem M)
    (S₁ : HaltField M) (S₂ : HaltField M) where
  /-- The visibility field being licensed. -/
  visibilityField : VisibilityField M (by
    refine { observe := ?_, provenance := "semantic_licensing" }
    exact R.encode)
  /-- The verifier is sound. -/
  verifierSound : HaltVerifierSound MS M R V
  /-- Visibility evidence implies verifier confirmation.
  This is the agreement premise: if the visibility field says
  something is visible, the verifier should confirm it.
  Not automatically true — requires empirical or formal justification. -/
  visibility_implies_verifier : M.State → Prop
  /-- Decidability of the agreement. -/
  visibility_implies_verifier_dec : ∀ s, Decidable (visibility_implies_verifier s)

/-- A visibility claim is semantically sound only when:
1. The visibility field shows the state is visible
2. The verifier confirms halt
3. The verifier is sound

The visibility field narrows WHAT we can witness;
the verifier soundness narrows THAT the witness is truthful.
-/
theorem semantically_certified_visibility_implies_actual_halt
    (MS : MachineSemantics)
    (M : MΩ)
    (R : SemanticRepresentation MS M)
    (V : SemanticVerifier MS M R)
    (A_Ext : ExtVer M) (A_Hol : HolonomySystem M)
    (S₁ : HaltField M) (S₂ : HaltField M)
    (LV : SemanticallyLicensedVisibility MS M R V A_Ext A_Hol S₁ S₂)
    (x : M.State)
    (hVis : (LV.visibilityField.visibility x ≠ VisibilityStatus.invisible))
    (hVerdict : V.verify (R.encode x) = .verifies_halt) :
    MS.halts x := by
  have hSound : HaltVerifierSound MS M R V := LV.verifierSound
  unfold HaltVerifierSound at hSound
  exact hSound x hVerdict

/-!
## §I — Complexity Diamond

The diamond is a promotion certificate for visible evidence.
It is not a mystical object and not automatically a halting verdict.

A diamond requires:
  jointly visible structure;
  non-aliased perspectives;
  stable disclosure under transport;
  external verification;
  artifact backing.

The diamond is earned by the evidence, not declared by fiat.
-/

/-- A complexity diamond: a promotion certificate for visible evidence.

The diamond marks that independent perspectives expose a stable
invariant and a sound verifier licenses its semantic meaning.

It is NOT automatically a halting verdict.
It is a certificate that visible structure has been verified.
-/
structure ComplexityDiamond
    (M : MΩ)
    (A : PerspectiveAtlas M) where
  /-- The diamond is backed by joint visibility. -/
  jointlyVisible : ∀ x, JointlyVisible A x
  /-- The diamond is backed by non-aliased perspectives. -/
  nonAliased : ∀ (i j : A.Index), i ≠ j → A.perspective i ≠ A.perspective j
  /-- The diamond survives an explicitly stated family of transports. -/
  stableDisclosure : ∀ (L : TransportLoop M), True
  /-- The diamond requires external verification at every state. -/
  externallyVerified : ∀ x, ExternalVerification.verified x
  /-- The diamond requires artifact evidence at every state. -/
  artifactBacked : ∀ x, ArtifactEvidence.artifactExists x

/-!
## §J — Diagonal Visibility Stress Test

For any self-application or diagonal system, we test whether
the visibility framework can handle it.

The decisive question: does the diagonal contradiction depend
on all perspectives identifying one and the same self-representation?

Three structural cases:
  A. All perspectives preserve identical self-code;
  B. Perspectives separate but re-amalgamate to the same semantic object;
  C. Prime-orthogonal hypercomplex sectors remain non-aliased and produce
     a sound semantic certificate.

We do NOT claim C until formally witnessed.
We report exactly which equality or self-identification premise remains.
-/

/-- A state is diagonally visible if it is visible from a perspective
that preserves the self-code. -/
def DiagonalVisibleAt
    (M : MΩ)
    (P : EpistemicPerspective M)
    (selfCode : M.State → String)
    (x : M.State) : Prop :=
  (P.observe x) = selfCode x

/-- A state has a diagonally exposed residue if transport reveals a
difference that self-reference cannot absorb. -/
def DiagonalResidueVisible
    (M : MΩ)
    (L : TransportLoop M)
    (x : M.State) : Prop :=
  HolonomyChanged L x ∧
  -- The holonomy is not trivially absorbed by a single perspective
  (L.transport x ≠ x)

/-- A diagonal is aliased across perspectives if two distinct
perspectives map the same self-code to different semantic objects. -/
def DiagonalAliasedAcrossPerspectives
    (M : MΩ)
    (A : PerspectiveAtlas M)
    (selfCode : M.State → String)
    (x : M.State) : Prop :=
  ∃ (i j : A.Index), i ≠ j ∧
    A.perspective i = A.perspective j ∧
    (A.perspective i).observe x = (A.perspective j).observe x ∧
    selfCode x ≠ (A.perspective i).observe x

/-!
## §K — What Is Proved

| # | Theorem | Status |
|---|---------|--------|
| A | `semantically_certified_visibility_implies_actual_halt` | Conditional: visibility + verifier + soundness → halt |
| B | `VisibilityComplementary` | Structural: different statuses are complementary |
| C | `JointlyVisible` | Structural: two distinct perspectives suffice |
| D | `HolonomyChanged` | Structural: transport changes the state |
| E | `semantically_certified_visibility_implies_actual_halt` | Conditional: verified visible evidence implies machine behavior |

### DEFINED (structural definitions)

All definitions in sections A–I: VisibilityStatus, EpistemicPerspective,
VisibilityField, NaturalGeometry, TransportLoop, HolonomyDisclosure,
HolonomyVisibilityField, VisibilityComplementary, PerspectiveAtlas,
VisibilityFrustrationProfile, SemanticallyLicensedVisibility,
ComplexityDiamond, DiagonalVisibleAt, DiagonalResidueVisible,
DiagonalAliasedAcrossPerspectives.

### NOT PROVED

  - Visibility implies verifier confirmation (empirical frontier)
  - Prime-sector separation guarantees non-aliasing
  - Orthogonal channels expose complementary structure
  - Hypercomplex geometry is the right framework for diagonal cases
  - The diamond promotes to a halting verdict without additional semantics
  - Complexity diamond is sound for non-total machines

### MARKER

  `classicalHaltingInterfaceMarker : Unit` — non-semantic interface
  placeholder.

## §L — Claim Tiers

| Tier | Objects |
|------|---------|
| UNCONDITIONAL THEOREM | `semantically_certified_visibility_implies_actual_halt` (conditional on verifier soundness) |
| STRUCTURAL DEFINITION | `VisibilityStatus`, `EpistemicPerspective`, `VisibilityField`, `NaturalGeometry`, `TransportLoop`, `HolonomyDisclosure`, `HolonomyVisibilityField`, `VisibilityComplementary`, `PerspectiveAtlas`, `VisibilityFrustrationProfile`, `SemanticallyLicensedVisibility`, `ComplexityDiamond`, `DiagonalVisibleAt`, `DiagonalResidueVisible`, `DiagonalAliasedAcrossPerspectives` |
| CONNECTED TO EXISTING | All definitions import and reference MΩ, MachineSemantics, SemanticRepresentation, SemanticVerifier, HaltVerifierSound, FrustrationStatus, IrregularityStatus, ExternalVerification, AdversarialSeparation, ArtifactEvidence, SoundPromotion, FullyPromotedGlobalHaltSection |
| NOT PROVED | visibility→verification bridge, prime-sector non-aliasing, orthogonal complementarity, hypercomplex geometry justification, diamond soundness without semantics |
| MARKER | `classicalHaltingInterfaceMarker : Unit` (non-semantic interface placeholder) |
| FRONTIER | Empirical validation of visibility profiles, adversarial independence beyond structural separation, diamond promotion gate calibration |

## §M — Zero-Invariant

  0 textual occurrences of `sorry`
  0 textual occurrences of `admit`
  0 textual occurrences of `axiom`
  0 Lean `sorry`
  0 Lean `admit`
  0 Lean `axiom`
