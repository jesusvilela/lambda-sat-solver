# Lambda SAT Middleware - Backend

A math-aligned λ-logic middleware that transforms formulas into CNF, solves with Kissat, and certifies results through model replay (SAT) or DRAT/LRAT proof checking (UNSAT).

## Architecture

### Core Components

1. **Lambda DSL** (`lambda_dsl.py`)
   - Typed lambda calculus with effect tracking
   - Expression types: Var, App, Abs, Effect, Literal
   - Type checker ensures correctness before execution
   - Evaluator with effect handlers

2. **CNF Utilities** (`cnf_utils.py`)
   - DIMACS CNF parser and writer
   - Model verification against formulas
   - Tseitin transformation (placeholder for full implementation)

3. **Kissat Wrapper** (`kissat_wrapper.py`)
   - Subprocess wrapper for Kissat SAT solver
   - Heuristic configuration (VSIDS, LRB, CHB, random branching)
   - Budget management (time, memory, conflicts)
   - DRAT proof generation for UNSAT results

4. **Proof Checking** (`proof_checking.py`)
   - DRAT proof verification via drat-trim
   - LRAT proof verification via lrat-check
   - Certified UNSAT results

5. **Middleware Kernel** (`middleware.py`)
   - Integrates all components
   - Effect handlers for I/O operations
   - Type-checked pipeline execution
   - Strict mode for mandatory proof verification

6. **API Server** (`api_server.py`)
   - Flask REST API for frontend integration
   - CORS enabled for cross-origin requests
   - Async route handlers
   - Health check endpoint

## Installation

### Prerequisites

- Python 3.11+
- Kissat SAT solver
- drat-trim proof checker
- (Optional) lrat-check for LRAT proofs

### Installing Kissat

```bash
git clone https://github.com/arminbiere/kissat.git
cd kissat
./configure
make
sudo cp build/kissat /usr/local/bin/
```

### Installing drat-trim

```bash
git clone https://github.com/marijnheule/drat-trim.git
cd drat-trim
make
sudo cp drat-trim /usr/local/bin/
```

### Installing Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Usage

### Command-Line Interface

```bash
# Solve a CNF file with default settings
python -m backend.cli examples/simple_sat.cnf

# Use aggressive heuristics with thorough budget
python -m backend.cli examples/pigeonhole_3_2.cnf \
  --heuristic aggressive \
  --budget thorough \
  --strict

# Save results to JSON
python -m backend.cli examples/simple_unsat.cnf \
  --output results.json
```

### API Server

```bash
# Start the API server
python -m backend.api_server

# Server will run on http://localhost:5001
```

#### API Endpoints

**Health Check**
```bash
GET /health
```

**Solve CNF Formula**
```bash
POST /api/solve
Content-Type: application/json

{
  "cnf": "p cnf 3 3\n1 2 0\n-1 3 0\n-2 -3 0",
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
```

**Solve with Lambda Middleware (Frontend Compatible)**
```bash
POST /api/solve-lambda
Content-Type: application/json

{
  "formula": {
    "variables": 3,
    "clauses": [[1, 2], [-1, 3], [-2, -3]]
  },
  "heuristic": "conservative",
  "budget": "standard"
}
```

**Verify Model**
```bash
POST /api/verify-model
Content-Type: application/json

{
  "cnf": "p cnf 3 3\n1 2 0\n-1 3 0\n-2 -3 0",
  "model": {"1": true, "2": true, "3": true}
}
```

### Python API

```python
import asyncio
from backend.middleware import create_middleware
from backend.cnf_utils import parse_dimacs

# Create middleware
middleware = create_middleware(strict_mode=False)

# Parse CNF
cnf = parse_dimacs("p cnf 3 3\n1 2 0\n-1 3 0\n-2 -3 0")

# Create solve pipeline
pipeline = middleware.create_solve_pipeline(
    heuristic={'branching': 'vsids', 'restarts': 'geometric', 'phase': 'saved', 'vivify': False},
    budget={'time_limit': 30, 'memory_limit': 256}
)

# Execute
result = asyncio.run(middleware.execute_pipeline(pipeline, cnf))
print(result)
```

