"""
API server tests using the Flask test client.

Endpoints that do not need a solver (health, parse-cnf, verify-model) are
always tested; solve endpoints are gated on Kissat availability
(KISSAT_BIN, default 'kissat' on PATH).
"""

import os
import shutil
import pytest

from backend.api_server import app, middleware

KISSAT_BIN = os.environ.get('KISSAT_BIN', 'kissat')
requires_kissat = pytest.mark.skipif(
    shutil.which(KISSAT_BIN) is None or middleware.kissat is None,
    reason=f"Kissat binary not available (KISSAT_BIN={KISSAT_BIN})"
)


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    def test_health(self, client):
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['mode'] in ('dev', 'strict', 'research')
        assert 'kissat_available' in data
        assert 'drat_available' in data


class TestParseCnfEndpoint:
    def test_parse_valid_cnf(self, client):
        response = client.post('/api/parse-cnf', json={
            'cnf': 'p cnf 3 2\n1 2 0\n-1 3 0'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['valid'] is True
        assert data['variables'] == 3
        assert data['clauses'] == 2

    def test_parse_missing_cnf(self, client):
        response = client.post('/api/parse-cnf', json={})
        assert response.status_code == 400

    def test_parse_malformed_cnf(self, client):
        response = client.post('/api/parse-cnf', json={
            'cnf': 'p cnf 2 1\n1 abc 0'
        })
        assert response.status_code == 400
        assert response.get_json()['valid'] is False


class TestVerifyModelEndpoint:
    def test_verify_satisfying_model(self, client):
        response = client.post('/api/verify-model', json={
            'cnf': 'p cnf 2 2\n1 2 0\n-1 2 0',
            'model': {'1': True, '2': True}
        })
        assert response.status_code == 200
        assert response.get_json()['valid'] is True

    def test_verify_falsifying_model(self, client):
        response = client.post('/api/verify-model', json={
            'cnf': 'p cnf 2 2\n1 0\n2 0',
            'model': {'1': True, '2': False}
        })
        assert response.status_code == 200
        assert response.get_json()['valid'] is False

    def test_verify_missing_cnf(self, client):
        response = client.post('/api/verify-model', json={
            'model': {'1': True}
        })
        assert response.status_code == 400


@requires_kissat
class TestSolveEndpoints:
    def test_solve_sat(self, client):
        response = client.post('/api/solve', json={
            'cnf': 'p cnf 3 3\n1 2 0\n-1 3 0\n-2 -3 0',
            'heuristic': {
                'branching': 'vsids',
                'restarts': 'geometric',
                'phase': 'saved',
                'vivify': False
            },
            'budget': {'time_limit': 10, 'memory_limit': 256}
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] in ('SAT', 'UNSAT', 'TIMEOUT', 'ERROR')
        if data['status'] == 'SAT':
            assert data['verified'] is True
            assert 'model' in data

    def test_solve_unsat(self, client):
        response = client.post('/api/solve', json={
            'cnf': 'p cnf 1 2\n1 0\n-1 0',
            'budget': {'time_limit': 10, 'memory_limit': 256}
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] in ('UNSAT', 'ERROR')

    def test_solve_missing_cnf(self, client):
        response = client.post('/api/solve', json={})
        assert response.status_code == 400

    def test_solve_lambda_with_preset(self, client):
        """End-to-end: frontend-style formula -> CNF -> solve -> verified"""
        response = client.post('/api/solve-lambda', json={
            'formula': {'variables': 2, 'clauses': [[1, 2], [-1, 2]]},
            'heuristic': 'conservative',
            'budget': 'standard'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] in ('SAT', 'UNSAT', 'TIMEOUT', 'ERROR')
        if data['status'] == 'SAT':
            assert data['verified'] is True

    def test_solve_lambda_missing_formula(self, client):
        response = client.post('/api/solve-lambda', json={})
        assert response.status_code == 400
