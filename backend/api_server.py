"""
Flask API server for Lambda SAT Middleware

Provides REST API endpoints for the frontend to interact with the backend
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
import os
import tempfile
import asyncio
from functools import wraps

from .middleware import create_middleware, CERTIFICATION_MODES
from .cnf_utils import parse_dimacs, CNFFormula
from .kissat_wrapper import Heuristic, Budget


app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Certification mode is configurable via environment:
#   dev      - solve even if proof tools are missing (default, development)
#   strict   - refuse to start without Kissat/drat-trim; refuse uncertified
#              UNSAT results (production / "proof certification" promise)
#   research - dev behavior plus raw Kissat output in responses
CERTIFICATION_MODE = os.environ.get('LAMBDA_SAT_MODE', 'dev').lower()
if CERTIFICATION_MODE not in CERTIFICATION_MODES:
    raise ValueError(
        f"Invalid LAMBDA_SAT_MODE={CERTIFICATION_MODE!r}. "
        f"Expected one of {CERTIFICATION_MODES}"
    )

middleware = create_middleware(mode=CERTIFICATION_MODE)


def async_route(f):
    """Decorator to run async functions in Flask routes"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '0.1.0',
        'mode': middleware.mode,
        'kissat_available': middleware.kissat is not None,
        'drat_available': middleware.drat_checker is not None,
        'lrat_available': middleware.lrat_checker is not None
    })


@app.route('/api/solve', methods=['POST'])
@async_route
async def solve():
    """
    Solve a CNF formula

    Request body:
    {
        "cnf": "p cnf 3 3\\n1 2 0\\n-1 3 0\\n-2 -3 0",
        "heuristic": {
            "branching": "vsids",
            "restarts": "geometric",
            "phase": "saved",
            "vivify": false
        },
        "budget": {
            "time_limit": 30,
            "memory_limit": 256
        }
    }

    Response:
    {
        "status": "SAT" | "UNSAT" | "TIMEOUT" | "ERROR",
        "model": {...},  // if SAT
        "verified": true,
        "stats": {...}
    }
    """
    try:
        data = request.json

        # Parse CNF
        cnf_text = data.get('cnf')
        if not cnf_text:
            return jsonify({'error': 'No CNF provided'}), 400

        cnf = parse_dimacs(cnf_text)

        # Get heuristic and budget
        heuristic_data = data.get('heuristic', {})
        budget_data = data.get('budget', {})

        # Create and execute pipeline
        pipeline = middleware.create_solve_pipeline(
            heuristic=heuristic_data,
            budget=budget_data
        )

        result = await middleware.execute_pipeline(pipeline, cnf)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'error': str(e)
        }), 500


@app.route('/api/solve-lambda', methods=['POST'])
@async_route
async def solve_lambda():
    """
    Solve using lambda middleware with formula conversion

    This endpoint supports the TypeScript frontend by accepting
    the same format and providing lambda middleware execution
    """
    try:
        data = request.json

        # Support both direct CNF and formula objects
        if 'cnf' in data:
            cnf = parse_dimacs(data['cnf'])
        elif 'formula' in data:
            # Convert from frontend format
            formula_data = data['formula']
            cnf = CNFFormula(
                num_vars=formula_data.get('variables', 0),
                clauses=formula_data.get('clauses', [])
            )
        else:
            return jsonify({'error': 'No formula provided'}), 400

        # Get configuration
        heuristic_name = data.get('heuristic', 'conservative')
        budget_name = data.get('budget', 'standard')

        # Map to heuristic configs
        heuristic_map = {
            'conservative': {
                'branching': 'vsids',
                'restarts': 'geometric',
                'phase': 'saved',
                'vivify': False
            },
            'aggressive': {
                'branching': 'lrb',
                'restarts': 'luby',
                'phase': 'false',
                'vivify': True
            },
            'random': {
                'branching': 'random',
                'restarts': 'fixed',
                'phase': 'random',
                'vivify': False
            }
        }

        budget_map = {
            'quick': {'time_limit': 1, 'memory_limit': 64},
            'standard': {'time_limit': 30, 'memory_limit': 256},
            'thorough': {'time_limit': 300, 'memory_limit': 1024}
        }

        heuristic = heuristic_map.get(heuristic_name, heuristic_map['conservative'])
        budget = budget_map.get(budget_name, budget_map['standard'])

        # Create and execute pipeline
        pipeline = middleware.create_solve_pipeline(
            heuristic=heuristic,
            budget=budget
        )

        result = await middleware.execute_pipeline(pipeline, cnf)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'message': str(e)
        }), 500


@app.route('/api/verify-model', methods=['POST'])
@async_route
async def verify_model():
    """
    Verify a model against a CNF formula

    Request body:
    {
        "cnf": "p cnf 3 3\\n...",
        "model": {"1": true, "2": false, "3": true}
    }
    """
    try:
        data = request.json

        cnf_text = data.get('cnf')
        if not cnf_text:
            return jsonify({'error': 'No CNF provided'}), 400

        cnf = parse_dimacs(cnf_text)

        model_data = data.get('model', {})
        # Convert string keys to integers
        model = {int(k): v for k, v in model_data.items()}

        # Verify
        from .cnf_utils import verify_model
        is_valid = verify_model(cnf, model)

        return jsonify({
            'valid': is_valid,
            'message': 'Model satisfies formula' if is_valid else 'Model does not satisfy formula'
        })

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/parse-cnf', methods=['POST'])
def parse_cnf():
    """
    Parse and validate DIMACS CNF

    Request body:
    {
        "cnf": "p cnf 3 3\\n1 2 0\\n..."
    }
    """
    try:
        data = request.json
        cnf_text = data.get('cnf')

        if not cnf_text:
            return jsonify({'error': 'No CNF provided'}), 400

        cnf = parse_dimacs(cnf_text)

        return jsonify({
            'valid': True,
            'variables': cnf.num_vars,
            'clauses': len(cnf.clauses),
            'formula': cnf.to_dict()
        })

    except Exception as e:
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 400


def run_server(host='127.0.0.1', port=5001, debug=True):
    """Run the API server"""
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║   Lambda SAT Middleware API Server                       ║
║   Version: 0.1.0                                          ║
╠═══════════════════════════════════════════════════════════╣
║   Server running at: http://{host}:{port}             ║
║   Health check: http://{host}:{port}/health          ║
║                                                           ║
║   Certification mode: {middleware.mode:>8}                          ║
║   Kissat available: {str(middleware.kissat is not None):>5}                           ║
║   DRAT checker available: {str(middleware.drat_checker is not None):>5}               ║
║   LRAT checker available: {str(middleware.lrat_checker is not None):>5}               ║
╚═══════════════════════════════════════════════════════════╝
    """)
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server()
