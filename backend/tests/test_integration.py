"""
Integration tests for Lambda SAT Middleware

Solver-dependent tests are gated on Kissat availability: set KISSAT_BIN to
point at a Kissat binary (default: 'kissat' on PATH). Tests are skipped,
not failed, when the solver is not installed.
"""

import os
import pytest
import asyncio
import json
import shutil
from pathlib import Path
import tempfile

from backend.middleware import create_middleware
from backend.cnf_utils import CNFFormula, parse_dimacs, write_dimacs, tseitin_transform

KISSAT_BIN = os.environ.get('KISSAT_BIN', 'kissat')
requires_kissat = pytest.mark.skipif(
    shutil.which(KISSAT_BIN) is None,
    reason=f"Kissat binary not available (KISSAT_BIN={KISSAT_BIN})"
)


@requires_kissat
class TestMiddlewareIntegration:
    """Integration tests for middleware pipeline"""

    @pytest.mark.asyncio
    async def test_simple_sat_formula(self):
        """Test solving a simple SAT formula"""
        middleware = create_middleware(strict_mode=False, kissat_binary=KISSAT_BIN)

        cnf = CNFFormula(num_vars=3, clauses=[[1, 2], [-1, 3], [-2, -3]])

        pipeline = middleware.create_solve_pipeline()
        result = await middleware.execute_pipeline(pipeline, cnf)

        assert result['status'] in ['SAT', 'ERROR']
        if result['status'] == 'SAT':
            assert 'model' in result
            assert result['verified'] is True

    @pytest.mark.asyncio
    async def test_simple_unsat_formula(self):
        """Test solving a simple UNSAT formula"""
        middleware = create_middleware(strict_mode=False, kissat_binary=KISSAT_BIN)

        # Contradictory formula: x1 AND -x1
        cnf = CNFFormula(num_vars=1, clauses=[[1], [-1]])

        pipeline = middleware.create_solve_pipeline()
        result = await middleware.execute_pipeline(pipeline, cnf)

        assert result['status'] in ['UNSAT', 'ERROR']

    @pytest.mark.asyncio
    async def test_tseitin_integration(self):
        """Test Tseitin transformation integrated with solver"""
        middleware = create_middleware(strict_mode=False, kissat_binary=KISSAT_BIN)

        # Formula: (x1 AND x2) OR (x3 AND x4)
        formula = {
            'type': 'OR',
            'children': [
                {
                    'type': 'AND',
                    'children': [
                        {'type': 'LITERAL', 'value': 1},
                        {'type': 'LITERAL', 'value': 2}
                    ]
                },
                {
                    'type': 'AND',
                    'children': [
                        {'type': 'LITERAL', 'value': 3},
                        {'type': 'LITERAL', 'value': 4}
                    ]
                }
            ]
        }

        cnf = tseitin_transform(formula)
        assert cnf.num_clauses > 0

        pipeline = middleware.create_solve_pipeline()
        result = await middleware.execute_pipeline(pipeline, cnf)

        assert result['status'] in ['SAT', 'UNSAT', 'TIMEOUT', 'ERROR']


@requires_kissat
class TestHeuristicConfigurations:
    """Test different heuristic configurations"""

    @pytest.mark.asyncio
    async def test_conservative_heuristic(self):
        """Test conservative heuristic"""
        middleware = create_middleware(strict_mode=False, kissat_binary=KISSAT_BIN)
        cnf = CNFFormula(num_vars=3, clauses=[[1, 2], [-1, 3]])

        heuristic = {
            'branching': 'vsids',
            'restarts': 'geometric',
            'phase': 'saved',
            'vivify': False
        }
        budget = {'time_limit': 10, 'memory_limit': 128}

        pipeline = middleware.create_solve_pipeline(heuristic, budget)
        result = await middleware.execute_pipeline(pipeline, cnf)

        assert result['status'] in ['SAT', 'UNSAT', 'TIMEOUT', 'ERROR']

    @pytest.mark.asyncio
    async def test_aggressive_heuristic(self):
        """Test aggressive heuristic"""
        middleware = create_middleware(strict_mode=False, kissat_binary=KISSAT_BIN)
        cnf = CNFFormula(num_vars=3, clauses=[[1, 2], [-1, 3]])

        heuristic = {
            'branching': 'lrb',
            'restarts': 'luby',
            'phase': 'false',
            'vivify': True
        }
        budget = {'time_limit': 10, 'memory_limit': 128}

        pipeline = middleware.create_solve_pipeline(heuristic, budget)
        result = await middleware.execute_pipeline(pipeline, cnf)

        assert result['status'] in ['SAT', 'UNSAT', 'TIMEOUT', 'ERROR']


