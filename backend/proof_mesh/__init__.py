"""Proof-distillation hypermesh.

The seven named research nodes propose, extract, challenge, and compare
artifacts. They are deliberately unable to certify a theorem. Certification
crosses the separate :class:`PromotionGate` boundary.
"""

from .artifacts import (
    Attestation,
    ClaimLanguage,
    ClaimKind,
    EpistemicRegister,
    Evidence,
    EvidenceKind,
    ProofArtifact,
    Remainder,
    SourceLocator,
    Status,
)
from .nodes import (
    BordonSymphonyNode,
    BeeNode,
    ConnectionEdge,
    EmperorNode,
    EmpressNode,
    LocalSection,
    PandoraNode,
    ToposAINode,
    UTAINode,
)
from .orchestrator import ProofHypermesh
from .ledger import ArtifactStore
from .verifiers import (
    FormalizationReport,
    LeanDeclarationVerifier,
    OpenSSLEd25519Signer,
    PromotedArtifact,
    PromotionGate,
    VerificationReport,
)

__all__ = [
    "Attestation",
    "ArtifactStore",
    "BeeNode",
    "BordonSymphonyNode",
    "ClaimKind",
    "ClaimLanguage",
    "ConnectionEdge",
    "EmperorNode",
    "EmpressNode",
    "EpistemicRegister",
    "Evidence",
    "EvidenceKind",
    "FormalizationReport",
    "LocalSection",
    "LeanDeclarationVerifier",
    "OpenSSLEd25519Signer",
    "PandoraNode",
    "ProofArtifact",
    "ProofHypermesh",
    "PromotionGate",
    "PromotedArtifact",
    "Remainder",
    "SourceLocator",
    "Status",
    "ToposAINode",
    "UTAINode",
    "VerificationReport",
]
