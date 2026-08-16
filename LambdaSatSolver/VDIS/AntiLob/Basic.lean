import Mathlib

/-!
# Anti-Löb Research Harness

## Overview

The Anti-Löb harness implements disciplined null-generation and claim demotion
for the Manifold Research programme. Every candidate signal declares its null
family. The system automatically generates matched nulls, tracks evidence states,
and demotes dependent claims when nulls are matched.

## Design Principles

1. **Null declaration**: Every claim must declare which null families it belongs to
2. **Matched-null generation**: For each null family, generate appropriate null hypotheses
3. **Evidence state**: Machine-readable classification of every claim
4. **Automatic demotion**: When a null is matched, all dependent claims are demoted
5. **Publication gate**: Only surviving claims enter the publication queue

## Evidence States

| State | Meaning | Action |
|-------|---------|--------|
| **P** | Proved (Lean-checked) | Locked, cannot be demoted by null matching |
| **A** | Axiomatized | Can be demoted to H or R |
| **M** | Measured | Can be demoted to H or R |
| **H** | Hypothesized | Can be demoted to R |
| **S** | Semantic | Can be demoted to R |
| **R** | Retired | Locked, cannot be revived without explicit acknowledgment |

---

## Core Types

### Null Families

A null family classifies the type of null hypothesis that can falsify a claim.
-/

/-- Classification of null hypotheses for a research claim. -/
inductive NullFamily
  | degreeMatched    -- Null matched by degree of the polynomial/operator
  | densityMatched   -- Null matched by density parameter α
  | coneMatched      -- Null matched by cone/geometric structure
  | instrumentMatched -- Null matched by instrumentation/measurement
  | computeMatched   -- Null matched by compute budget
  | labelMatched     -- Null matched by label permutation
  | embeddingMatched -- Null matched by embedding/structural choice
  | selfImageMatched -- Null matched by self-referential structure
  deriving DecidableEq, Repr, Inhabited

/-- All null families. -/
def allNullFamilies : List NullFamily :=
  [.degreeMatched, .densityMatched, .coneMatched, .instrumentMatched,
   .computeMatched, .labelMatched, .embeddingMatched, .selfImageMatched]

/-- Convert a null family to a string. -/
def NullFamily.toString : NullFamily → String
  | .degreeMatched => "degree-matched"
  | .densityMatched => "density-matched"
  | .coneMatched => "cone-matched"
  | .instrumentMatched => "instrument-matched"
  | .computeMatched => "compute-matched"
  | .labelMatched => "label-matched"
  | .embeddingMatched => "embedding-matched"
  | .selfImageMatched => "self-image-matched"

instance : ToString NullFamily := ⟨NullFamily.toString⟩

/-- Null families that are automatically generated (not manually declared). -/
def generatedNullFamilies : List NullFamily :=
  [.degreeMatched, .densityMatched, .coneMatched, .instrumentMatched,
   .computeMatched, .labelMatched]

/-- Manually declared null families (require explicit specification). -/
def declaredNullFamilies : List NullFamily :=
  [.embeddingMatched, .selfImageMatched]

/-!
## Claim Representation

Each research claim has a unique identifier, evidence state, null family
declaration, and dependency list.
-/

/-- Machine-readable evidence state for a research claim. -/
inductive EvidenceState
  | P  -- Proved (Lean-checked)
  | A  -- Axiomatized
  | M  -- Measured
  | H  -- Hypothesized
  | S  -- Semantic
  | R  -- Retired
  deriving DecidableEq, Repr, Inhabited

/-- Convert evidence state to a string. -/
def EvidenceState.toString : EvidenceState → String
  | .P => "P (Proved)"
  | .A => "A (Axiomatized)"
  | .M => "M (Measured)"
  | .H => "H (Hypothesized)"
  | .S => "S (Semantic)"
  | .R => "R (Retired)"

instance : ToString EvidenceState := ⟨EvidenceState.toString⟩

/-- A research claim with full metadata. -/
structure Claim where
  /-- Unique claim identifier (e.g., "R166", "g_r_field", "rho_star") -/
  id : String
  /-- Human-readable description -/
  description : String
  /-- Current evidence state -/
  evidence : EvidenceState
  /-- Null families this claim belongs to -/
  nullFamilies : List NullFamily
  /-- Claims that depend on this claim (reverse dependencies) -/
  dependsOn : List String
  /-- Round of origin -/
  round : String
  /-- Whether this claim has been demoted -/
  demoted : Bool
  deriving Repr

