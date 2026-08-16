# Machine Semantic Bridge

## Claim Discipline

  This document defines the soundness bridge from promoted sectionability
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

## What This Document Contains

1. Why promotion is not yet semantic truth
2. Operational machine semantics
3. ActuallyHalts as existential trace predicate
4. Representation across manifolds
5. Preservation versus reflection
6. Semantic verifier and verifier soundness
7. Sectionability statuses that carry no direct semantic verdict
8. Conditional semantic soundness theorem
9. What is proved
10. What remains open

## 1. Why Promotion Is Not Yet Semantic Truth

A fully promoted section (`FullyPromotedGlobalHaltSection`) bundles:
  - gluing compatibility (no shift where locally_decidable)
  - stability (no transport irregularity)
  - external verification (independent halting check)
  - adversarial separation (proposer ≠ verifier)
  - artifact evidence (concrete backing)

But none of these fields, individually or jointly, prove that the
promoted section's halting claims match actual machine behavior.

The semantic bridge `promoted_halting_claim_is_semantically_sound`
adds the required condition: if the verifier is sound AND the section
agrees with the verifier, THEN the machine actually halts.

Without the soundness premise, the bridge does not hold.

## 2. Operational Machine Semantics

### MachineSemantics

```lean
structure MachineSemantics where
  State : Type u
  halts : State → Prop
  halts_dec : ∀ s, Decidable (halts s)
  step : State → State → Prop
  step_functional : ∀ s₁ s₂ s₃, step s₁ s₂ → step s₁ s₃ → s₂ = s₃
```

A state transition system with a terminal predicate. Intentionally
abstract — not a specific model (Turing machines, lambda calculus,
SAT solvers, etc.).

### Reaches

```lean
inductive Reaches (M : MachineSemantics) : M.State → M.State → Prop
  | refl (c) : Reaches M c c
  | next {c c' c''} (hstep : M.step c = some c') (hrest : Reaches M c' c'') :
      Reaches M c c''
```

Finite execution trace. `Reaches M c c'` means c' is reachable from c
via zero or more steps. This is the operational trace, not a halting
predicate.

### ActuallyHalts

```lean
def ActuallyHalts (M : MachineSemantics) (c : M.State) : Prop :=
  ∃ c', Reaches M c c' ∧ M.halts c'
```

An existential trace predicate. Not decidable. Not a global section.
A local trace conclusion: there exists some terminal state reachable
from c.

## 3. ActuallyHalts as Existential Trace Predicate

ActuallyHalts is defined as:

```
ActuallyHalts M c := ∃ c', Reaches M c c' ∧ M.halts c'
```

This is NOT:
  - A Boolean predicate over all states
  - A global halting section
  - A decidable decision procedure
  - A claim that halting is always detectable

This IS:
  - A trace-based existential property
  - A local conclusion (one trace, one state)
  - A semantic ground truth that other layers reference

The existential quantifier means: we do not claim to decide halting.
We only claim that IF a terminal reachable state exists, then halting
is witnessed by that trace.

## 4. Representation Across Manifolds

### SemanticRepresentation

```lean
structure SemanticRepresentation (M : MachineSemantics) (A : MΩ) where
  encode : M.State → A.State
  encode_dec : ∀ s, Decidable (encode s)
```

Maps machine states into manifold states. No claim of completeness
or faithfulness.

### Preservation vs Reflection

```lean
def RepresentationPreservesHalting ... :=
  ∀ c, M.halts c → (∃ c', Reaches M c c' ∧ M.halts c')

def RepresentationReflectsHalting ... :=
  ∀ c, M.halts c → M.halts (R.encode c)
```

Preservation says: if the machine halts, the manifold may still
represent it (not guaranteed — the manifold might lose the trace).

Reflection says: if the machine halts, the manifold also halts
(not guaranteed — the manifold might not detect the trace).

Neither is assumed by default. Both are separate optional properties.

## 5. Semantic Verifier

### VerificationVerdict

```lean
inductive VerificationVerdict
  | verifies_halt
  | verifies_nonhalt
  | inconclusive
```

