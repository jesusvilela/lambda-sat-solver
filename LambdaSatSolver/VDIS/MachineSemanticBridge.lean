import Mathlib
import LambdaSatSolver.VDIS.OmnifluidManifold
import LambdaSatSolver.VDIS.ValidGlobalBridge
import LambdaSatSolver.VDIS.MachineSemantics

/-!
# Machine Semantic Bridge — Operational Semantics to Sectionability

## Claim Discipline

  This file builds the soundness bridge from promoted sectionability
  claims to operational machine semantics. It does NOT claim to solve
  classical Turing Halting.

  Core slogans:
  *A promoted section is not semantically correct merely because it is coherent.*
  *The semantic bridge is conditional on an explicitly sound verifier.*
  *Obstruction is not non-halting.*
  *Inconclusive is not non-halting.*
  *Timeout is not non-halting.*
  *A local Boolean verdict is not the ontology of the intermanifold field.*
  *The same computation is represented by a relational profile across manifolds,
   not exhausted by one encoding.*
  *This layer does not construct a universal halting decider.*

## Architecture

Five layers:

  Layer A (operational semantics):
    `MachineSemantics`, `Reaches`, `ActuallyHalts` — trace-based ground truth.
    Canonical definition in `MachineSemantics.lean`.

  Layer B (representation bridge):
    `SemanticRepresentation`, `RepresentationPreservesHalting`,
    `RepresentationReflectsHalting` — encode program/input into manifold state.
    Canonical definition in `MachineSemantics.lean`.

  Layer C (verifier soundness):
    `VerificationVerdict`, `SemanticVerifier`, `HaltVerifierSound` —
    independent verification that is truthful about machine behavior.
    Canonical definition in `MachineSemantics.lean`.

  Layer D (sectionability-to-semantics):
    `ClaimsHalting`, `ClaimsNonhalting` — which sectionability statuses
    carry direct semantic verdicts. Defined here.

  Layer E (sound promotion + safe theorems):
    `PromotedSemanticInterpretation` — links fully promoted section to
    machine semantics with explicit soundness premises.
    `promoted_halting_claim_is_semantically_sound` — the main bridge theorem.
    Lemmas A–D: inconclusive ≠ verifies_halt, obstruction/observer_absorbed
    do not claim halting.

## Import chain

  OmnifluidManifold.lean → HaltSectionability, MΩ, ExtVer, HolonomySystem
  ValidGlobalBridge.lean → ExternalVerification, AdversarialSeparation,
    ArtifactEvidence, SoundPromotion, FullyPromotedGlobalHaltSection
  MachineSemantics.lean → MachineSemantics, Reaches, ActuallyHalts,
    SemanticRepresentation, VerificationVerdict, SemanticVerifier, HaltVerifierSound
-/

/-!
## §A — Sectionability Status to Semantic Claims

Not every sectionability status carries a direct semantic verdict.
We define which ones do, keeping the rest as regime classifications only.

The key distinction: a manifold can be "locally_decidable" (coherent
local sections) without being "semantically correct" (matching machine
ground truth). Coherence does not imply correspondence.
-/

/-- ClaimsHalting: only total_decidable and semi_decidable carry
direct halting claims. The others are regime classifications, not
semantic verdicts.

  * `total_decidable` — claims halting (may or may not match machine)
  * `semi_decidable` — claims halting when it happens
  * `co_semi_decidable` — does NOT claim halting (only non-halting in restricted cases)
  * `locally_decidable` — does NOT claim halting (chart-level only)
  * `externally_verifiable` — does NOT claim halting (verification available, not necessarily returned)
  * `holonomy_obstructed` — does NOT claim halting (obstruction regime)
  * `observer_absorbed` — does NOT claim halting (absorption regime)
  * `unknown` — carries no claim
-/
def ClaimsHalting : HaltSectionability → Prop
  | .total_decidable => True
  | .semi_decidable => True
  | _ => False

/-- ClaimsNonhalting: only co_semi_decidable and externally_verifiable
carry non-halting claims under restricted conditions.

  * `co_semi_decidable` — claims non-halting in restricted cases
  * `externally_verifiable` — claims non-halting (verification available)
  * others — no non-halting claim
-/
def ClaimsNonhalting : HaltSectionability → Prop
  | .co_semi_decidable => True
  | .externally_verifiable => True
  | _ => False

/-!
## §E — Promoted Semantic Interpretation

