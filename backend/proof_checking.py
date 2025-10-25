"""
DRAT and LRAT proof checking wrappers
"""

import subprocess
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from .cnf_utils import CNFFormula, write_dimacs


@dataclass
class ProofCheckResult:
    """Result of proof checking"""
    valid: bool
    message: str
    checker_output: Optional[str] = None


class DRATChecker:
    """Wrapper for drat-trim proof checker"""

    def __init__(self, drat_trim_binary: str = "drat-trim"):
        self.drat_trim_binary = drat_trim_binary
        self._check_availability()

    def _check_availability(self):
        """Check if drat-trim is available"""
        try:
            result = subprocess.run(
                [self.drat_trim_binary, '--help'],
                capture_output=True,
                text=True,
                timeout=5
            )
            # drat-trim may return non-zero for --help, so we just check it runs
        except FileNotFoundError:
            raise RuntimeError(
                f"drat-trim binary not found: {self.drat_trim_binary}. "
                "Please install drat-trim and ensure it's in PATH."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("drat-trim check timed out")

    def check_proof(
        self,
        formula: CNFFormula,
        proof_path: Path,
        timeout: int = 60
    ) -> ProofCheckResult:
        """
        Verify DRAT proof

        Args:
            formula: Original CNF formula
            proof_path: Path to DRAT proof file
            timeout: Timeout in seconds

        Returns:
            ProofCheckResult indicating validity
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Write formula to file
            cnf_path = tmpdir / "formula.cnf"
            write_dimacs(formula, cnf_path)

            # Run drat-trim
            cmd = [
                self.drat_trim_binary,
                str(cnf_path),
                str(proof_path)
            ]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )

                # drat-trim returns 0 if proof is valid
                if result.returncode == 0:
                    return ProofCheckResult(
                        valid=True,
                        message="DRAT proof verified successfully",
                        checker_output=result.stdout
                    )
                else:
                    return ProofCheckResult(
                        valid=False,
                        message="DRAT proof verification failed",
                        checker_output=result.stdout + "\n" + result.stderr
                    )

            except subprocess.TimeoutExpired:
                return ProofCheckResult(
                    valid=False,
                    message=f"Proof checking timed out after {timeout}s"
                )
            except Exception as e:
                return ProofCheckResult(
                    valid=False,
                    message=f"Proof checking failed: {str(e)}"
                )


class LRATChecker:
    """Wrapper for LRAT proof checker"""

    def __init__(self, lrat_check_binary: str = "lrat-check"):
        self.lrat_check_binary = lrat_check_binary
        self._check_availability()

    def _check_availability(self):
        """Check if lrat-check is available"""
        try:
            result = subprocess.run(
                [self.lrat_check_binary],
                capture_output=True,
                text=True,
                timeout=5
            )
        except FileNotFoundError:
            raise RuntimeError(
                f"lrat-check binary not found: {self.lrat_check_binary}. "
                "Please install lrat-check and ensure it's in PATH."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("lrat-check timed out")

    def check_proof(
        self,
        formula: CNFFormula,
        proof_path: Path,
        timeout: int = 60
    ) -> ProofCheckResult:
        """
        Verify LRAT proof

        Args:
            formula: Original CNF formula
            proof_path: Path to LRAT proof file
            timeout: Timeout in seconds

        Returns:
            ProofCheckResult indicating validity
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Write formula to file
            cnf_path = tmpdir / "formula.cnf"
            write_dimacs(formula, cnf_path)

            # Run lrat-check
            cmd = [
                self.lrat_check_binary,
                str(cnf_path),
                str(proof_path)
            ]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )

                # Check for verification success
                if 's VERIFIED' in result.stdout or result.returncode == 0:
                    return ProofCheckResult(
                        valid=True,
                        message="LRAT proof verified successfully",
                        checker_output=result.stdout
                    )
                else:
                    return ProofCheckResult(
                        valid=False,
                        message="LRAT proof verification failed",
                        checker_output=result.stdout + "\n" + result.stderr
                    )

            except subprocess.TimeoutExpired:
                return ProofCheckResult(
                    valid=False,
                    message=f"Proof checking timed out after {timeout}s"
                )
            except Exception as e:
                return ProofCheckResult(
                    valid=False,
                    message=f"Proof checking failed: {str(e)}"
                )
