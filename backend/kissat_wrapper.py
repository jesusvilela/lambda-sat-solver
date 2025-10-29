"""
Kissat SAT solver wrapper with DRAT proof support
"""

import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

from .cnf_utils import CNFFormula, write_dimacs, parse_model_line


class SolverResult(Enum):
    """SAT solver result"""
    SAT = "SAT"
    UNSAT = "UNSAT"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"


@dataclass
class Heuristic:
    """Heuristic configuration for SAT solver"""
    branching: str = 'vsids'  # vsids, lrb, chb, random
    restarts: str = 'geometric'  # geometric, luby, fixed
    phase: str = 'saved'  # saved, false, true, random
    vivify: bool = False


@dataclass
class Budget:
    """Resource budget for solver"""
    time_limit: int = 30  # seconds
    memory_limit: int = 256  # MB
    conflict_limit: Optional[int] = None


@dataclass
class SolverOutput:
    """Output from SAT solver"""
    result: SolverResult
    model: Optional[Dict[int, bool]] = None
    proof_path: Optional[Path] = None
    stats: Optional[Dict[str, any]] = None
    error_message: Optional[str] = None


class KissatWrapper:
    """Wrapper for Kissat SAT solver"""

    def __init__(self, kissat_binary: str = "kissat"):
        self.kissat_binary = kissat_binary
        self._check_availability()

    def _check_availability(self):
        """Check if Kissat is available"""
        try:
            result = subprocess.run(
                [self.kissat_binary, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError(f"Kissat binary not working: {self.kissat_binary}")
        except FileNotFoundError:
            raise RuntimeError(
                f"Kissat binary not found: {self.kissat_binary}. "
                "Please install Kissat and ensure it's in PATH."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Kissat version check timed out")

    def solve(
        self,
        formula: CNFFormula,
        heuristic: Optional[Heuristic] = None,
        budget: Optional[Budget] = None,
        produce_proof: bool = True
    ) -> SolverOutput:
        """
        Solve CNF formula using Kissat

        Args:
            formula: CNF formula to solve
            heuristic: Heuristic configuration
            budget: Resource budget
            produce_proof: Whether to produce DRAT proof for UNSAT

        Returns:
            SolverOutput with result and optional model/proof
        """
        if heuristic is None:
            heuristic = Heuristic()
        if budget is None:
            budget = Budget()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Write CNF to file
            cnf_path = tmpdir / "formula.cnf"
            write_dimacs(formula, cnf_path)

            # Prepare proof file path
            proof_path = None
            if produce_proof:
                proof_path = tmpdir / "proof.drat"

            # Build Kissat command
            cmd = self._build_command(
                cnf_path,
                heuristic,
                budget,
                proof_path
            )

            # Run Kissat
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=budget.time_limit
                )

                output = self._parse_output(result, proof_path)

                # Copy proof file to a persistent location if it exists
                if output.proof_path and output.proof_path.exists():
                    persistent_proof = Path(tempfile.mktemp(suffix='.drat', prefix='kissat_proof_'))
                    shutil.copy2(output.proof_path, persistent_proof)
                    output.proof_path = persistent_proof

                return output

            except subprocess.TimeoutExpired:
                return SolverOutput(
                    result=SolverResult.TIMEOUT,
                    error_message=f"Solver exceeded time limit of {budget.time_limit}s"
                )
            except Exception as e:
                return SolverOutput(
                    result=SolverResult.ERROR,
                    error_message=f"Solver execution failed: {str(e)}"
                )

    def _build_command(
        self,
        cnf_path: Path,
        heuristic: Heuristic,
        budget: Budget,
        proof_path: Optional[Path]
    ) -> list:
        """Build Kissat command with heuristic settings"""
        cmd = [self.kissat_binary]

        # Add heuristic flags
        # Note: These are example flags - actual Kissat flags may vary
        if heuristic.branching == 'lrb':
            cmd.append('--lrb')
        elif heuristic.branching == 'chb':
            cmd.append('--chb')

        if heuristic.restarts == 'luby':
            cmd.append('--luby')

        if heuristic.phase == 'false':
            cmd.append('--phase=false')
        elif heuristic.phase == 'true':
            cmd.append('--phase=true')
        elif heuristic.phase == 'random':
            cmd.append('--phase=random')

        if heuristic.vivify:
            cmd.append('--vivify')

        # Add budget constraints
        if budget.conflict_limit:
            cmd.extend(['--conflicts', str(budget.conflict_limit)])

        # Add proof output
        if proof_path:
            cmd.extend([str(cnf_path), str(proof_path)])
        else:
            cmd.append(str(cnf_path))

        return cmd

    def _parse_output(
        self,
        result: subprocess.CompletedProcess,
        proof_path: Optional[Path]
    ) -> SolverOutput:
        """Parse Kissat output"""
        stdout = result.stdout
        stderr = result.stderr

        # Parse result
        if 's SATISFIABLE' in stdout:
            # Extract model
            model = self._extract_model(stdout)
            return SolverOutput(
                result=SolverResult.SAT,
                model=model,
                stats=self._extract_stats(stdout)
            )

        elif 's UNSATISFIABLE' in stdout:
            # Check for proof file
            if proof_path and proof_path.exists():
                return SolverOutput(
                    result=SolverResult.UNSAT,
                    proof_path=proof_path,
                    stats=self._extract_stats(stdout)
                )
            else:
                return SolverOutput(
                    result=SolverResult.UNSAT,
                    stats=self._extract_stats(stdout)
                )

        else:
            return SolverOutput(
                result=SolverResult.ERROR,
                error_message=f"Could not parse solver output. stdout: {stdout[:200]}"
            )

    def _extract_model(self, output: str) -> Dict[int, bool]:
        """Extract model from Kissat output"""
        model = {}

        for line in output.split('\n'):
            line = line.strip()
            if line.startswith('v '):
                model.update(parse_model_line(line))

        return model

    def _extract_stats(self, output: str) -> Dict[str, any]:
        """Extract statistics from Kissat output"""
        stats = {}

        for line in output.split('\n'):
            line = line.strip()
            if line.startswith('c '):
                # Parse statistics lines
                # Format: "c conflicts: 1234"
                parts = line[2:].split(':')
                if len(parts) == 2:
                    key = parts[0].strip()
                    try:
                        value = int(parts[1].strip())
                        stats[key] = value
                    except ValueError:
                        stats[key] = parts[1].strip()

        return stats
