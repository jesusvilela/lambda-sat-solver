"""External verifier adapters and the only final-status promotion gate.

Reports are diagnostic values, not capabilities. The gate invokes verifier
objects that were installed into its trusted configuration; callers cannot
promote by manufacturing a report dataclass.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
import copy
from hashlib import sha256
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any, Mapping, Protocol

from .artifacts import (
    Attestation,
    ClaimLanguage,
    ProofArtifact,
    Status,
    canonical_json,
    digest,
)
from .ledger import ArtifactStore


@dataclass(frozen=True)
class VerificationReport:
    claim_id: str
    input_hash: str
    verifier_id: str
    independent_of: str
    accepted: bool
    verdict: Status
    certificate_kind: str
    certificate_digest: str
    replay_recipe: str
    checker_environment_hash: str
    assumptions: tuple[str, ...] = ()
    diagnostic: str = ""

    def __post_init__(self) -> None:
        if self.verdict not in (Status.PROVED, Status.REFUTED):
            raise ValueError("verifier verdict must be proved or refuted")


@dataclass(frozen=True)
class FormalizationReport:
    claim_id: str
    input_hash: str
    verifier_id: str
    independent_of: str
    accepted: bool
    formal_statement: str
    certificate_digest: str
    method: str
    replay_recipe: str
    checker_environment_hash: str
    diagnostic: str = ""


class ArtifactVerifier(Protocol):
    verifier_id: str

    def verify(self, artifact: ProofArtifact) -> VerificationReport: ...


class AdequacyVerifier(Protocol):
    verifier_id: str

    def verify_adequacy(self, artifact: ProofArtifact) -> FormalizationReport: ...


class PromotionSigner(Protocol):
    gate_id: str
    public_key_pem: bytes

    def sign(self, payload: bytes) -> str: ...


class OpenSSLEd25519Signer:
    """Ed25519 signer backed by OpenSSL.

    In an adversarial deployment this object belongs in an isolated promotion
    process. Research nodes and UI consumers receive only ``public_key_pem``.
    """

    def __init__(
        self,
        *,
        gate_id: str,
        private_key_pem: bytes,
        openssl_binary: str | None = None,
    ):
        if not gate_id:
            raise ValueError("gate_id must be nonempty")
        binary = openssl_binary or shutil.which("openssl")
        if not binary:
            raise RuntimeError("OpenSSL is required for Ed25519 promotion signatures")
        self.gate_id = gate_id
        self.__private_key_pem = bytes(private_key_pem)
        self.openssl_binary = str(Path(binary).resolve())
        self.public_key_pem = self._derive_public_key()

    @classmethod
    def generate(
        cls, gate_id: str, openssl_binary: str | None = None
    ) -> "OpenSSLEd25519Signer":
        binary = openssl_binary or shutil.which("openssl")
        if not binary:
            raise RuntimeError("OpenSSL is required for Ed25519 promotion signatures")
        with tempfile.TemporaryDirectory(prefix="proof-mesh-keygen-") as tmp:
            private_path = Path(tmp) / "private.pem"
            result = subprocess.run(
                [binary, "genpkey", "-algorithm", "ED25519", "-out", str(private_path)],
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"OpenSSL Ed25519 key generation failed: {result.stderr}"
                )
            private_key = private_path.read_bytes()
        return cls(
            gate_id=gate_id,
            private_key_pem=private_key,
            openssl_binary=binary,
        )

    def _derive_public_key(self) -> bytes:
        with tempfile.TemporaryDirectory(prefix="proof-mesh-pubkey-") as tmp:
            private_path = Path(tmp) / "private.pem"
            public_path = Path(tmp) / "public.pem"
            private_path.write_bytes(self.__private_key_pem)
            result = subprocess.run(
                [
                    self.openssl_binary,
                    "pkey",
                    "-in",
                    str(private_path),
                    "-pubout",
                    "-out",
                    str(public_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"OpenSSL public-key derivation failed: {result.stderr}"
                )
            return public_path.read_bytes()

    def sign(self, payload: bytes) -> str:
        with tempfile.TemporaryDirectory(prefix="proof-mesh-sign-") as tmp:
            private_path = Path(tmp) / "private.pem"
            payload_path = Path(tmp) / "payload.bin"
            signature_path = Path(tmp) / "signature.bin"
            private_path.write_bytes(self.__private_key_pem)
            payload_path.write_bytes(payload)
            result = subprocess.run(
                [
                    self.openssl_binary,
                    "pkeyutl",
                    "-sign",
                    "-inkey",
                    str(private_path),
                    "-rawin",
                    "-in",
                    str(payload_path),
                    "-out",
                    str(signature_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(f"OpenSSL Ed25519 signing failed: {result.stderr}")
            return base64.b64encode(signature_path.read_bytes()).decode("ascii")

    @staticmethod
    def verify(
        *,
        payload: bytes,
        signature: str,
        public_key_pem: bytes,
        openssl_binary: str | None = None,
    ) -> bool:
        binary = openssl_binary or shutil.which("openssl")
        if not binary:
            return False
        try:
            signature_bytes = base64.b64decode(signature, validate=True)
        except (ValueError, TypeError):
            return False
        with tempfile.TemporaryDirectory(prefix="proof-mesh-verify-") as tmp:
            public_path = Path(tmp) / "public.pem"
            payload_path = Path(tmp) / "payload.bin"
            signature_path = Path(tmp) / "signature.bin"
            public_path.write_bytes(public_key_pem)
            payload_path.write_bytes(payload)
            signature_path.write_bytes(signature_bytes)
            result = subprocess.run(
                [
                    binary,
                    "pkeyutl",
                    "-verify",
                    "-pubin",
                    "-inkey",
                    str(public_path),
                    "-rawin",
                    "-in",
                    str(payload_path),
                    "-sigfile",
                    str(signature_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            return result.returncode == 0


def _unsigned_attestation_payload(
    *,
    artifact: ProofArtifact,
    report: VerificationReport,
    gate_id: str,
    adequacy: FormalizationReport | None,
) -> dict[str, Any]:
    return {
        "claim_id": report.claim_id,
        "verifier_id": report.verifier_id,
        "verdict": report.verdict.value,
        "certificate_kind": report.certificate_kind,
        "certificate_digest": report.certificate_digest,
        "replay_recipe": report.replay_recipe,
        "checker_environment_hash": report.checker_environment_hash,
        "input_hash": report.input_hash,
        "independent_of": report.independent_of,
        "assumptions": report.assumptions,
        "adequacy_verifier_id": None if adequacy is None else adequacy.verifier_id,
        "adequacy_certificate_digest": (
            None if adequacy is None else adequacy.certificate_digest
        ),
        "adequacy_independent_of": (
            None if adequacy is None else adequacy.independent_of
        ),
        "adequacy_method": None if adequacy is None else adequacy.method,
        "adequacy_replay_recipe": (
            None if adequacy is None else adequacy.replay_recipe
        ),
        "adequacy_checker_environment_hash": (
            None if adequacy is None else adequacy.checker_environment_hash
        ),
        "gate_id": gate_id,
        "candidate_artifact_id": artifact.artifact_id,
        "candidate_payload": artifact.to_dict(),
    }


@dataclass(frozen=True)
class PromotedArtifact:
    """A final verdict envelope whose authority is external trust, not its type."""

    candidate: ProofArtifact
    attestation: Attestation

    @property
    def claimed_status(self) -> Status:
        return self.attestation.verdict

    def verify_signature(self, trusted_gate_keys: Mapping[str, bytes]) -> bool:
        try:
            if not self.candidate.validate_integrity():
                return False
        except (TypeError, ValueError):
            return False
        key = trusted_gate_keys.get(self.attestation.gate_id)
        if key is None:
            return False
        if self.attestation.claim_id != self.candidate.claim_id:
            return False
        if self.attestation.input_hash != self.candidate.artifact_id:
            return False
        report = VerificationReport(
            claim_id=self.attestation.claim_id,
            input_hash=self.attestation.input_hash,
            verifier_id=self.attestation.verifier_id,
            independent_of=self.attestation.independent_of,
            accepted=True,
            verdict=self.attestation.verdict,
            certificate_kind=self.attestation.certificate_kind,
            certificate_digest=self.attestation.certificate_digest,
            replay_recipe=self.attestation.replay_recipe,
            checker_environment_hash=self.attestation.checker_environment_hash,
            assumptions=self.attestation.assumptions,
        )
        adequacy = (
            None
            if self.attestation.adequacy_verifier_id is None
            else FormalizationReport(
                claim_id=self.candidate.claim_id,
                input_hash=self.candidate.artifact_id,
                verifier_id=self.attestation.adequacy_verifier_id,
                independent_of=self.attestation.adequacy_independent_of or "",
                accepted=True,
                formal_statement=self.candidate.formal_statement or "",
                certificate_digest=(
                    self.attestation.adequacy_certificate_digest or ""
                ),
                method=self.attestation.adequacy_method or "",
                replay_recipe=self.attestation.adequacy_replay_recipe or "",
                checker_environment_hash=(
                    self.attestation.adequacy_checker_environment_hash or ""
                ),
            )
        )
        payload = _unsigned_attestation_payload(
            artifact=self.candidate,
            report=report,
            gate_id=self.attestation.gate_id,
            adequacy=adequacy,
        )
        return OpenSSLEd25519Signer.verify(
            payload=canonical_json(payload).encode("utf-8"),
            signature=self.attestation.signature,
            public_key_pem=key,
        )

    def trusted_status(
        self, trusted_gate_keys: Mapping[str, bytes]
    ) -> Status | None:
        return self.attestation.verdict if self.verify_signature(trusted_gate_keys) else None


class PromotionGate:
    """Object-capability boundary between research and proof status.

    Verifier instances, rather than user-provided reports or verifier-name
    strings, are the trusted capabilities. Configuring this gate is a TCB
    operation.
    """

    def __init__(
        self,
        verifiers: Mapping[str, ArtifactVerifier],
        *,
        signer: PromotionSigner,
        artifact_store: ArtifactStore,
        adequacy_verifiers: Mapping[str, AdequacyVerifier] | None = None,
    ):
        self.gate_id = signer.gate_id
        self.__signer = signer
        self.__artifact_store = artifact_store
        self.__verifiers = dict(verifiers)
        self.__adequacy_verifiers = dict(adequacy_verifiers or {})
        for name, verifier in self.__verifiers.items():
            if name != verifier.verifier_id:
                raise ValueError("verifier registry key must equal verifier.verifier_id")
        for name, verifier in self.__adequacy_verifiers.items():
            if name != verifier.verifier_id:
                raise ValueError(
                    "adequacy registry key must equal verifier.verifier_id"
                )

    def verify_and_promote(
        self,
        artifact: ProofArtifact,
        *,
        verifier_id: str,
        adequacy_verifier_id: str | None = None,
    ) -> PromotedArtifact:
        if not artifact.validate_integrity():
            raise ValueError("candidate artifact integrity failed before verification")
        if not self.__artifact_store.lineage_complete(artifact):
            raise ValueError(
                "candidate is not present with a complete lineage in the gate-side store"
            )
        try:
            verifier = self.__verifiers[verifier_id]
        except KeyError as exc:
            raise PermissionError("verifier capability is not installed") from exc
        report = verifier.verify(artifact)
        self._validate_report(artifact, verifier_id, report)

        adequacy: FormalizationReport | None = None
        if artifact.claim_language is ClaimLanguage.PROSE:
            if adequacy_verifier_id is None:
                raise ValueError(
                    "prose claims require a separately installed "
                    "formalization-adequacy verifier"
                )
            try:
                adequacy_verifier = self.__adequacy_verifiers[adequacy_verifier_id]
            except KeyError as exc:
                raise PermissionError(
                    "formalization-adequacy verifier capability is not installed"
                ) from exc
            adequacy = adequacy_verifier.verify_adequacy(artifact)
            self._validate_adequacy(
                artifact,
                adequacy_verifier_id,
                adequacy,
                proof_verifier_id=report.verifier_id,
            )

        unsigned = _unsigned_attestation_payload(
            artifact=artifact,
            report=report,
            gate_id=self.gate_id,
            adequacy=adequacy,
        )
        signature = self.__signer.sign(
            canonical_json(unsigned).encode("utf-8")
        )
        attestation = Attestation(
            claim_id=report.claim_id,
            verifier_id=report.verifier_id,
            verdict=report.verdict,
            certificate_kind=report.certificate_kind,
            certificate_digest=report.certificate_digest,
            replay_recipe=report.replay_recipe,
            checker_environment_hash=report.checker_environment_hash,
            input_hash=report.input_hash,
            independent_of=report.independent_of,
            assumptions=report.assumptions,
            adequacy_verifier_id=None if adequacy is None else adequacy.verifier_id,
            adequacy_certificate_digest=(
                None if adequacy is None else adequacy.certificate_digest
            ),
            adequacy_independent_of=(
                None if adequacy is None else adequacy.independent_of
            ),
            adequacy_method=None if adequacy is None else adequacy.method,
            adequacy_replay_recipe=(
                None if adequacy is None else adequacy.replay_recipe
            ),
            adequacy_checker_environment_hash=(
                None if adequacy is None else adequacy.checker_environment_hash
            ),
            gate_id=self.gate_id,
            signature=signature,
        )
        return PromotedArtifact(candidate=artifact, attestation=attestation)

    @staticmethod
    def _validate_report(
        artifact: ProofArtifact,
        requested_verifier_id: str,
        report: VerificationReport,
    ) -> None:
        if report.verifier_id != requested_verifier_id:
            raise ValueError("verifier returned a mismatched identity")
        if not report.accepted:
            raise ValueError(f"verifier rejected certificate: {report.diagnostic}")
        if report.claim_id != artifact.claim_id:
            raise ValueError("verifier report belongs to a different claim")
        if report.input_hash != artifact.artifact_id:
            raise ValueError("verifier report belongs to a different artifact state")
        if report.independent_of != artifact.producer:
            raise ValueError("verifier independence was not bound to the producer")
        if report.verifier_id == artifact.producer:
            raise ValueError("proposer and verifier must be distinct")
        if artifact.formal_statement is None:
            raise ValueError("there is no formal statement for the checker to certify")
        if artifact.remainder.proof_blockers():
            raise ValueError(
                "proof-critical remainder is nonempty: "
                f"{artifact.remainder.proof_blockers()}"
            )
        if artifact.claim_language is ClaimLanguage.PROSE and (
            artifact.remainder.ambiguity_set
            or artifact.remainder.competing_interpretations
        ):
            raise ValueError(
                "prose claim has unresolved ambiguity or competing interpretations"
            )
        if report.verdict is Status.PROVED and artifact.status is not Status.PROOF_CANDIDATE:
            raise ValueError("only an explicit proof candidate may be proved")
        required = (
            report.certificate_kind,
            report.certificate_digest,
            report.replay_recipe,
            report.checker_environment_hash,
        )
        if any(not item for item in required):
            raise ValueError("certificate is not replayable or environment-locked")

    @staticmethod
    def _validate_adequacy(
        artifact: ProofArtifact,
        requested_verifier_id: str,
        report: FormalizationReport,
        *,
        proof_verifier_id: str,
    ) -> None:
        if report.verifier_id != requested_verifier_id:
            raise ValueError("adequacy verifier returned a mismatched identity")
        if not report.accepted:
            raise ValueError(
                f"formalization adequacy was rejected: {report.diagnostic}"
            )
        if report.claim_id != artifact.claim_id:
            raise ValueError("adequacy report belongs to a different claim")
        if report.input_hash != artifact.artifact_id:
            raise ValueError("adequacy report belongs to a different artifact state")
        if report.independent_of != artifact.producer:
            raise ValueError("adequacy review was not independent of the producer")
        if report.verifier_id == artifact.producer:
            raise ValueError("proposer cannot certify its own formalization adequacy")
        if report.verifier_id == proof_verifier_id:
            raise ValueError(
                "proof checking and prose/formal adequacy require distinct principals"
            )
        if report.formal_statement != artifact.formal_statement:
            raise ValueError("adequacy report checks a different formal statement")
        if any(
            not item
            for item in (
                report.certificate_digest,
                report.method,
                report.replay_recipe,
                report.checker_environment_hash,
            )
        ):
            raise ValueError(
                "adequacy review lacks a replayable, environment-locked certificate"
            )


_LEAN_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*$")
_LEAN_IMPORT_COMMAND = re.compile(
    r"(?m)^\s*(?:(?:public|private)\s+)*import\b"
)


class LeanDeclarationVerifier:
    """Compile one exact import-free source and inspect one declaration.

    Imported dependency closures require an isolated clean builder, which this
    first deployment does not pretend to provide. A green root ``lake build``
    is not sufficient because Lean accepts ``sorry``.
    """

    STANDARD_AXIOMS = frozenset({"propext", "Quot.sound", "Classical.choice"})

    def __init__(
        self,
        *,
        project_root: str | Path,
        import_module: str,
        declaration: str,
        source_file: str | Path,
        timeout_seconds: int = 120,
        allowed_axioms: set[str] | frozenset[str] | None = None,
    ):
        if not _LEAN_IDENTIFIER.fullmatch(import_module):
            raise ValueError("unsafe or unsupported Lean module identifier")
        if not _LEAN_IDENTIFIER.fullmatch(declaration):
            raise ValueError("unsafe or unsupported Lean declaration identifier")
        self.project_root = Path(project_root).expanduser().resolve()
        self.import_module = import_module
        self.declaration = declaration
        self.source_file = Path(source_file).expanduser().resolve()
        try:
            self.source_file.relative_to(self.project_root)
        except ValueError as exc:
            raise ValueError("Lean source_file must be inside project_root") from exc
        if self.source_file.suffix != ".lean" or not self.source_file.is_file():
            raise ValueError("Lean source_file must be an existing .lean file")
        self.timeout_seconds = timeout_seconds
        self.allowed_axioms = (
            self.STANDARD_AXIOMS
            if allowed_axioms is None
            else frozenset(allowed_axioms)
        )
        self.verifier_id = f"lean-kernel:{import_module}:{declaration}"

    def environment_hash(self) -> str:
        payload: dict[str, str] = {}
        for name in ("lean-toolchain", "lakefile.toml", "lakefile.lean", "lake-manifest.json"):
            path = self.project_root / name
            if path.exists() and path.is_file():
                payload[name] = sha256(path.read_bytes()).hexdigest()
        payload[
            f"target-source:{self.source_file.relative_to(self.project_root)}"
        ] = sha256(self.source_file.read_bytes()).hexdigest()
        lake_binary = shutil.which("lake")
        if lake_binary:
            lake_path = Path(lake_binary).resolve()
            payload["lake-binary-path"] = str(lake_path)
            payload["lake-binary-sha256"] = sha256(lake_path.read_bytes()).hexdigest()
        try:
            version = subprocess.run(
                ["lake", "env", "lean", "--version"],
                cwd=self.project_root,
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            payload["lean-version"] = version.stdout + version.stderr
            lean_env_path = subprocess.run(
                ["lake", "env", "printenv", "PATH"],
                cwd=self.project_root,
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            ).stdout.strip()
            lean_binary = shutil.which("lean", path=lean_env_path)
            if lean_binary:
                lean_path = Path(lean_binary).resolve()
                payload["lean-binary-path"] = str(lean_path)
                payload["lean-binary-sha256"] = sha256(
                    lean_path.read_bytes()
                ).hexdigest()
        except (OSError, subprocess.TimeoutExpired) as exc:
            payload["lean-version-error"] = repr(exc)
        return digest(payload)

    def _reported_axioms(self, output: str) -> tuple[str, ...] | None:
        declaration = re.escape(self.declaration)
        if re.search(
            rf"'{declaration}' does not depend on any axioms", output
        ):
            return ()
        match = re.search(
            rf"'{declaration}' depends on axioms:\s*\[([^\]]*)\]",
            output,
            re.DOTALL,
        )
        if not match:
            return None
        return tuple(
            item.strip()
            for item in match.group(1).replace("\n", " ").split(",")
            if item.strip()
        )

    def verify(self, artifact: ProofArtifact) -> VerificationReport:
        environment_hash = self.environment_hash()
        if artifact.formal_statement != self.declaration:
            return self._rejected(
                artifact,
                environment_hash,
                "artifact formal symbol differs from requested declaration",
            )
        if artifact.formal_environment_hash != environment_hash:
            return self._rejected(
                artifact,
                environment_hash,
                "artifact is not locked to the current source/checker environment",
            )
        source_bytes = self.source_file.read_bytes()
        source_hash = sha256(source_bytes).hexdigest()
        if artifact.source.content_hash != source_hash:
            return self._rejected(
                artifact,
                environment_hash,
                "artifact source digest differs from exact Lean source",
            )
        source_text = source_bytes.decode("utf-8")
        if _LEAN_IMPORT_COMMAND.search(source_text):
            return self._rejected(
                artifact,
                environment_hash,
                "source imports dependencies; isolated clean dependency replay "
                "is required and not implemented by this adapter",
            )
        audit_source = source_text + f"\n#print axioms {self.declaration}\n"
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".lean",
                prefix="ProofMeshAudit_",
                dir=self.project_root,
                encoding="utf-8",
                delete=False,
            ) as handle:
                handle.write(audit_source)
                audit_path = Path(handle.name)
            try:
                result = subprocess.run(
                    ["lake", "env", "lean", str(audit_path)],
                    cwd=self.project_root,
                    text=True,
                    capture_output=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )
            finally:
                audit_path.unlink(missing_ok=True)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return self._rejected(
                artifact, environment_hash, f"Lean replay failed to run: {exc}"
            )

        output = result.stdout + "\n" + result.stderr
        axioms = self._reported_axioms(output)
        unsafe_markers = ("sorryAx", "declaration uses 'sorry'", "declaration uses ‘sorry’")
        unexpected_axioms = (
            ()
            if axioms is None
            else tuple(axiom for axiom in axioms if axiom not in self.allowed_axioms)
        )
        accepted = (
            result.returncode == 0
            and axioms is not None
            and not any(marker in output for marker in unsafe_markers)
            and not unexpected_axioms
        )
        diagnostic_parts: list[str] = []
        if result.returncode != 0:
            diagnostic_parts.append(f"Lean exited {result.returncode}")
        if axioms is None:
            diagnostic_parts.append("no parseable #print axioms result")
        if unexpected_axioms:
            diagnostic_parts.append(f"unexpected axioms: {unexpected_axioms}")
        if any(marker in output for marker in unsafe_markers):
            diagnostic_parts.append("sorryAx detected")
        return VerificationReport(
            claim_id=artifact.claim_id,
            input_hash=artifact.artifact_id,
            verifier_id=self.verifier_id,
            independent_of=artifact.producer,
            accepted=accepted,
            verdict=Status.PROVED,
            certificate_kind="Lean kernel replay plus #print axioms",
            certificate_digest=sha256(output.encode("utf-8")).hexdigest(),
            replay_recipe=(
                f"Append `#print axioms {self.declaration}` to an exact copy "
                f"of {self.source_file}"
                + f", then run `lake env lean` inside {self.project_root}"
            ),
            checker_environment_hash=environment_hash,
            assumptions=tuple(axioms or ()),
            diagnostic="; ".join(diagnostic_parts) if diagnostic_parts else "accepted",
        )

    def _rejected(
        self, artifact: ProofArtifact, environment_hash: str, diagnostic: str
    ) -> VerificationReport:
        return VerificationReport(
            claim_id=artifact.claim_id,
            input_hash=artifact.artifact_id,
            verifier_id=self.verifier_id,
            independent_of=artifact.producer,
            accepted=False,
            verdict=Status.PROVED,
            certificate_kind="Lean kernel replay plus #print axioms",
            certificate_digest=sha256(diagnostic.encode("utf-8")).hexdigest(),
            replay_recipe="not available: precondition failed",
            checker_environment_hash=environment_hash,
            diagnostic=diagnostic,
        )


class DRATVerifierAdapter:
    """Run a TOCTOU-safe DRAT replay as a diagnostic, never a promotion.

    A DRAT proof certifies UNSAT of exact CNF bytes; it does not certify that
    those bytes faithfully encode an arbitrary mathematical claim. Until a
    separately trust-anchored claim-to-CNF adequacy attestation exists, this
    adapter always returns ``accepted=False`` even when replay succeeds.
    """

    def __init__(
        self,
        *,
        checker: Any,
        formula: Any,
        proof_path: str | Path,
        checker_environment_hash: str,
        replay_recipe: str,
        verifier_id: str = "drat-trim:explicit-verified",
    ):
        self.checker = checker
        self.formula_snapshot = copy.deepcopy(formula)
        proof = Path(proof_path).expanduser().resolve()
        self.proof_bytes = proof.read_bytes()
        self.checker_environment_hash = checker_environment_hash
        self.replay_recipe = replay_recipe
        self.verifier_id = verifier_id
        formula_payload = (
            self.formula_snapshot.to_dict()
            if hasattr(self.formula_snapshot, "to_dict")
            else repr(self.formula_snapshot)
        )
        self.formula_digest = sha256(
            canonical_json(formula_payload).encode("utf-8")
        ).hexdigest()

    def verify(self, artifact: ProofArtifact) -> VerificationReport:
        formula_now = (
            self.formula_snapshot.to_dict()
            if hasattr(self.formula_snapshot, "to_dict")
            else repr(self.formula_snapshot)
        )
        if sha256(canonical_json(formula_now).encode("utf-8")).hexdigest() != self.formula_digest:
            raise RuntimeError("internal CNF snapshot mutated")
        with tempfile.NamedTemporaryFile(suffix=".drat", delete=False) as handle:
            handle.write(self.proof_bytes)
            replay_path = Path(handle.name)
        try:
            result = self.checker.check_proof(
                copy.deepcopy(self.formula_snapshot), replay_path
            )
        finally:
            replay_path.unlink(missing_ok=True)
        output = result.checker_output or result.message
        replay_valid = bool(result.valid and "s VERIFIED" in output)
        proof_digest = sha256(self.proof_bytes).hexdigest()
        certificate_digest = digest(
            {
                "formula_digest": self.formula_digest,
                "proof_digest": proof_digest,
                "checker_output_digest": sha256(output.encode("utf-8")).hexdigest(),
            }
        )
        return VerificationReport(
            claim_id=artifact.claim_id,
            input_hash=artifact.artifact_id,
            verifier_id=self.verifier_id,
            independent_of=artifact.producer,
            accepted=False,
            verdict=Status.PROVED,
            certificate_kind="DRAT replay diagnostic; encoding unverified",
            certificate_digest=certificate_digest,
            replay_recipe=self.replay_recipe,
            checker_environment_hash=self.checker_environment_hash,
            assumptions=(
                f"formula_digest={self.formula_digest}",
            ),
            diagnostic=(
                (
                    "DRAT replay succeeded, but claim-to-CNF adequacy has no "
                    "trust-anchored certificate"
                )
                if replay_valid
                else result.message
            ),
        )