Three outcomes. `inconclusive` is NOT `non-halting`. It is absence
of evidence. Non-halting requires a genuine certificate (separate
premise), not absence of a halt verdict.

### SemanticVerifier

```lean
structure SemanticVerifier (M : MachineSemantics) (A : MΩ) (R : SemanticRepresentation M A) where
  verify : A.State → VerificationVerdict
  verify_dec : ∀ s, Decidable (verify s)
```

Checks manifold states. Independent of the section candidate.

### HaltVerifierSound

```lean
def HaltVerifierSound (M : MachineSemantics) (A : MΩ) (R : SemanticRepresentation M A)
    (V : SemanticVerifier M A R) : Prop :=
  ∀ c, V.verify (R.encode c) = .verifies_halt → M.halts c
```

Soundness: verifier confirmation implies machine halting.
Not assumed. Not proved. An explicit premise in the soundness bridge.

## 6. Sectionability Statuses That Carry No Direct Semantic Verdict

### ClaimsHalting

```lean
def ClaimsHalting : HaltSectionability → Prop
  | .total_decidable => True
  | .semi_decidable => True
  | _ => False
```

Only `total_decidable` and `semi_decidable` carry direct halting
claims. The rest are regime classifications:
  - `co_semi_decidable`: non-halting in restricted cases (not a general claim)
  - `locally_decidable`: chart-level coherence (not global correctness)
  - `externally_verifiable`: verification AVAILABLE (not verification returned)
  - `holonomy_obstructed`: local sections fail to glue (not non-halting)
  - `observer_absorbed`: human recognition mistaken for verification (not halting)
  - `unknown`: carries no claim

### ClaimsNonhalting

```lean
def ClaimsNonhalting : HaltSectionability → Prop
  | .co_semi_decidable => True
  | .externally_verifiable => True
  | _ => False
```

Only `co_semi_decidable` and `externally_verifiable` carry non-halting
claims under restricted conditions.

## 7. Conditional Semantic Soundness Theorem

### PromotedSemanticInterpretation

```lean
structure PromotedSemanticInterpretation (...) where
  verifierSound : HaltVerifierSound M A R V
  sectionVerdictAgreement :
    ∀ x, ClaimsHalting (G.regime x) → V.verify (R.encode x) = .verifies_halt
  externalVerification : ∀ x, ExternalVerification.verified x
  adversarialSeparation : ∀ x, AdversarialSeparation.independentlyChecked x
  artifactEvidence : ∀ x, ArtifactEvidence.artifactExists x
```

Links a fully promoted section to machine semantics with all premises
explicit.

### promoted_halting_claim_is_semantically_sound

```lean
theorem promoted_halting_claim_is_semantically_sound (...) :
    M.halts x := by
  have h_agree : V.verify (R.encode x) = .verifies_halt :=
    PSI.sectionVerdictAgreement x hClaim
  have h_sound : HaltVerifierSound M A R V := PSI.verifierSound
  unfold HaltVerifierSound at h_sound
  exact h_sound x h_agree
```

The proof passes through:
  1. `sectionVerdictAgreement` — ClaimsHalting → verifier confirms halt
  2. `HaltVerifierSound` — verifier confirms halt → machine halts
  3. Therefore: machine halts

This theorem does NOT claim:
  - Every promoted section is complete
  - Every halting computation is detected
  - Every non-halting computation is certified
  - A universal total decider exists

It claims only: when the premises align, the conclusion follows.

## 8. What Is Proved

| # | Theorem | Premises | Conclusion |
|---|---------|----------|------------|
| A | `promoted_halting_claim_is_semantically_sound` | hClaim, hVerdict, PSI | M.halts x |
| B | `verifier_inconclusive_yields_no_halting_conclusion` | hVerdict: inconclusive | inconclusive ≠ verifies_halt |
| C | `obstruction_status_yields_no_direct_halting_conclusion` | h: regime = holonomy_obstructed | ¬ ClaimsHalting (regime) |
| D | `observer_absorbed_yields_no_halting_claim` | h_obs: regime = observer_absorbed | ¬ ClaimsHalting (regime) |

