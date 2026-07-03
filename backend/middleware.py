"""
Lambda SAT Middleware Kernel

Integrates lambda DSL, SAT solver, and proof checking into a unified pipeline
"""

from pathlib import Path
from typing import Optional, Dict, Any
import asyncio

from .lambda_dsl import (
    Evaluator,
    TypeChecker,
    LambdaExpr,
    abs_,
    app,
    effect,
    literal,
    pipeline,
    var
)
from .cnf_utils import (
    CNFFormula,
    parse_dimacs,
    parse_dimacs_file,
    verify_model,
    tseitin_transform
)
from .kissat_wrapper import (
    KissatWrapper,
    Heuristic,
    Budget,
    SolverResult as KissatResult
)
from .proof_checking import DRATChecker, LRATChecker
from .binary_clause_check import check_binary_clauses


#: Explicit certification modes
#:   dev      - solve even if proof tools are missing; results may be unverified
#:   strict   - SAT must model-check and UNSAT must proof-check, otherwise ERROR;
#:              all tools must be available at startup
#:   research - like dev, but responses additionally carry raw Kissat output
#:              alongside the verification status
CERTIFICATION_MODES = ('dev', 'strict', 'research')


def _certificate_status(status: str, verified: Optional[bool]) -> str:
    """Map a raw (status, verified) pair to an explicit certificate status.

    This is a read of existing response fields, not a new correctness
    guarantee: SAT_CERTIFIED/UNSAT_CERTIFIED mean the model/proof check
    already in `_handle_solve` passed. UNVERIFIED_SOLVER_CLAIM marks a
    solver-reported SAT/UNSAT that wasn't independently verified (only
    reachable outside strict mode, since strict mode already turns an
    unverified result into ERROR).
    """
    if status == 'SAT':
        return 'SAT_CERTIFIED' if verified else 'UNVERIFIED_SOLVER_CLAIM'
    if status == 'UNSAT':
        return 'UNSAT_CERTIFIED' if verified else 'UNVERIFIED_SOLVER_CLAIM'
    if status == 'TIMEOUT':
        return 'TIMEOUT'
    return 'ERROR'


