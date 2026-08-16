/-!
# Proof Distillation: a typed certification firewall

This import-free shadow formalizes one narrow architectural fact:
the seven research nodes emit candidate events, while a proved artifact
requires a separate external-verifier attestation. It does not formalize
the mathematical correctness of any extracted claim.

The file is intentionally not added to the active root import. Verify it as
an exact module and inspect the two `#print axioms` reports below.
-/

namespace VDIS.ProofDistillation

/-- The seven proof-distillation research roles. -/
inductive ResearchNode where
  | emperor
  | empress
  | pandora
  | bee
  | bordonSymphony
  | utai
  | toposAI
deriving DecidableEq, Repr

def ResearchNode.label : ResearchNode → String
  | .emperor => "Emperor"
  | .empress => "Empress"
  | .pandora => "Pandora"
  | .bee => "Bee"
  | .bordonSymphony => "Bordon Symphony"
  | .utai => "UTAI"
  | .toposAI => "Topos AI"

/-- Research statuses deliberately exclude `proved` and `refuted`. -/
inductive ResearchStatus where
  | captured
  | normalized
  | candidate
  | tested
  | proofCandidate
  | open
  | quarantined
deriving DecidableEq, Repr

/-- Content-addressed source location. -/
structure SourceDigest where
  pathOrUrl : String
  contentHash : String
  spanHash : String
deriving DecidableEq, Repr

/-- An immutable candidate moving through the research mesh. -/
structure CandidateArtifact where
  claimId : String
  statement : String
  hypotheses : List String
  source : SourceDigest
  producer : String
  status : ResearchStatus
  remainder : List String
  routeHistory : List String
deriving DecidableEq, Repr

/-- Replayable evidence produced outside the research-node family. -/
structure ExternalAttestation (candidate : CandidateArtifact) where
  verifierId : String
  verifierIndependent : verifierId ≠ candidate.producer
  certificateDigest : String
  replayRecipe : String
  checkerEnvironmentHash : String
  checkedClaimId : String
  claimMatches : checkedClaimId = candidate.claimId
  checkerAccepted : Bool
  checkerAccepted_eq : checkerAccepted = true

/-- A proved artifact is constructible only together with its attestation. -/
structure ProvedArtifact where
  candidate : CandidateArtifact
  attestation : ExternalAttestation candidate

/-- Research events and externally verified events have distinct constructors. -/
inductive MeshEvent where
  | research : ResearchNode → CandidateArtifact → MeshEvent
  | verified : ProvedArtifact → MeshEvent

/-- A research hop preserves the claim and source, appends its route, and can
only return the research constructor. -/
def runResearchNode (node : ResearchNode) (candidate : CandidateArtifact) :
    MeshEvent :=
  .research node
    { candidate with
      producer := node.label
      routeHistory := candidate.routeHistory ++ [node.label] }

/-- The promotion gate is separate and requires a fully typed attestation. -/
def promote (candidate : CandidateArtifact)
    (attestation : ExternalAttestation candidate) : MeshEvent :=
  .verified ⟨candidate, attestation⟩

/-- No invocation of a research node is definitionally a verified event. -/
theorem research_node_cannot_emit_verified
    (node : ResearchNode) (candidate : CandidateArtifact)
    (proved : ProvedArtifact) :
    runResearchNode node candidate ≠ .verified proved := by
  intro h
  cases h

/-- Every proved value carries a concrete external attestation. -/
theorem proved_artifact_has_attestation (proved : ProvedArtifact) :
    Nonempty (ExternalAttestation proved.candidate) :=
  ⟨proved.attestation⟩

/-- The full Bordon cycle has ten named phases. -/
inductive BordonPhase where
  | inhale
  | superpose
  | anneal
  | holoport
  | exhale
  | listen
  | measureHolonomy
  | reglue
  | moveFrame
  | continue
deriving DecidableEq, Repr

def fullBordonCycle : List BordonPhase :=
  [.inhale, .superpose, .anneal, .holoport, .exhale,
   .listen, .measureHolonomy, .reglue, .moveFrame, .continue]

theorem full_bordon_cycle_has_ten_phases :
    fullBordonCycle.length = 10 := rfl

end VDIS.ProofDistillation

#print axioms VDIS.ProofDistillation.research_node_cannot_emit_verified
#print axioms VDIS.ProofDistillation.proved_artifact_has_attestation
#print axioms VDIS.ProofDistillation.full_bordon_cycle_has_ten_phases