/-!
## Null Generation

For each null family, generate appropriate null hypotheses.
-/

/-- Generate a null hypothesis for a given claim and null family.
  Returns a list of null specifications that can be tested. -/
def generateNulls (claim : Claim) (family : NullFamily) : List String :=
  match family with
  | .degreeMatched =>
      -- Generate nulls at different polynomial degrees
      [s!"{claim.id}_deg0", s!"{claim.id}_deg1", s!"{claim.id}_deg2",
       s!"{claim.id}_deg_max"]
  | .densityMatched =>
      -- Generate nulls at different density parameters α
      [s!"{claim.id}_α_low", s!"{claim.id}_α_mid", s!"{claim.id}_α_high",
       s!"{claim.id}_α_critical"]
  | .coneMatched =>
      -- Generate nulls with different cone/geometric structures
      [s!"{claim.id}_cone0", s!"{claim.id}_cone1", s!"{claim.id}_cone_dual"]
  | .instrumentMatched =>
      -- Generate nulls with different instrumentation
      [s!"{claim.id}_inst_none", s!"{claim.id}_inst_partial", s!"{claim.id}_inst_full"]
  | .computeMatched =>
      -- Generate nulls at different compute budgets
      [s!"{claim.id}_comp_low", s!"{claim.id}_comp_mid", s!"{claim.id}_comp_high"]
  | .labelMatched =>
      -- Generate nulls with permuted labels
      [s!"{claim.id}_label_id", s!"{claim.id}_label_random",
       s!"{claim.id}_label_anti"]
  | .embeddingMatched =>
      -- Generate nulls with different embeddings
      [s!"{claim.id}_embed_none", s!"{claim.id}_embed_partial",
       s!"{claim.id}_embed_full"]
  | .selfImageMatched =>
      -- Generate self-referential nulls
      [s!"{claim.id}_self_none", s!"{claim.id}_self_weak",
       s!"{claim.id}_self_strong"]

/-!
## Claim Graph

Manages the dependency graph and automatic demotion.
-/

/-- A claim graph tracks all claims and their dependencies. -/
structure ClaimGraph where
  /-- All claims indexed by ID -/
  claims : List Claim
  /-- Evidence ledger: tracks state transitions -/
  evidenceLog : List (String × EvidenceState × EvidenceState × String)

/-- Create an empty claim graph. -/
def emptyClaimGraph : ClaimGraph :=
  { claims := [], evidenceLog := [] }

/-- Add a claim to the graph. -/
def ClaimGraph.addClaim (g : ClaimGraph) (c : Claim) : ClaimGraph :=
  { g with claims := c :: g.claims }

/-- Record an evidence state transition. -/
def ClaimGraph.recordTransition (g : ClaimGraph) (claimId : String)
    (fromState toState : EvidenceState) (reason : String) : ClaimGraph :=
  { g with evidenceLog := (claimId, fromState, toState, reason) :: g.evidenceLog }

/-- Find a claim by ID. -/
def ClaimGraph.findClaim (g : ClaimGraph) (id : String) : Option Claim :=
  g.claims.find? fun c => c.id == id

/-- Check if a claim has been matched by any null family.
  A claim is "matched" if at least one of its null families has been tested
  and the null hypothesis was not rejected (i.e., the claim survived).
  
  This is a placeholder — actual implementation requires null testing infrastructure. -/
def ClaimGraph.isMatched (g : ClaimGraph) (id : String) : Bool :=
  -- Placeholder: return false for all claims
  -- Actual implementation would check null test results
  false

/-- Demote a claim and all its dependents.
  When a claim is demoted, all claims that depend on it are also demoted. -/