class SolverMiddleware:
    """
    Lambda SAT Middleware

    Provides a typed lambda DSL for composing SAT solving pipelines with
    proof certification and model verification.
    """

    def __init__(
        self,
        kissat_binary: str = "kissat",
        drat_trim_binary: str = "drat-trim",
        lrat_check_binary: str = "lrat-check",
        strict_mode: Optional[bool] = None,
        mode: Optional[str] = None
    ):
        """
        Initialize middleware

        Args:
            kissat_binary: Path to Kissat binary
            drat_trim_binary: Path to drat-trim binary
            lrat_check_binary: Path to lrat-check binary
            strict_mode: Deprecated boolean alias; True maps to mode='strict',
                False maps to mode='dev'
            mode: Certification mode: 'dev', 'strict' or 'research'
                (default 'strict' to preserve prior behavior)
        """
        if mode is None:
            if strict_mode is None:
                mode = 'strict'
            else:
                mode = 'strict' if strict_mode else 'dev'
        if mode not in CERTIFICATION_MODES:
            raise ValueError(
                f"Unknown certification mode: {mode!r}. "
                f"Expected one of {CERTIFICATION_MODES}"
            )
        self.mode = mode
        self.strict_mode = (mode == 'strict')

        # Initialize solvers and checkers
        try:
            self.kissat = KissatWrapper(kissat_binary)
        except RuntimeError as e:
            if self.strict_mode:
                raise
            print(f"Warning: Kissat not available: {e}")
            self.kissat = None

        try:
            self.drat_checker = DRATChecker(drat_trim_binary)
        except RuntimeError as e:
            if self.strict_mode:
                raise
            print(f"Warning: DRAT checker not available: {e}")
            self.drat_checker = None

        try:
            self.lrat_checker = LRATChecker(lrat_check_binary)
        except RuntimeError as e:
            # LRAT is optional even in strict mode
            print(f"Info: LRAT checker not available: {e}")
            self.lrat_checker = None

        # Set up effect handlers
        self.effect_handlers = {
            'readCNF': self._handle_read_cnf,
            'solve': self._handle_solve,
            'checkModel': self._handle_check_model,
            'checkDRAT': self._handle_check_drat,
            'checkLRAT': self._handle_check_lrat
        }

        self.type_checker = TypeChecker()
        self.evaluator = Evaluator(self.effect_handlers)

    async def _handle_read_cnf(self, path: str) -> CNFFormula:
        """Effect handler: Read CNF from file"""
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"CNF file not found: {path}")
        return parse_dimacs_file(path_obj)

    async def _handle_solve(
        self,
        cnf: CNFFormula,
        heuristic: Dict[str, Any],
        budget: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Effect handler: Solve CNF formula"""
        # Fast independent pre-check: a binary-clause (2-SAT) contradiction
        # proves the whole formula UNSAT without invoking Kissat or waiting
        # on DRAT verification - the SCC argument is self-verifying, and
        # runs even if Kissat isn't installed. This only fires when such a
        # contradiction exists in the 2-literal clauses; otherwise it's a
        # no-op and Kissat runs as usual.
        binary_check = check_binary_clauses(cnf)
        if not binary_check.consistent:
            response = {
                'status': 'UNSAT',
                'verified': True,
                'proof_message': (
                    f'Proved UNSAT from binary clauses alone (2-SAT contradiction '
                    f'on variable {binary_check.conflicting_variable}); Kissat not invoked.'
                ),
                'stats': None,
            }
            if self.mode == 'research':
                response['raw_output'] = None
                response['mode'] = 'research'
            response['certificate'] = _certificate_status(
                response['status'], response.get('verified')
            )
            return response

        if self.kissat is None:
            raise RuntimeError("Kissat solver not available")

        # Convert dicts to dataclasses
        heuristic_obj = Heuristic(**heuristic) if isinstance(heuristic, dict) else heuristic
        budget_obj = Budget(**budget) if isinstance(budget, dict) else budget

        # Solve with Kissat
        result = self.kissat.solve(
            cnf,
            heuristic_obj,
            budget_obj,
            produce_proof=True
        )

        # Handle SAT result
        if result.result == KissatResult.SAT:
            # Verify model before returning
            if result.model and verify_model(cnf, result.model):
                response = {
                    'status': 'SAT',
                    'model': result.model,
                    'verified': True,
                    'stats': result.stats
                }
            else:
                response = {
                    'status': 'ERROR',
                    'message': 'Model verification failed',
                    'verified': False
                }

        # Handle UNSAT result
        elif result.result == KissatResult.UNSAT:
            verified = False
            proof_message = "No proof available"

            # Verify proof if available. Proof checking is a separate step
            # from solving and can take longer than the solve itself on hard
            # instances, so give it the same time budget the caller asked
            # for rather than a timeout hardcoded independent of it.
            if result.proof_path and self.drat_checker:
                proof_check = self.drat_checker.check_proof(
                    cnf, result.proof_path, timeout=budget_obj.time_limit
                )
                verified = proof_check.valid
                proof_message = proof_check.message

            if self.strict_mode and not verified:
                response = {
                    'status': 'ERROR',
                    'message': f'UNSAT proof verification required but failed: {proof_message}',
                    'verified': False
                }
            else:
                response = {
                    'status': 'UNSAT',
                    'verified': verified,
                    'proof_message': proof_message,
                    'stats': result.stats
                }

        # Handle timeout
        elif result.result == KissatResult.TIMEOUT:
            response = {
                'status': 'TIMEOUT',
                'message': result.error_message
            }

        # Handle error
        else:
            response = {
                'status': 'ERROR',
                'message': result.error_message
            }

        # Research mode: expose raw solver output alongside verification
        if self.mode == 'research':
            response['raw_output'] = result.raw_output
            response['mode'] = 'research'

        response['certificate'] = _certificate_status(
            response['status'], response.get('verified')
        )

        return response

    async def _handle_check_model(
        self,
        cnf: CNFFormula,
        model: Dict[int, bool]
    ) -> bool:
        """Effect handler: Verify model satisfies CNF"""
        return verify_model(cnf, model)

    async def _handle_check_drat(
        self,
        cnf: CNFFormula,
        proof_path: str
    ) -> Dict[str, Any]:
        """Effect handler: Check DRAT proof"""
        if self.drat_checker is None:
            return {
                'valid': False,
                'message': 'DRAT checker not available'
            }

        proof_path_obj = Path(proof_path)
        if not proof_path_obj.exists():
            return {
                'valid': False,
                'message': f'Proof file not found: {proof_path}'
            }

        result = self.drat_checker.check_proof(cnf, proof_path_obj)
        return {
            'valid': result.valid,
            'message': result.message
        }

    async def _handle_check_lrat(
        self,
        cnf: CNFFormula,
        proof_path: str
    ) -> Dict[str, Any]:
        """Effect handler: Check LRAT proof"""
        if self.lrat_checker is None:
            return {
                'valid': False,
                'message': 'LRAT checker not available'
            }

        proof_path_obj = Path(proof_path)
        if not proof_path_obj.exists():
            return {
                'valid': False,
                'message': f'Proof file not found: {proof_path}'
            }

        result = self.lrat_checker.check_proof(cnf, proof_path_obj)
        return {
            'valid': result.valid,
            'message': result.message
        }

    async def execute_pipeline(
        self,
        pipeline: LambdaExpr,
        input_data: Any
    ) -> Any:
        """
        Execute a lambda pipeline with type checking

        Args:
            pipeline: Lambda expression defining the pipeline
            input_data: Input data to the pipeline

        Returns:
            Result of pipeline execution
        """
        # Type check pipeline
        try:
            pipeline_type = self.type_checker.check(pipeline)
            print(f"Pipeline type: {pipeline_type}")
        except TypeError as e:
            raise TypeError(f"Pipeline type checking failed: {e}")

        # Evaluate pipeline
        result = await self.evaluator.evaluate(
            app(pipeline, literal(input_data))
        )

        return result

    def create_solve_pipeline(
        self,
        heuristic: Optional[Dict[str, Any]] = None,
        budget: Optional[Dict[str, Any]] = None
    ) -> LambdaExpr:
        """
        Create a standard solve pipeline: CNF -> solve -> Result

        Args:
            heuristic: Heuristic configuration
            budget: Budget configuration

        Returns:
            Lambda expression for the pipeline
        """
        if heuristic is None:
            heuristic = {
                'branching': 'vsids',
                'restarts': 'geometric',
                'phase': 'saved',
                'vivify': False
            }

        if budget is None:
            budget = {
                'time_limit': 30,
                'memory_limit': 256
            }

        # λ cnf. solve(cnf, heuristic, budget)
        # Wrapped in pipeline() (a no-op for a single stage) so this stays
        # consistent with create_path_pipeline() and any future multi-stage
        # composition, rather than returning the raw abs_(...) directly.
        return pipeline(
            abs_('cnf', effect('solve', var('cnf'), literal(heuristic), literal(budget)))
        )

    def create_path_pipeline(
        self,
        heuristic: Optional[Dict[str, Any]] = None,
        budget: Optional[Dict[str, Any]] = None
    ) -> LambdaExpr:
        """
        Create a two-stage pipeline: path -> readCNF -> solve -> Result

        Unlike create_solve_pipeline(), this pipeline accepts a file path and
        composes readCNF and solve as explicit DSL stages via pipeline().

        Args:
            heuristic: Heuristic configuration
            budget: Budget configuration

        Returns:
            Lambda expression for the two-stage pipeline
        """
        if heuristic is None:
            heuristic = {
                'branching': 'vsids',
                'restarts': 'geometric',
                'phase': 'saved',
                'vivify': False
            }

        if budget is None:
            budget = {
                'time_limit': 30,
                'memory_limit': 256
            }

        read_stage = abs_('path', effect('readCNF', var('path')))
        solve_stage = abs_(
            'cnf',
            effect('solve', var('cnf'), literal(heuristic), literal(budget))
        )
        # pipeline(read_stage, solve_stage) == λx. solve_stage(read_stage(x))
        return pipeline(read_stage, solve_stage)


def create_middleware(
    strict_mode: Optional[bool] = None,
    mode: Optional[str] = None,
    **kwargs
) -> SolverMiddleware:
    """
    Factory function to create middleware instance

    Args:
        strict_mode: Deprecated boolean alias; True maps to mode='strict',
            False maps to mode='dev'
        mode: Certification mode: 'dev' (tolerate missing tools),
            'strict' (require tools; SAT must model-check, UNSAT must
            proof-check) or 'research' (dev behavior plus raw solver output)
        **kwargs: Additional arguments passed to SolverMiddleware

    Returns:
        Configured SolverMiddleware instance
    """
    if mode is None and strict_mode is None:
        mode = 'dev'
    return SolverMiddleware(strict_mode=strict_mode, mode=mode, **kwargs)
