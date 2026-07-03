"""
Tests for the Kissat wrapper: version detection, flag validation,
memory-limit enforcement and certification modes.

Solver-dependent tests are gated by KISSAT_BIN (default: 'kissat' on PATH)
and skipped when the solver is not installed. DRAT-dependent tests are
additionally gated by DRAT_TRIM_BIN.
"""

import os
import shutil
import pytest

from backend.cnf_utils import CNFFormula
from backend.kissat_wrapper import (
    KissatWrapper,
    Heuristic,
    Budget,
    SolverResult
)
from backend.middleware import SolverMiddleware, create_middleware

KISSAT_BIN = os.environ.get('KISSAT_BIN', 'kissat')
DRAT_TRIM_BIN = os.environ.get('DRAT_TRIM_BIN', 'drat-trim')

kissat_available = shutil.which(KISSAT_BIN) is not None
drat_available = shutil.which(DRAT_TRIM_BIN) is not None

requires_kissat = pytest.mark.skipif(
    not kissat_available,
    reason=f"Kissat binary not available (KISSAT_BIN={KISSAT_BIN})"
)
requires_drat = pytest.mark.skipif(
    not (kissat_available and drat_available),
    reason=f"Kissat/drat-trim not available "
           f"(KISSAT_BIN={KISSAT_BIN}, DRAT_TRIM_BIN={DRAT_TRIM_BIN})"
)

UNSAT_FORMULA = CNFFormula(num_vars=2, clauses=[[1, 2], [-1], [-2]])
SAT_FORMULA = CNFFormula(num_vars=2, clauses=[[1, 2], [-1, 2]])


class TestWrapperInitialization:
    """Startup behavior: availability, version and flag detection"""

    def test_missing_binary_raises(self):
        with pytest.raises(RuntimeError):
            KissatWrapper("definitely-not-a-sat-solver-binary")

    @requires_kissat
    def test_version_detected(self):
        wrapper = KissatWrapper(KISSAT_BIN)
        assert wrapper.version

    @requires_kissat
    def test_flags_validated_at_startup(self):
        wrapper = KissatWrapper(KISSAT_BIN)
        # Every recorded flag must have been empirically accepted
        assert wrapper.supported_flags
        for flag in wrapper.supported_flags:
            assert flag.startswith('--')


@requires_kissat
class TestFlagValidation:
    """Fail-fast behavior for unsupported heuristic options"""

    def test_default_heuristic_solves(self):
        wrapper = KissatWrapper(KISSAT_BIN)
        output = wrapper.solve(SAT_FORMULA, Heuristic(), Budget(time_limit=10))
        assert output.result == SolverResult.SAT
        assert output.model

    def test_all_preset_heuristics_accepted_or_explicit_error(self):
        """Presets must either solve or produce an explicit
        'Unsupported heuristic configuration' error - never a silent
        solver-level failure."""
        wrapper = KissatWrapper(KISSAT_BIN)
        presets = [
            Heuristic(branching='vsids', restarts='geometric',
                      phase='saved', vivify=False),
            Heuristic(branching='lrb', restarts='luby',
                      phase='false', vivify=True),
            Heuristic(branching='random', restarts='fixed',
                      phase='random', vivify=False),
        ]
        for heuristic in presets:
            output = wrapper.solve(
                UNSAT_FORMULA, heuristic, Budget(time_limit=10)
            )
            if output.result == SolverResult.ERROR:
                assert 'Unsupported heuristic configuration' in (
                    output.error_message or ''
                )
            else:
                assert output.result == SolverResult.UNSAT

    def test_select_flag_fails_fast_for_unknown_flag(self):
        wrapper = KissatWrapper(KISSAT_BIN)
        with pytest.raises(ValueError):
            wrapper._select_flag(
                ['--no-such-option=xyz'], 'bogus setting'
            )

    def test_select_flag_optional_falls_back(self):
        wrapper = KissatWrapper(KISSAT_BIN)
        assert wrapper._select_flag(
            ['--no-such-option=xyz'], 'bogus setting', required=False
        ) is None

    def test_conflict_limit_flag(self):
        wrapper = KissatWrapper(KISSAT_BIN)
        output = wrapper.solve(
            UNSAT_FORMULA, Heuristic(),
            Budget(time_limit=10, conflict_limit=1000)
        )
        assert output.result in (SolverResult.UNSAT, SolverResult.ERROR)
        if output.result == SolverResult.ERROR:
            assert 'Unsupported heuristic configuration' in (
                output.error_message or ''
            )