## Heuristic Configurations

### Conservative (Default)
- Branching: VSIDS (Variable State Independent Decaying Sum)
- Restarts: Geometric progression
- Phase: Saved (use previously saved phases)
- Vivify: Disabled

### Aggressive
- Branching: LRB (Learning Rate Based)
- Restarts: Luby sequence
- Phase: False bias
- Vivify: Enabled

### Random
- Branching: Random
- Restarts: Fixed interval
- Phase: Random
- Vivify: Disabled

## Budget Configurations

### Quick
- Time limit: 1 second
- Memory limit: 64 MB

### Standard (Default)
- Time limit: 30 seconds
- Memory limit: 256 MB

### Thorough
- Time limit: 300 seconds (5 minutes)
- Memory limit: 1024 MB (1 GB)

## Trusted Computing Base (TCB)

The minimal trusted components:

1. **CNF Parser** - Parses DIMACS format
2. **Tseitin Transformation** - Converts formulas to equisatisfiable CNF
3. **Model Checker** - Verifies SAT results by checking assignments
4. **DRAT/LRAT Checkers** - Verify UNSAT proofs
5. **Effect Handlers** - Controlled I/O operations

The SAT solver (Kissat) is NOT in the TCB - results are always verified.

## Correctness Theorem

For any λ-formula Φ:

**If** `T(Φ) = ψ` (CNF produced by Tseitin+projection)

**Then:**
- Kissat returns SAT ⇒ ∃ assignment A to top variables such that A satisfies Φ (verified by model replay)
- Kissat returns UNSAT ⇒ DRAT/LRAT proof P is a valid refutation of ψ (verified by proof checker), hence Φ is unsatisfiable

## Development

### Running Tests

```bash
# TODO: Add test suite
python -m pytest backend/tests/
```

### Code Structure

```
backend/
├── __init__.py           # Package initialization
├── lambda_dsl.py         # Lambda calculus DSL
├── cnf_utils.py          # CNF parsing and utilities
├── kissat_wrapper.py     # Kissat solver wrapper
├── proof_checking.py     # DRAT/LRAT proof checkers
├── middleware.py         # Main middleware kernel
├── api_server.py         # Flask API server
├── cli.py               # Command-line interface
└── requirements.txt      # Python dependencies
```

## Docker Deployment

```bash
# Build the container
docker build -t lambda-sat-middleware .

# Run the API server
docker run -p 5001:5001 lambda-sat-middleware

# Or use docker-compose for full stack
docker-compose up
```

## Known Limitations (MVP)

1. **Tseitin transformation** - Currently only accepts CNF input; full formula transformation is a placeholder
2. **Heuristic flags** - Some Kissat flags are examples and may need adjustment for actual Kissat version
3. **LRAT support** - Kissat doesn't natively produce LRAT; requires conversion from DRAT
4. **Distributed execution** - No support for distributed solving yet
5. **LCF-style certification** - Future work for formal proof generation

## Future Enhancements

1. Full Tseitin transformation for arbitrary propositional formulas
2. Quantifier expansion for ∀/∃ over finite domains
3. Higher-order λ-term erasure (β-reduction to first-order)
4. Portfolio solving with parallel execution
5. Incremental solving support
6. Memory profiling and slicing
7. Extended solver flags (vivify, eliminate, simplify)
8. LCF certificate path for clausification

## License

MIT License - See LICENSE file for details

## References

- Kissat: https://github.com/arminbiere/kissat
- DRAT-trim: https://github.com/marijnheule/drat-trim
- LRAT specification: https://www.cs.utexas.edu/~marijn/publications/lrat.pdf
