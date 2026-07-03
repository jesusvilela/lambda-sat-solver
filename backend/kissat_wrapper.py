"""
Kissat SAT solver wrapper with DRAT proof support
"""

import os
import re
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Set, Tuple
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
    raw_output: Optional[str] = None


class KissatWrapper:
    """Wrapper for Kissat SAT solver"""

    def __init__(self, kissat_binary: str = "kissat"):
        self.kissat_binary = kissat_binary
        self.version: Optional[str] = None
        self.supported_flags: Set[str] = set()
        self._check_availability()
        self._detect_supported_options()

    def _check_availability(self):
        """Check if Kissat is available and detect its version"""
        try:
            result = subprocess.run(
                [self.kissat_binary, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError(f"Kissat binary not working: {self.kissat_binary}")
            self.version = result.stdout.strip().split('\n')[0].strip() or None
        except FileNotFoundError:
            raise RuntimeError(
                f"Kissat binary not found: {self.kissat_binary}. "
                "Please install Kissat and ensure it's in PATH."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Kissat version check timed out")

    #: Concrete flags the wrapper may emit, empirically validated against
    #: the detected binary at startup. Option names and value spaces changed
    #: across Kissat major versions (e.g. Kissat 4 has no --score and its
    #: --restart is a boolean, not a strategy name), so name-based checks
    #: are not sufficient: each exact flag is probed.
    _CANDIDATE_FLAGS = (
        '--score=vsids',
        '--score=vmtf',
        '--stable=2',
        '--stable=0',
        '--restart=luby',
        '--restart=never',
        '--restart=block',
        '--restart=false',
        '--reluctant=true',
        '--phase=false',
        '--phase=true',
        '--vivify=true',
        '--vivify=false',
        '--conflicts=1',
    )

    #: stderr patterns Kissat uses to reject unknown options
    _INVALID_OPTION_RE = re.compile(
        r'(invalid|unknown|unrecognized)\s+(long\s+)?option', re.IGNORECASE
    )

    def _probe_flag(self, flag: str) -> bool:
        """Empirically check whether the Kissat binary accepts a flag.

        Runs `kissat <flag>` with empty stdin: a rejected flag produces an
        'invalid option' error before any input is read, while an accepted
        flag proceeds to (and fails at) parsing the empty input.
        """
        try:
            result = subprocess.run(
                [self.kissat_binary, flag],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=5
            )
        except (subprocess.TimeoutExpired, OSError):
            return False
        output = (result.stderr or '') + (result.stdout or '')
        return not self._INVALID_OPTION_RE.search(output)

    def _detect_supported_options(self):
        """Validate at startup which of the wrapper's candidate flags this
        Kissat build accepts, so that unsupported heuristic requests fail
        fast at solve time instead of erroring inside the solver or
        silently degrading."""
        for flag in self._CANDIDATE_FLAGS:
            if self._probe_flag(flag):
                self.supported_flags.add(flag)

        # Numeric-valued options are probed with a sample value and
        # recorded as templates.
        if '--conflicts=1' in self.supported_flags:
            self.supported_flags.discard('--conflicts=1')
            self.supported_flags.add('--conflicts=<n>')

        if not self.supported_flags:
            print(
                f"Warning: could not validate any heuristic flags for "
                f"'{self.kissat_binary}' "
                f"({self.version or 'unknown version'}); "
                "heuristic flags will be omitted.",
                file=sys.stderr
            )

    def _select_flag(
        self,
        candidates,
        requested: str,
        required: bool = True
    ) -> Optional[str]:
        """Select the first candidate flag validated for this build.

        Args:
            candidates: Ordered list of concrete flag strings
            requested: Human-readable description of the requested setting
            required: If True, raise when no candidate is supported
                (fail fast); if False, silently fall back to solver defaults

        Raises:
            ValueError: If required and the detected Kissat build accepts
                none of the candidate flags.
        """
        for flag in candidates:
            key = flag
            if flag.startswith('--conflicts='):
                key = '--conflicts=<n>'
            if key in self.supported_flags:
                return flag
        if not self.supported_flags:
            # Flag validation failed entirely; already warned at startup
            return None
        if required:
            raise ValueError(
                f"Heuristic setting {requested!r} is not supported by "
                f"{self.version or self.kissat_binary} "
                f"(none of {list(candidates)} accepted)"
            )
        return None

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

            # Build Kissat command (validates heuristic flags against the
            # detected Kissat build; unsupported requests fail fast here)
            try:
                cmd = self._build_command(
                    cnf_path,
                    heuristic,
                    budget,
                    proof_path
                )
            except ValueError as e:
                return SolverOutput(
                    result=SolverResult.ERROR,
                    error_message=f"Unsupported heuristic configuration: {e}"
                )

            # Run Kissat
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=budget.time_limit,
                    preexec_fn=self._make_memory_limiter(budget.memory_limit)
                )

                output = self._parse_output(result, proof_path)

                # Copy proof file to a persistent location if it exists.
                # Use mkstemp to avoid the TOCTOU race that mktemp() creates.
                if output.proof_path and output.proof_path.exists():
                    fd, persistent_path = tempfile.mkstemp(
                        suffix='.drat', prefix='kissat_proof_'
                    )
                    try:
                        os.close(fd)
                        shutil.copy2(output.proof_path, persistent_path)
                    except Exception:
                        os.unlink(persistent_path)
                        raise
                    output.proof_path = Path(persistent_path)

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

    @staticmethod
    def _make_memory_limiter(memory_limit_mb: Optional[int]):
        """Create a preexec_fn that enforces the memory budget via
        RLIMIT_AS in the child process (POSIX only).

        Returns None when no limit is requested or the platform does not
        support resource limits, so subprocess.run behaves as before.
        """
        if not memory_limit_mb:
            return None
        try:
            import resource
        except ImportError:
            # Non-POSIX platform: no OS-level enforcement available
            return None

        limit_bytes = memory_limit_mb * 1024 * 1024

        def set_limits():
            try:
                resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
            except (ValueError, OSError):
                # Cannot lower/raise limit in this environment; run unrestricted
                pass

        return set_limits

    def _build_command(
        self,
        cnf_path: Path,
        heuristic: Heuristic,
        budget: Budget,
        proof_path: Optional[Path]
    ) -> list:
        """Build Kissat command with heuristic settings.

        Uses option names validated at startup against the detected binary
        (`kissat --range` plus `--help`), because option names changed
        across Kissat versions:
          Kissat 1.x/2.x era: --score=vmtf|vsids, --restart=...
          Kissat 3.x/4.x:     --stable=0|1|2 (0=focused/VMTF, 2=stable/score),
                              --phase=<bool>, --vivify=<bool>, --conflicts=<n>

        Raises:
            ValueError: If an explicitly requested heuristic maps to an
                option that the detected Kissat build does not support
                (fail fast instead of silently degrading).
        """
        cmd = [self.kissat_binary]

        # Branching heuristic.
        # Older Kissat: --score=vmtf|vsids. Kissat 4: focused mode (VMTF-style)
        # vs stable mode (score/VSIDS-style) selected via --stable.
        # 'lrb', 'chb', 'random' are not Kissat heuristics; approximate with
        # the solver default (no flag required).
        if heuristic.branching == 'vsids':
            flag = self._select_flag(
                ['--score=vsids', '--stable=2'],
                f'branching={heuristic.branching}'
            )
            if flag:
                cmd.append(flag)
        elif heuristic.branching in ('vmtf', 'lrb', 'chb', 'random'):
            flag = self._select_flag(
                ['--score=vmtf', '--stable=0'],
                f'branching={heuristic.branching}',
                required=False
            )
            if flag:
                cmd.append(flag)

        # Restart strategy.
        # Older Kissat: --restart=block|luby|always|never.
        # Kissat 4 has boolean --restart plus --reluctant (reluctant
        # doubling, which generates the Luby sequence): 'fixed' maps to
        # --restart=false and 'luby' to --reluctant=true. 'geometric'
        # (this wrapper's default naming) degrades to the solver default.
        # Explicit requests fail fast when no equivalent flag is accepted.
        if heuristic.restarts == 'luby':
            flag = self._select_flag(
                ['--restart=luby', '--reluctant=true'],
                f'restarts={heuristic.restarts}'
            )
            if flag:
                cmd.append(flag)
        elif heuristic.restarts == 'fixed':
            flag = self._select_flag(
                ['--restart=never', '--restart=false'],
                f'restarts={heuristic.restarts}'
            )
            if flag:
                cmd.append(flag)
        elif heuristic.restarts == 'geometric':
            flag = self._select_flag(
                ['--restart=block'],
                f'restarts={heuristic.restarts}',
                required=False
            )
            if flag:
                cmd.append(flag)
        # 'block' (default) needs no explicit flag

        # Phase (initial polarity for variable decisions)
        if heuristic.phase in ('false', 'true'):
            flag = self._select_flag(
                [f'--phase={heuristic.phase}'],
                f'phase={heuristic.phase}'
            )
            if flag:
                cmd.append(flag)
        # 'saved' and 'random' use Kissat's default (phase=true = saved polarity)

        # Vivification inprocessing (only required when explicitly enabled)
        flag = self._select_flag(
            ['--vivify=true' if heuristic.vivify else '--vivify=false'],
            f'vivify={heuristic.vivify}',
            required=heuristic.vivify
        )
        if flag:
            cmd.append(flag)

        # Conflict budget
        if budget.conflict_limit:
            flag = self._select_flag(
                [f'--conflicts={budget.conflict_limit}'],
                f'conflict_limit={budget.conflict_limit}'
            )
            if flag:
                cmd.append(flag)

        # Positional arguments: CNF file, then optional proof file
        cmd.append(str(cnf_path))
        if proof_path:
            cmd.append(str(proof_path))

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
                stats=self._extract_stats(stdout),
                raw_output=stdout
            )

        elif 's UNSATISFIABLE' in stdout:
            # Check for proof file
            if proof_path and proof_path.exists():
                return SolverOutput(
                    result=SolverResult.UNSAT,
                    proof_path=proof_path,
                    stats=self._extract_stats(stdout),
                    raw_output=stdout
                )
            else:
                return SolverOutput(
                    result=SolverResult.UNSAT,
                    stats=self._extract_stats(stdout),
                    raw_output=stdout
                )

        else:
            return SolverOutput(
                result=SolverResult.ERROR,
                error_message=f"Could not parse solver output. stdout: {stdout[:200]}",
                raw_output=stdout
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
        """Extract statistics from Kissat output.

        Kissat writes statistics lines in the format:
            c <key>:       <value>   <optional extra text>
        e.g.
            c conflicts:                    4713         per second:   ...
            c decisions:                    5000         ...
            c memory:                       12.3 MB

        We extract the first numeric token after the colon as the value.
        Keys are normalised to lower-case with spaces replaced by underscores.
        """
        stats = {}

        for line in output.split('\n'):
            line = line.strip()
            if not line.startswith('c '):
                continue
            body = line[2:]
            if ':' not in body:
                continue
            key_part, _, value_part = body.partition(':')
            key = key_part.strip().lower().replace(' ', '_')
            if not key:
                continue
            # Extract first token that looks like a number (int or float)
            for token in value_part.split():
                try:
                    stats[key] = int(token)
                    break
                except ValueError:
                    try:
                        stats[key] = float(token)
                        break
                    except ValueError:
                        continue

        return stats
