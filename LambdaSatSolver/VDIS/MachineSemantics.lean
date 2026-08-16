import Mathlib
import LambdaSatSolver.VDIS.OmnifluidManifold

/-!
# Machine Semantics Kernel — Canonical Definitions

## Claim Discipline

  This file provides the single canonical definition of operational machine
  semantics for the VDIS layer. It does NOT claim to solve classical
  Turing Halting.

  Core slogans:
  *Same name is not same semantics.*
  *One semantic kernel, many manifold representations.*
  *Representation transport must be explicit.*

## Contents

  `MachineSemantics` — state transition system with halting predicate
  `Reaches` — finite execution trace
  `ActuallyHalts` — existential trace predicate
  `SemanticRepresentation` — encode program/input into manifold state
  `RepresentationPreservesHalting` — optional preservation property
  `RepresentationReflectsHalting` — optional reflection property
  `VerificationVerdict` — three-outcome verifier result
  `SemanticVerifier` — independent verifier on manifold states
  `HaltVerifierSound` — verifier soundness condition

## Import chain

  OmnifluidManifold.lean → HaltSectionability, MΩ, ExtVer, HolonomySystem
-/

open Real

/-!
## §A — Operational Machine Semantics

A minimal operational semantics: a state transition system with a
terminal predicate. Intentionally abstract — not a specific model.

ActuallyHalts is an existential trace predicate, not a global decider.
-/

/-- A minimal machine semantics.

Provides the computational ground truth for halting.
Intentionally abstract — instantiation for specific computation families
(Turing machines, SAT solvers, lambda calculi) is left open.
-/
structure MachineSemantics where
  /-- Raw machine states. -/
  State : Type u
  /-- The halting predicate: does the machine halt? -/
  halts : State → Prop
  /-- Decidable halting for computation. -/
  halts_dec : ∀ s, Decidable (halts s)
  /-- Step relation: one computation step. -/
  step : State → State → Prop
  /-- Step is functional: each state has at most one successor. -/
  step_functional : ∀ s₁ s₂ s₃, step s₁ s₂ → step s₁ s₃ → s₂ = s₃

/-- Reachability via finite execution trace.

`Reaches M c c'` means state c' is reachable from c via zero or more steps
of M. This is the operational semantics trace, not a halting predicate. -/
inductive Reaches (M : MachineSemantics) : M.State → M.State → Prop
  | refl (c) : Reaches M c c
  | next {c c' c''} (hstep : M.step c = some c') (hrest : Reaches M c' c'') :
      Reaches M c c''

/-- ActuallyHalts: a program/input pair halts iff there exists a
terminal reachable state from the initial configuration.

This is an existential trace predicate, not a decidable predicate.
Not a global section. A local trace conclusion.
-/
def ActuallyHalts (M : MachineSemantics) (c : M.State) : Prop :=
  ∃ c', Reaches M c c' ∧ M.halts c'

/-!
## §B — Representation Bridge Across Manifolds

A program/input pair may appear differently in different computational
manifolds. This structure encodes that mapping without claiming
completeness or faithfulness.

Preservation and reflection are kept as separate optional properties.
-/

/-- A semantic representation bridges a machine semantics to a
computation manifold.

`encode p i` maps a program/input pair into a manifold state.
No claim of completeness or faithfulness is made by default.
-/
structure SemanticRepresentation
    (M : MachineSemantics) (A : MΩ) where
  /-- Encode a program/input pair into a manifold state. -/
  encode : M.State → A.State
  /-- The encoding is decidable. -/
  encode_dec : ∀ s, Decidable (encode s)

/-- Preservation: if the machine halts at c, the manifold section
may still claim halting (not guaranteed). -/
def RepresentationPreservesHalting
    (M : MachineSemantics) (A : MΩ) (R : SemanticRepresentation M A) : Prop :=
  ∀ c, M.halts c → (∃ c', Reaches M c c' ∧ M.halts c')

/-- Reflection: if the manifold section claims halting, the machine
actually halts (not guaranteed without this premise). -/
def RepresentationReflectsHalting
    (M : MachineSemantics) (A : MΩ) (R : SemanticRepresentation M A) : Prop :=
  ∀ c, M.halts c → M.halts (R.encode c)

/-!
## §C — Verifier Soundness

An independent verifier checks manifold states. Soundness means
verifier agreement with machine halting is not accidental.

We do NOT assume human recognition is verification.
We do NOT assume timeout implies non-halting.
We do NOT assume search exhaustion implies non-halting.
-/

/-- Verification verdicts: three possible outcomes.

  * `verifies_halt` — verifier confirms halting
  * `verifies_nonhalt` — verifier confirms non-halting
  * `inconclusive` — verifier cannot decide

`inconclusive` is NOT `non-halting`. It is absence of evidence.
-/
inductive VerificationVerdict
  | verifies_halt
  | verifies_nonhalt
  | inconclusive
  deriving DecidableEq, Repr

/-- A semantic verifier operates on manifold states.

Given a machine semantics and a semantic representation, the verifier
checks whether the machine actually halts at a given program state.
-/
structure SemanticVerifier
    (M : MachineSemantics) (A : MΩ) (R : SemanticRepresentation M A) where
  /-- Verify a manifold state and return a verdict. -/
  verify : A.State → VerificationVerdict
  /-- Verification is decidable. -/
  verify_dec : ∀ s, Decidable (verify s)

/-- Halt verifier soundness: if the verifier says "verifies_halt" at
R.encode c, then M actually halts at c.

This is a conditional proposition: the soundness bridge requires
the verifier to be truthful. It does not prove the verifier is
truthful — that is an additional premise.

Note: we do NOT define non-halting soundness. Non-halting claims
(verifies_nonhalt, timeout, search exhaustion, human recognition)
are not treated as equivalent to non-halting without a genuine
certificate semantics.
-/
def HaltVerifierSound
    (M : MachineSemantics) (A : MΩ) (R : SemanticRepresentation M A)
    (V : SemanticVerifier M A R) : Prop :=
  ∀ c, V.verify (R.encode c) = .verifies_halt → M.halts c