### UNCONDITIONAL THEOREMS

  1. `promoted_halting_claim_is_semantically_sound` — if the
     promoted section claims halting, the verifier confirms halt,
     and the verifier is sound, then the machine actually halts.

  2. `verifier_inconclusive_yields_no_halting_conclusion` — if the
     verifier returns inconclusive, it does not verify halt.
     Inconclusive is distinct from verifies_halt.

  3. `obstruction_status_yields_no_direct_halting_conclusion` — if
     the regime is holonomy_obstructed, it does not claim halting.

  4. `observer_absorbed_yields_no_halting_claim` — if the regime
     is observer_absorbed, it does not claim halting.

### STRUCTURAL DEFINITIONS

  `MachineSemantics`, `Reaches`, `ActuallyHalts`,
  `SemanticRepresentation`, `VerificationVerdict`,
  `SemanticVerifier`, `HaltVerifierSound`,
  `ClaimsHalting`, `ClaimsNonhalting`,
  `PromotedSemanticInterpretation` — all defined.

### NOT PROVED

  - Completeness: every halting computation is detected by the promoted section
  - Universal decidability: a total_decidable section always exists
  - Classical undecidability: the full MΩ admits no total computable section

## 9. What Remains Open

### Formal open questions

1. **Soundness bridge calibration**: When does `HaltVerifierSound` hold
   for real verifiers? This requires a machine semantics instantiation.

2. **Adversarial separation strength**: Does `actors_distinct` (type
   inequality) imply genuine computational independence? A stronger
   model would require different algorithms, different data, or
   non-computable verification.

### Empirical open questions

3. **Promotion gate validation**: Do fully promoted sections (with all
   5 evidence premises) correspond to actual halting behavior?

4. **Semantic correspondence**: Does `ClaimsHalting` correctly classify
   machine-halting states across different computational manifolds?

5. **Soundness of verification**: Are real-world verifiers (human,
   tool-based, adversarial) sound about machine halting?

## 10. Claim Tiers

| Tier | Objects |
|------|---------|
| UNCONDITIONAL THEOREM | `promoted_halting_claim_is_semantically_sound`, `verifier_inconclusive_yields_no_halting_conclusion`, `obstruction_status_yields_no_direct_halting_conclusion`, `observer_absorbed_yields_no_halting_claim` |
| DEFINED | `MachineSemantics`, `Reaches`, `ActuallyHalts`, `SemanticRepresentation`, `VerificationVerdict`, `SemanticVerifier`, `HaltVerifierSound`, `ClaimsHalting`, `ClaimsNonhalting`, `PromotedSemanticInterpretation` |
| ASSUMED PREMISE | `HaltVerifierSound` (truthfulness of verifier about machine behavior), `sectionVerdictAgreement` (section matches verifier) |
| NOT PROVED | completeness, universal decidability, non-halting certification, classical undecidability |
| MARKER | `classicalHaltingInterfaceMarker : Unit` (non-semantic interface placeholder) |
| FRONTIER | adversarial separation strength, empirical promotion gate validation, soundness bridge calibration |

## 11. Remaining Semantic Frontier

The architecture now has a complete chain:

```
intermanifold coherence
  → gluing / stability obstruction (proved)
  → evidence promotion (proved)
  → soundness bridge (conditional)
  → machine semantic correspondence (proved, conditional)
```

The next frontier is not another geometric layer.
It is empirical: does the soundness bridge hold for real machines,
real verifiers, and real computational manifolds?

## Required Sentences

  A promoted section is not semantically correct merely because it is coherent.
  The semantic bridge is conditional on an explicitly sound verifier.
  Obstruction is not non-halting.
  Inconclusive is not non-halting.
  Timeout is not non-halting.
  A local Boolean verdict is not the ontology of the intermanifold field.
  The same computation is represented by a relational profile across manifolds,
  not exhausted by one encoding.
  This layer does not construct a universal halting decider.