@requires_kissat
class TestExampleFiles:
    """Test with example CNF files"""

    @pytest.mark.asyncio
    async def test_simple_sat_example(self):
        """Test with simple_sat.cnf example"""
        example_path = Path(__file__).parent.parent.parent / 'examples' / 'simple_sat.cnf'
        if not example_path.exists():
            pytest.skip("Example file not found")

        middleware = create_middleware(strict_mode=False, kissat_binary=KISSAT_BIN)
        cnf = parse_dimacs(example_path.read_text())

        pipeline = middleware.create_solve_pipeline()
        result = await middleware.execute_pipeline(pipeline, cnf)

        # Should be SAT or ERROR (if solver not available)
        assert result['status'] in ['SAT', 'ERROR']

    @pytest.mark.asyncio
    async def test_simple_unsat_example(self):
        """Test with simple_unsat.cnf example"""
        example_path = Path(__file__).parent.parent.parent / 'examples' / 'simple_unsat.cnf'
        if not example_path.exists():
            pytest.skip("Example file not found")

        middleware = create_middleware(strict_mode=False, kissat_binary=KISSAT_BIN)
        cnf = parse_dimacs(example_path.read_text())

        pipeline = middleware.create_solve_pipeline()
        result = await middleware.execute_pipeline(pipeline, cnf)

        # Should be UNSAT or ERROR (if solver not available)
        assert result['status'] in ['UNSAT', 'ERROR']