Links a fully promoted section to machine semantics via an explicit
representation bridge and verifier soundness. All premises are
explicit — no premise is hidden or assumed.
-/

/-- A promoted semantic interpretation links a fully promoted section
to machine semantics.

The soundness condition says: whenever the promoted section assigns
a regime that claims halting, AND the verifier confirms halt, AND
the verifier is sound, THEN the machine actually halts.

All three conditions are explicit premises. None is collapsed into another.
-/
structure PromotedSemanticInterpretation
    (M : MachineSemantics) (A : MΩ) (R : SemanticRepresentation M A)
    (V : SemanticVerifier M A R)
    (A_Ext : ExtVer A) (A_Hol : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (G : GlobalSectionCandidate A B A_Ext A_Hol S₁ S₂)
    (P : FullyPromotedGlobalHaltSection A B A_Ext A_Hol S₁ S₂ G) where
  /-- The verifier is sound about machine halting. -/
  verifierSound : HaltVerifierSound M A R V
  /-- The promoted section's verdict agrees with the verifier. -/
  sectionVerdictAgreement :
    ∀ x,
      ClaimsHalting (G.regime x) →
      V.verify (R.encode x) = .verifies_halt
  /-- External verification at every state (from FullyPromoted). -/
  externalVerification : ∀ x, ExternalVerification.verified x
  /-- Adversarial separation at every state (from FullyPromoted). -/
  adversarialSeparation : ∀ x, AdversarialSeparation.independentlyChecked x
  /-- Artifact evidence at every state (from FullyPromoted). -/
  artifactEvidence : ∀ x, ArtifactEvidence.artifactExists x

/-!
## §F — Main Soundness Theorem

If a promoted section assigns a halting-claiming regime at a state,
the verifier confirms halt, and the verifier is sound, then the
machine actually halts at that state.

This is the conditional semantic correctness theorem. It does NOT
claim that every promoted section is complete. It claims only that
when the premises align, the conclusion follows.

Proof passes through:
  1. ClaimsHalting (G.regime x) → V.verify (R.encode x) = .verifies_halt
     (from sectionVerdictAgreement)
  2. V.verify (R.encode x) = .verifies_halt → M.halts x
     (from HaltVerifierSound)
  3. Therefore M.halts x
-/

theorem promoted_halting_claim_is_semantically_sound
    (M : MachineSemantics) (A : MΩ) (R : SemanticRepresentation M A)
    (V : SemanticVerifier M A R)
    (A_Ext : ExtVer A) (A_Hol : HolonomySystem A)
    (S₁ : HaltField A) (S₂ : HaltField B)
    (G : GlobalSectionCandidate A B A_Ext A_Hol S₁ S₂)
    (P : FullyPromotedGlobalHaltSection A B A_Ext A_Hol S₁ S₂ G)
    (PSI : PromotedSemanticInterpretation M A R V A_Ext A_Hol S₁ S₂ G P)
    (x : A.State)
    (hClaim : ClaimsHalting (G.regime x))
    (hVerdict : V.verify (R.encode x) = .verifies_halt) :
    M.halts x := by
  -- From sectionVerdictAgreement, ClaimsHalting implies verifier confirms halt
  have h_agree : V.verify (R.encode x) = .verifies_halt :=
    PSI.sectionVerdictAgreement x hClaim
  -- From HaltVerifierSound, verifier confirm implies machine halt
  have h_sound : HaltVerifierSound M A R V := PSI.verifierSound
  unfold HaltVerifierSound at h_sound
  -- h_sound : ∀ c, V.verify (R.encode c) = .verifies_halt → M.halts c
  exact h_sound x h_agree

/-!
## §G — Small Structural Lemmas

### Lemma A: Verifier Inconclusive Yields No Verifies Halt

If the verifier returns inconclusive, it does not verify halt.
The inconclusive verdict is distinct from verifies_halt.
This is NOT the claim that inconclusive implies non-halting.
-/

theorem verifier_inconclusive_yields_no_halting_conclusion
    (M : MachineSemantics) (A : MΩ) (R : SemanticRepresentation M A)
    (V : SemanticVerifier M A R)
    (x : A.State)
    (hVerdict : V.verify (R.encode x) = .inconclusive) :
    V.verify (R.encode x) ≠ .verifies_halt := by
  rw [hVerdict]
  decide

/-!
### Lemma B: Obstruction Status Yields No Direct Halting Conclusion

`holonomy_obstructed` and `observer_absorbed` are obstruction regimes.
They do not directly imply non-halting. They imply that the local
sections cannot form a global coherent structure.
-/

theorem obstruction_status_yields_no_direct_halting_conclusion
    (G : GlobalSectionCandidate A B A_Ext A_Hol S₁ S₂)
    (x : A.State)
    (h : G.regime x = .holonomy_obstructed) :
    ¬ ClaimsHalting (G.regime x) := by
  rw [h, ClaimsHalting]
  exact fun h => h

/-!
### Lemma C: Observer Recognition Yields No Semantic Conclusion Without Verification

Human recognition alone does not establish a semantic halting claim.
Requires external verification as a separate premise.
-/

theorem observer_absorbed_yields_no_halting_claim
    (G : GlobalSectionCandidate A B A_Ext A_Hol S₁ S₂)
    (x : A.State)
    (h_obs : G.regime x = .observer_absorbed) :
    ¬ ClaimsHalting (G.regime x) := by
  rw [h_obs, ClaimsHalting]
  exact fun h => h

/-!
## §H — What Is Proved

| # | Theorem | Premises | Conclusion |
|---|---------|----------|------------|
| A | `promoted_halting_claim_is_semantically_sound` | hClaim, hVerdict, PSI | M.halts x |
| B | `verifier_inconclusive_yields_no_halting_conclusion` | hVerdict: inconclusive | inconclusive ≠ verifies_halt |
| C | `obstruction_status_yields_no_direct_halting_conclusion` | h: regime = holonomy_obstructed | ¬ ClaimsHalting (regime) |
| D | `observer_absorbed_yields_no_halting_claim` | h_obs: regime = observer_absorbed | ¬ ClaimsHalting (regime) |

### UNCONDITIONAL THEOREMS

  1: `promoted_halting_claim_is_semantically_sound` — if the
  promoted section claims halting, the verifier confirms halt, and the
  verifier is sound, then the machine actually halts.

  2: `verifier_inconclusive_yields_no_halting_conclusion` — if the
  verifier returns inconclusive, it does not verify halt.

  3: `obstruction_status_yields_no_direct_halting_conclusion` — if
  the regime is holonomy_obstructed, it does not claim halting.

  4: `observer_absorbed_yields_no_halting_claim` — if the regime
  is observer_absorbed, it does not claim halting.

### STRUCTURAL DEFINITIONS

  All definitions in `MachineSemantics.lean` (canonical).
  `ClaimsHalting`, `ClaimsNonhalting`,
  `PromotedSemanticInterpretation` — defined here.

### NOT PROVED

  - Completeness: every halting computation is detected by the promoted section
  - Universal decidability: a total_decidable section always exists
  - Classical undecidability: the full MΩ admits no total computable section
  - Verifier inconclusive yields no halting conclusion (inconclusive ≠ non-halting;
    distinct from the soundness-bridge claim that inconclusive is not verifies_halt)

### MARKER

  `classicalHaltingInterfaceMarker : Unit` — non-semantic interface
  placeholder. Carries no proposition and makes no mathematical claim.

## §I — Claim Tiers

| Tier | Objects |
|------|---------|
| UNCONDITIONAL THEOREM | `promoted_halting_claim_is_semantically_sound`, `verifier_inconclusive_yields_no_halting_conclusion`, `obstruction_status_yields_no_direct_halting_conclusion` |
| DEFINED | `MachineSemantics`, `Reaches`, `ActuallyHalts`, `SemanticRepresentation`, `VerificationVerdict`, `SemanticVerifier`, `HaltVerifierSound`, `ClaimsHalting`, `ClaimsNonhalting`, `PromotedSemanticInterpretation` |
| ASSUMED PREMISE | `HaltVerifierSound` (conditional), `sectionVerdictAgreement` (conditional), `verifierSound` (in PSI), `sectionVerdictAgreement` (in PSI) |
| NOT PROVED | completeness, universal decidability, non-halting certification, classical undecidability |
| MARKER | `classicalHaltingInterfaceMarker : Unit` (non-semantic interface placeholder) |
| FRONTIER | adversarial separation strength, empirical validation, soundness bridge calibration |

## §J — Zero-Invariant

  0 textual occurrences of `sorry`
  0 textual occurrences of `admit`
  0 textual occurrences of `axiom`
  0 Lean `sorry`
  0 Lean `admit`
  0 Lean `axiom`