def ClaimGraph.demoteClaim (g : ClaimGraph) (id : String) (reason : String) : ClaimGraph :=
  match g.findClaim id with
  | none => g
  | some claim =>
    -- Mark this claim as demoted
    let g1 := { g with claims := g.claims.map fun c =>
      if c.id == id then {c with demoted := true} else c }
    -- Recursively demote dependents
    let g2 := claim.dependsOn.foldl (fun g' depId =>
      g'.demoteClaim depId s!"Demoted because {id} ({reason}) was demoted") g1
    -- Record the transition
    g2.recordTransition id .H .R reason

/-- Get all retired claims. -/
def ClaimGraph.retiredClaims (g : ClaimGraph) : List Claim :=
  g.claims.filter fun c => c.evidence == .R

/-- Get all active (non-retired, non-demoted) claims. -/
def ClaimGraph.activeClaims (g : ClaimGraph) : List Claim :=
  g.claims.filter fun c => c.evidence != .R && !c.demoted

/-!
## Null Test Result

Represents the outcome of testing a null hypothesis. -/

/-- Outcome of a null test. -/
inductive NullTestOutcome
  | notRejected  -- Null hypothesis was not rejected (claim survives)
  | rejected     -- Null hypothesis was rejected (claim is falsified)
  deriving DecidableEq, Repr, Inhabited

/-- A null test result. -/
structure NullTestResult where
  /-- ID of the null being tested -/
  nullId : String
  /-- ID of the claim being tested -/
  claimId : String
  /-- Null family used -/
  family : NullFamily
  /-- Outcome of the test -/
  outcome : NullTestOutcome
  /-- Statistical significance (if applicable) -/
  pValue : Option Float
  /-- Test configuration -/
  config : String
  deriving Repr

/-!
## Publication Queue

Only claims that survive null testing enter the publication queue.
-/

/-- A publication queue entry. -/
structure PublicationEntry where
  /-- Claim to publish -/
  claim : Claim
  /-- List of null tests that confirmed the claim -/
  supportingNulls : List NullTestResult
  /-- Round of publication -/
  round : String

/-- Publication queue: claims ready for or already published. -/
structure PublicationQueue where
  /-- Entries waiting for null testing -/
  pending : List PublicationEntry
  /-- Entries that passed all null tests -/
  confirmed : List PublicationEntry
  /-- Entries that failed some null tests -/
  failed : List PublicationEntry

/-- Create an empty publication queue. -/
def emptyPublicationQueue : PublicationQueue :=
  { pending := [], confirmed := [], failed := [] }

/-- Submit a claim for publication review. -/
def PublicationQueue.submit (q : PublicationQueue) (entry : PublicationEntry) : PublicationQueue :=
  { q with pending := entry :: q.pending }

/-- Process the publication queue: move pending entries to confirmed/failed
  based on null test results. -/
def PublicationQueue.process (q : PublicationQueue) : PublicationQueue :=
  -- Placeholder: actual processing requires null test infrastructure
  q

/-!
## Dashboard

Top-level view of the research programme's health.
-/

/-- Programme dashboard showing claim status. -/
structure ProgrammeDashboard where
  /-- Total claims -/
  totalClaims : Nat
  /-- Retired claims -/
  retiredClaims : Nat
  /-- Active claims -/
  activeClaims : Nat
  /-- Proved claims -/
  provedClaims : Nat
  /-- Claims pending null testing -/
  pendingClaims : Nat
  /-- Demoted claims this session -/
  demotedThisSession : List (String × String)

/-- Generate a dashboard from a claim graph. -/
def ProgrammeDashboard.fromGraph (g : ClaimGraph) : ProgrammeDashboard :=
  let claims := g.claims
  {
    totalClaims := claims.length
    retiredClaims := claims.filter fun c => c.evidence == .R |>.length
    activeClaims := claims.filter fun c => c.evidence != .R && !c.demoted |>.length
    provedClaims := claims.filter fun c => c.evidence == .P |>.length
    pendingClaims := 0  -- Placeholder
    demotedThisSession := []  -- Placeholder
  }

/-!
## Claim Registry

All claims from the Manifold Research programme, registered with their
evidence state, null families, and dependency information.

### Claim Categories

- **Turing Halting (TH)**: Claims about undecidability of halting in hypercomplex
- **Hardness Holonomy (HH)**: Claims about hardness barriers and holonomy
- **Cayley-Dickson Algebra (CD)**: Claims about algebraic structure
- **Structural Witness (SW)**: Claims about the T_n witness
- **Visibility Field (VF)**: Claims about g_r(α) and local invisibility
- **Observability Coordinates (OC)**: Claims about encoding advantages
- **Anti-Löb Methodology (AL)**: Claims about null-generation and demotion
- **Core Programme (CP)**: Claims about the programme's foundational assumptions

### Evidence Ledger

Each claim transitions through the P/A/M/H/S/R states as evidence accumulates.
The ledger records every transition with a reason.
-/


/-- A research claim with full metadata. -/
structure Claim where
  /-- Unique claim identifier (e.g., "TH_n3", "SW_backbone", "VF_gr") -/
  id : String
  /-- Human-readable description -/
  description : String
  /-- Current evidence state -/
  evidence : EvidenceState
  /-- Null families this claim belongs to -/
  nullFamilies : List NullFamily
  /-- Claims that depend on this claim (reverse dependencies) -/
  dependsOn : List String
  /-- Round of origin -/
  round : String
  /-- Whether this claim has been demoted -/
  demoted : Bool
  deriving Repr

/-- All claims in the programme, registered in dependency order. -/
def allClaims : List Claim :=
  -- === Core Programme (foundational) ===
  [
    { id := "CP_axiom"
      description := "Manifold Research programme axioms: hypercomplex algebra, structural witness, obstruction density"
      evidence := .A
      nullFamilies := [.selfImageMatched]
      dependsOn := []
      round := "R0"
      demoted := false },

    { id := "CP_braided"
      description := "The programme distinguishes 4 interacting fibers: algebraic computation, Lean formalization, conceptual architecture, honest assessment"
      evidence := .A
      nullFamilies := [.selfImageMatched]
      dependsOn := ["CP_axiom"]
      round := "R185"
      demoted := false },

    -- === Turing Halting (TH) ===
    { id := "TH_exists_n"
      description := "For n ≥ 3, ∃ T ∈ Aₙ with (T,T,T) ≠ 0, T*T ≠ T, nontrivial halting set, non-subalgebra halting set"
      evidence := .P
      nullFamilies := [.degreeMatched, .embeddingMatched]
      dependsOn := ["CD_mulByLevel", "CD_associator"]
      round := "R39"
      demoted := false },

    { id := "TH_halting"
      description := "For n ≥ 3 and any non-quine universal T, no algorithmic test decides halting"
      evidence := .P
      nullFamilies := [.computeMatched, .instrumentMatched]
      dependsOn := ["TH_exists_n", "TH_nonquine"]
      round := "R42"
      demoted := false },

    { id := "TH_holonomy"
      description := "For n ≥ 3 and any non-quine universal T, H(s) ≠ 0 for all s ≠ 0"
      evidence := .P
      nullFamilies := [.degreeMatched, .coneMatched]
      dependsOn := ["TH_exists_n"]
      round := "R45"
      demoted := false },

    { id := "TH_nonquine"
      description := "Non-quine universal T satisfies T*T ≠ T"
      evidence := .P
      nullFamilies := [.degreeMatched]
      dependsOn := ["CD_mulByLevel"]
      round := "R39"
      demoted := false },

    -- === Hardness Holonomy (HH) ===
    { id := "HH_barrier"
      description := "If computational holonomy is nonzero for all nonzero states, then the only algebraic fixed point is zero"
      evidence := .P
      nullFamilies := [.coneMatched]
      dependsOn := ["TH_holonomy"]
      round := "R50"
      demoted := false },

    { id := "HH_threeLayer"
      description := "The holonomy barrier is the proof floor; the associator measures non-associativity; the fixed point theorem is the ceiling"
      evidence := .A
      nullFamilies := [.coneMatched]
      dependsOn := ["HH_barrier", "CD_associator"]
      round := "R55"
      demoted := false },

    -- === Cayley-Dickson Algebra (CD) ===
    { id := "CD_mulByLevel"
      description := "Cayley-Dickson multiplication defined for all n via mulByLevel"
      evidence := .P
      nullFamilies := []
      dependsOn := []
      round := "R30"
      demoted := false },

    { id := "CD_associator"
      description := "The associator (a,b,c) = (ab)c - a(bc) measures failure of associativity; nonzero iff non-associative"
      evidence := .P
      nullFamilies := []
      dependsOn := ["CD_mulByLevel"]
      round := "R35"
      demoted := false },

    { id := "CD_hurwitz"
      description := "Norm multiplicativity holds for n=0,1,2,3 (Hurwitz); fails for n≥4"
      evidence := .P
      nullFamilies := [.degreeMatched]
      dependsOn := ["CD_mulByLevel"]
      round := "R36"
      demoted := false },

    { id := "CD_fano"
      description := "The Fano plane structure emerges at n ≥ 3, encoding non-commutativity and non-associativity"
      evidence := .P
      nullFamilies := []
      dependsOn := ["CD_mulByLevel"]
      round := "R38"
      demoted := false },

    -- === Structural Witness (SW) ===
    { id := "SW_witness_def"
      description := "Tₙ = e₀ + e_{2^{n-1}} + e_{2^n-1} is the structural witness for level n"
      evidence := .P
      nullFamilies := []
      dependsOn := ["CD_mulByLevel"]
      round := "R39"
      demoted := false },

    { id := "SW_backbone"
      description := "The support of T_n equals structuralBackbone n = {0, 2^{n-1}, 2^n-1}"
      evidence := .P
      nullFamilies := []
      dependsOn := ["SW_witness_def"]
      round := "R40"
      demoted := false },

    { id := "SW_backbone_card"
      description := "structuralBackbone n has exactly 3 elements for n ≥ 3"
      evidence := .P
      nullFamilies := []
      dependsOn := ["SW_backbone"]
      round := "R40"
      demoted := false },

    { id := "SW_holonomy"
      description := "T_n has nontrivial computational holonomy for n ≥ 3"
      evidence := .P
      nullFamilies := [.coneMatched]
      dependsOn := ["SW_witness_def", "CD_associator"]
      round := "R42"
      demoted := false },

    { id := "SW_embedding"
      description := "Octonions embed into Aₙ for n ≥ 4 via zero-padding"
      evidence := .P
      nullFamilies := [.embeddingMatched]
      dependsOn := ["CD_mulByLevel"]
      round := "R45"
      demoted := false },

    -- === Visibility Field (VF) ===
    { id := "VF_backbone"
      description := "Backbone positions {0, 2^{n-1}, 2^n-1} are determined by the Cayley-Dickson structure"
      evidence := .P
      nullFamilies := [.embeddingMatched]
      dependsOn := ["SW_backbone"]
      round := "R142"
      demoted := false },

    { id := "VF_gr_rises"
      description := "The visibility field g_r(α) rises toward the random 3-SAT threshold"
      evidence := .H
      nullFamilies := [.densityMatched, .computeMatched]
      dependsOn := ["SW_backbone"]
      round := "R183"
      demoted := false },

    { id := "VF_char_depth"
      description := "Characteristic visibility depth r_c ≈ 5 near random 3-SAT threshold"
      evidence := .M
      nullFamilies := [.densityMatched, .computeMatched]
      dependsOn := ["VF_gr_rises"]
      round := "R184"
      demoted := false },

    { id := "VF_exponent"
      description := "Critical exponent ν ≈ 1.7 for the visibility field scaling"
      evidence := .H
      nullFamilies := [.densityMatched, .computeMatched]
      dependsOn := ["VF_char_depth"]
      round := "R184"
      demoted := false },

    { id := "VF_scalar_response"
      description := "Proposed hidden hypercomplex volume failed; response looks scalar and single-scale"
      evidence := .R
      nullFamilies := [.coneMatched, .embeddingMatched]
      dependsOn := ["VF_gr_rises"]
      round := "R185"
      demoted := true },

    -- === Obstruction Density (OD) ===
    { id := "OD_rho_star"
      description := "Substrate-stable obstruction density ρ* = 0.135 ± 0.003"
      evidence := .M
      nullFamilies := [.densityMatched]
      dependsOn := ["SW_backbone", "VF_backbone"]
      round := "R185"
      demoted := false },

    { id := "OD_algebra_invariant"
      description := "Same obstruction density reported across several algebraic substrates (ℝ, ℂ, ℍ, 𝕆)"
      evidence := .M
      nullFamilies := [.embeddingMatched]
      dependsOn := ["OD_rho_star"]
      round := "R185"
      demoted := false },

    { id := "OD_annihilator_reveals"
      description := "The algebra reveals the wall; it does not remove it. Same ρ* across algebraic substrates"
      evidence := .A
      nullFamilies := [.embeddingMatched]
      dependsOn := ["OD_algebra_invariant"]
      round := "R185"
      demoted := false },

    -- === Observability Coordinates (OC) ===
    { id := "OC_definition"
      description := "Observability coordinate: encoding that changes accessibility of invariant without changing dynamics or complexity class"
      evidence := .A
      nullFamilies := [.selfImageMatched]
      dependsOn := []
      round := "R142"
      demoted := false },

    { id := "OC_cayleyDickson"
      description := "Cayley-Dickson encoding provides observability advantage: backbone visible at O(1) cost"
      evidence := .P
      nullFamilies := [.embeddingMatched]
      dependsOn := ["OC_definition", "SW_backbone"]
      round := "R142"
      demoted := false },

    { id := "OC_solver_neutral"
      description := "Cayley-Dickson encoding does NOT make SAT easier to solve (no solver advantage)"
      evidence := .P
      nullFamilies := [.degreeMatched]
      dependsOn := ["OC_cayleyDickson"]
      round := "R142"
      demoted := false },

    { id := "OC_advantage_separated"
      description := "Solver advantage vs observability advantage: algebra changes visibility without changing complexity"
      evidence := .A
      nullFamilies := [.selfImageMatched]
      dependsOn := ["OC_solver_neutral"]
      round := "R142"
      demoted := false },

    -- === Anti-Löb Methodology (AL) ===
    { id := "AL_null_families"
      description := "Eight null families: degree, density, cone, instrument, compute, label, embedding, self-image"
      evidence := .P
      nullFamilies := []
      dependsOn := []
      round := "R142"
      demoted := false },

    { id := "AL_matched_null"
      description := "Matched-null generation and claim demotion: every candidate signal declares its null family"
      evidence := .A
      nullFamilies := [.selfImageMatched]
      dependsOn := ["AL_null_families"]
      round := "R142"
      demoted := false },

    { id := "AL_evidence_lattice"
      description := "Six-level evidence lattice: Proved, Axiomatized, Measured, Hypothesized, Semantic, Retired"
      evidence := .P
      nullFamilies := [.selfImageMatched]
      dependsOn := []
      round := "R185"
      demoted := false },

    { id := "AL_publication_gate"
      description := "Publication queue: only claims surviving null testing enter confirmed"
      evidence := .A
      nullFamilies := [.selfImageMatched]
      dependsOn := ["AL_matched_null"]
      round := "R142"
      demoted := false },

    -- === Retired Claims ===
    { id := "R30_volume"
      description := "Hidden hypercomplex volume was proposed but failed matched-null tests"
      evidence := .R
      nullFamilies := [.coneMatched, .embeddingMatched]
      dependsOn := ["SW_witness_def"]
      round := "R30"
      demoted := true },

    { id := "R142_rugedness"
      description := "XOR can be more rugged than SAT while remaining polynomial"
      evidence := .R
      nullFamilies := [.degreeMatched]
      dependsOn := ["SW_witness_def"]
      round := "R142"
      demoted := true },

    { id := "R142_residual"
      description := "Proposed special residual geometry was eliminated by five matched-null investigations"
      evidence := .R
      nullFamilies := [.coneMatched, .embeddingMatched]
      dependsOn := ["SW_witness_def"]
      round := "R142"
      demoted := true }
  ]

/-!
## Claim Lookup Functions

Convenience functions for finding claims by ID or by evidence state.
-/

/-- Find a claim by ID. -/
def findClaim (id : String) (claims : List Claim) : Option Claim :=
  claims.find? fun c => c.id == id

/-- Find all claims in a given evidence state. -/
def claimsByState (s : EvidenceState) (claims : List Claim) : List Claim :=
  claims.filter fun c => c.evidence == s

/-- Count claims by evidence state. -/
def countByState (s : EvidenceState) (claims : List Claim) : Nat :=
  (claimsByState s claims).length

/-- Get the programme dashboard for all registered claims. -/
def programmeDashboard : ProgrammeDashboard :=
  ProgrammeDashboard.fromGraph { claims := allClaims, evidenceLog := [] }

end AntiLob