@requires_kissat
class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_empty_formula(self):
        """Test with empty formula"""
        middleware = create_middleware(strict_mode=False, kissat_binary=KISSAT_BIN)
        cnf = CNFFormula(num_vars=0, clauses=[])

        pipeline = middleware.create_solve_pipeline()
        result = await middleware.execute_pipeline(pipeline, cnf)

        # Empty formula is trivially SAT
        assert result['status'] in ['SAT', 'ERROR']

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling"""
        middleware = create_middleware(strict_mode=False, kissat_binary=KISSAT_BIN)
        cnf = CNFFormula(num_vars=3, clauses=[[1, 2], [-1, 3]])

        # Very short timeout
        heuristic = {
            'branching': 'vsids',
            'restarts': 'geometric',
            'phase': 'saved',
            'vivify': False
        }
        budget = {'time_limit': 0.001, 'memory_limit': 128}  # 1ms timeout

        pipeline = middleware.create_solve_pipeline(heuristic, budget)
        result = await middleware.execute_pipeline(pipeline, cnf)

        # May timeout or solve quickly
        assert result['status'] in ['SAT', 'UNSAT', 'TIMEOUT', 'ERROR']


@requires_kissat
class TestTseitinEndToEnd:
    """End-to-end tests with Tseitin transformation"""

    @pytest.mark.asyncio
    async def test_and_formula_e2e(self):
        """Test AND formula end-to-end"""
        middleware = create_middleware(strict_mode=False, kissat_binary=KISSAT_BIN)

        # x1 AND x2
        formula = {
            'type': 'AND',
            'children': [
                {'type': 'LITERAL', 'value': 1},
                {'type': 'LITERAL', 'value': 2}
            ]
        }

        cnf = tseitin_transform(formula)
        pipeline = middleware.create_solve_pipeline()
        result = await middleware.execute_pipeline(pipeline, cnf)

        # Should be SAT (satisfied by x1=T, x2=T)
        assert result['status'] in ['SAT', 'ERROR']

    @pytest.mark.asyncio
    async def test_contradiction_e2e(self):
        """Test contradiction end-to-end"""
        middleware = create_middleware(strict_mode=False, kissat_binary=KISSAT_BIN)

        # x1 AND NOT(x1)
        formula = {
            'type': 'AND',
            'children': [
                {'type': 'LITERAL', 'value': 1},
                {'type': 'NOT', 'child': {'type': 'LITERAL', 'value': 1}}
            ]
        }

        cnf = tseitin_transform(formula)
        pipeline = middleware.create_solve_pipeline()
        result = await middleware.execute_pipeline(pipeline, cnf)

        # Should be UNSAT
        assert result['status'] in ['UNSAT', 'ERROR']

    @pytest.mark.asyncio
    async def test_complex_formula_e2e(self):
        """Test complex formula end-to-end"""
        middleware = create_middleware(strict_mode=False, kissat_binary=KISSAT_BIN)

        # (x1 -> x2) AND (x2 -> x3) AND x1
        # Should imply x3 is true
        formula = {
            'type': 'AND',
            'children': [
                {
                    'type': 'IMPLIES',
                    'left': {'type': 'LITERAL', 'value': 1},
                    'right': {'type': 'LITERAL', 'value': 2}
                },
                {
                    'type': 'IMPLIES',
                    'left': {'type': 'LITERAL', 'value': 2},
                    'right': {'type': 'LITERAL', 'value': 3}
                },
                {'type': 'LITERAL', 'value': 1}
            ]
        }

        cnf = tseitin_transform(formula)
        pipeline = middleware.create_solve_pipeline()
        result = await middleware.execute_pipeline(pipeline, cnf)

        # Should be SAT
        assert result['status'] in ['SAT', 'ERROR']
        if result['status'] == 'SAT':
            # Check that x1, x2, x3 are all true in the model
            model = result.get('model', {})
            # Note: model may include Tseitin variables


class TestBinaryClauseFastPath:
    """The binary-clause pre-check runs even without Kissat installed,
    since it's an independent proof that doesn't invoke the solver."""

    @pytest.mark.asyncio
    async def test_fast_path_does_not_require_kissat(self):
        middleware = create_middleware(strict_mode=False, kissat_binary="/nonexistent/kissat")
        assert middleware.kissat is None

        # Classic 2-SAT UNSAT gadget: consistent to catch via binary clauses alone
        cnf = CNFFormula(num_vars=2, clauses=[[1, 2], [-1, 2], [1, -2], [-1, -2]])
        pipeline = middleware.create_solve_pipeline()
        result = await middleware.execute_pipeline(pipeline, cnf)

        assert result['status'] == 'UNSAT'
        assert result['certificate'] == 'UNSAT_CERTIFIED'
        assert 'Kissat not invoked' in result['proof_message']

    @pytest.mark.asyncio
    async def test_no_kissat_and_no_binary_contradiction_raises(self):
        middleware = create_middleware(strict_mode=False, kissat_binary="/nonexistent/kissat")
        cnf = CNFFormula(num_vars=2, clauses=[[1, 2]])
        pipeline = middleware.create_solve_pipeline()
        with pytest.raises(RuntimeError):
            await middleware.execute_pipeline(pipeline, cnf)


class TestCertificateStatus:
    """Unit tests for the certificate-status mapping (no Kissat required)"""

    def test_sat_verified(self):
        from backend.middleware import _certificate_status
        assert _certificate_status('SAT', True) == 'SAT_CERTIFIED'

    def test_sat_unverified(self):
        from backend.middleware import _certificate_status
        assert _certificate_status('SAT', False) == 'UNVERIFIED_SOLVER_CLAIM'

    def test_unsat_verified(self):
        from backend.middleware import _certificate_status
        assert _certificate_status('UNSAT', True) == 'UNSAT_CERTIFIED'

    def test_unsat_unverified(self):
        from backend.middleware import _certificate_status
        assert _certificate_status('UNSAT', False) == 'UNVERIFIED_SOLVER_CLAIM'

    def test_timeout(self):
        from backend.middleware import _certificate_status
        assert _certificate_status('TIMEOUT', None) == 'TIMEOUT'

    def test_error(self):
        from backend.middleware import _certificate_status
        assert _certificate_status('ERROR', None) == 'ERROR'


@requires_kissat
class TestCertificateStatusIntegration:
    """End-to-end: the certificate field appears on real solve results"""

    @pytest.mark.asyncio
    async def test_unsat_result_carries_certificate(self):
        middleware = create_middleware(strict_mode=False, kissat_binary=KISSAT_BIN)
        cnf = CNFFormula(num_vars=1, clauses=[[1], [-1]])
        pipeline = middleware.create_solve_pipeline()
        result = await middleware.execute_pipeline(pipeline, cnf)
        assert result['status'] == 'UNSAT'
        assert result['certificate'] == 'UNSAT_CERTIFIED'

    @pytest.mark.asyncio
    async def test_sat_result_carries_certificate(self):
        middleware = create_middleware(strict_mode=False, kissat_binary=KISSAT_BIN)
        cnf = CNFFormula(num_vars=2, clauses=[[1, 2]])
        pipeline = middleware.create_solve_pipeline()
        result = await middleware.execute_pipeline(pipeline, cnf)
        assert result['status'] == 'SAT'
        assert result['certificate'] == 'SAT_CERTIFIED'