class TestMemoryLimiter:
    """OS-level memory budget enforcement"""

    def test_no_limit_returns_none(self):
        assert KissatWrapper._make_memory_limiter(None) is None
        assert KissatWrapper._make_memory_limiter(0) is None

    def test_limiter_callable_on_posix(self):
        limiter = KissatWrapper._make_memory_limiter(256)
        try:
            import resource  # noqa: F401
        except ImportError:
            assert limiter is None
        else:
            assert callable(limiter)

    @requires_kissat
    def test_solve_within_memory_limit(self):
        wrapper = KissatWrapper(KISSAT_BIN)
        output = wrapper.solve(
            SAT_FORMULA, Heuristic(),
            Budget(time_limit=10, memory_limit=512)
        )
        assert output.result == SolverResult.SAT


@requires_kissat
class TestProofPersistence:
    """DRAT proofs must survive the temporary solve directory"""

    def test_unsat_proof_persisted(self):
        wrapper = KissatWrapper(KISSAT_BIN)
        output = wrapper.solve(UNSAT_FORMULA, Heuristic(), Budget(time_limit=10))
        assert output.result == SolverResult.UNSAT
        assert output.proof_path is not None
        assert output.proof_path.exists()
        output.proof_path.unlink()

    @requires_drat
    def test_unsat_proof_checks(self):
        from backend.proof_checking import DRATChecker
        wrapper = KissatWrapper(KISSAT_BIN)
        output = wrapper.solve(UNSAT_FORMULA, Heuristic(), Budget(time_limit=10))
        assert output.proof_path is not None
        checker = DRATChecker(DRAT_TRIM_BIN)
        result = checker.check_proof(UNSAT_FORMULA, output.proof_path)
        assert result.valid
        output.proof_path.unlink()


class TestCertificationModes:
    """Explicit dev / strict / research certification modes"""

    def test_invalid_mode_rejected(self):
        with pytest.raises(ValueError):
            create_middleware(mode='production')

    def test_default_mode_is_dev(self):
        middleware = create_middleware()
        assert middleware.mode == 'dev'
        assert middleware.strict_mode is False

    def test_strict_mode_alias(self):
        try:
            middleware = create_middleware(strict_mode=True)
        except RuntimeError:
            # strict mode fails fast when tools are missing - also correct
            assert not (kissat_available and drat_available)
            return
        assert middleware.mode == 'strict'
        assert middleware.strict_mode is True

    def test_dev_mode_tolerates_missing_tools(self):
        middleware = SolverMiddleware(
            kissat_binary='definitely-not-a-sat-solver-binary',
            mode='dev'
        )
        assert middleware.kissat is None

    def test_strict_mode_requires_tools(self):
        with pytest.raises(RuntimeError):
            SolverMiddleware(
                kissat_binary='definitely-not-a-sat-solver-binary',
                mode='strict'
            )

    @requires_kissat
    @pytest.mark.asyncio
    async def test_research_mode_exposes_raw_output(self):
        middleware = create_middleware(mode='research', kissat_binary=KISSAT_BIN)
        pipeline = middleware.create_solve_pipeline()
        result = await middleware.execute_pipeline(pipeline, SAT_FORMULA)
        assert result['status'] == 'SAT'
        assert result.get('mode') == 'research'
        assert 'raw_output' in result

    @requires_drat
    @pytest.mark.asyncio
    async def test_strict_mode_certifies_unsat(self):
        middleware = create_middleware(
            mode='strict',
            kissat_binary=KISSAT_BIN,
            drat_trim_binary=DRAT_TRIM_BIN
        )
        pipeline = middleware.create_solve_pipeline()
        result = await middleware.execute_pipeline(pipeline, UNSAT_FORMULA)
        assert result['status'] == 'UNSAT'
        assert result['verified'] is True
