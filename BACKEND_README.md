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
   - **Full Tseitin transformation** supporting AND, OR, NOT, IMPLIES, IFF, XOR

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

6. **Portfolio Solver** (`portfolio.py`)
   - Parallel execution of multiple solver configurations
   - Sequential fallback mode
   - Configurable heuristic portfolios
   - First-result or exhaustive solving modes

7. **Benchmarking Harness** (`benchmark.py`)
   - Comprehensive benchmarking suite
   - PAR-2 (Penalized Average Runtime) scoring
   - Head-to-head configuration comparison
   - CSV and JSON export
   - Detailed statistical analysis

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
  --mode strict

# Save results to JSON
python -m backend.cli examples/simple_unsat.cnf \
  --output results.json
```

### Python API

```python
import asyncio
from backend.middleware import create_middleware
from backend.cnf_utils import parse_dimacs

# Create middleware ('dev', 'strict' or 'research' certification mode)
middleware = create_middleware(mode='dev')

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
# Run all tests
python -m pytest backend/tests/ -v

# Run specific test files
python -m pytest backend/tests/test_tseitin.py -v
python -m pytest backend/tests/test_cnf_utils.py -v
python -m pytest backend/tests/test_integration.py -v

# Run with coverage
python -m pytest backend/tests/ --cov=backend --cov-report=html
```

### Test Suite

The project includes comprehensive tests covering:
- **Tseitin Transformation** (20 tests)
  - All logical operators (AND, OR, NOT, IMPLIES, IFF, XOR)
  - Complex nested formulas
  - Edge cases and error handling
  - Correctness properties

- **CNF Utilities** (27 tests)
  - DIMACS parsing and writing
  - Model verification
  - Edge cases (large variables, empty formulas, etc.)
  - Format validation

- **Integration Tests** (15 tests)
  - End-to-end solving workflows
  - Tseitin + solving integration
  - Heuristic configurations
  - Tseitin end-to-end and the GF(2)/2-SAT fast paths

### Code Structure

```
backend/
├── __init__.py           # Package initialization
├── lambda_dsl.py         # Lambda calculus DSL
├── cnf_utils.py          # CNF parsing and Tseitin transformation
├── kissat_wrapper.py     # Kissat solver wrapper
├── proof_checking.py     # DRAT/LRAT proof checkers
├── middleware.py         # Main middleware kernel
├── cli.py                # Command-line interface
├── portfolio.py          # Portfolio solver
├── portfolio_cli.py      # Portfolio CLI
├── binary_clause_check.py # sound 2-SAT UNSAT fast-path
├── xor_extraction.py     # sound GF(2)/XOR UNSAT fast-path
├── benchmark.py          # Benchmarking harness
├── benchmark_cli.py      # Benchmarking CLI
├── complexity/           # intrinsic-invariant hardness ladder + contracts
├── requirements.txt      # Python dependencies
└── tests/                # the full test suite
```

## Docker Deployment

```bash
# Build the container (Kissat + drat-trim + the Python library)
docker build -t lambda-sat-middleware .

# Run the CLI in the container
docker run --rm lambda-sat-middleware \
  python -m backend.cli examples/simple_sat.cnf
```

## New Features (v2.0)

### Tseitin Transformation
Full implementation supporting arbitrary propositional formulas:
- **Operators**: AND, OR, NOT, IMPLIES, IFF, XOR
- **Optimization**: Subformula sharing via memoization
- **Correctness**: Equisatisfiable CNF with minimal variables

Example usage:
```python
from backend.cnf_utils import tseitin_transform

# (x1 AND x2) OR (x3 IMPLIES x4)
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
            'type': 'IMPLIES',
            'left': {'type': 'LITERAL', 'value': 3},
            'right': {'type': 'LITERAL', 'value': 4}
        }
    ]
}

cnf = tseitin_transform(formula)
```

### Portfolio Solving
Run multiple heuristic configurations in parallel:

```bash
# Parallel portfolio solving
python -m backend.portfolio_cli examples/hard_problem.cnf \
  --mode parallel \
  --configs 4 \
  --timeout 300 \
  --return-first

# Sequential portfolio solving
python -m backend.portfolio_cli examples/hard_problem.cnf \
  --mode sequential \
  --configs 4
```

### Benchmarking Harness
Comprehensive benchmarking with PAR-2 scoring:

```bash
# Run benchmark suite
python -m backend.benchmark_cli benchmarks/ \
  --timeout 300 \
  --configs 4 \
  --parallel \
  --output-csv results.csv \
  --output-json results.json

# Compare two configurations
python -m backend.benchmark_cli benchmarks/ \
  --configs 4 \
  --compare vsids_0 lrb_0
```

Features:
- PAR-2 (Penalized Average Runtime) scoring
- Head-to-head configuration comparison
- Detailed statistics (mean, median, std dev)
- CSV and JSON export
- Parallel and sequential modes

## Known Limitations

1. **Heuristic flags** - Some Kissat flags are examples and may need adjustment for actual Kissat version
2. **LRAT support** - Kissat doesn't natively produce LRAT; requires conversion from DRAT
3. **Distributed execution** - No support for distributed solving yet
4. **LCF-style certification** - Future work for formal proof generation

## Future Enhancements

1. ✅ ~~Full Tseitin transformation for arbitrary propositional formulas~~ **DONE**
2. ✅ ~~Portfolio solving with parallel execution~~ **DONE**
3. ✅ ~~Benchmarking harness with PAR-2 scoring~~ **DONE**
4. ✅ ~~Comprehensive test suite~~ **DONE**
5. Quantifier expansion for ∀/∃ over finite domains
6. Higher-order λ-term erasure (β-reduction to first-order)
7. Incremental solving support
8. Memory profiling and slicing
9. Extended solver flags (vivify, eliminate, simplify)
10. LCF certificate path for clausification
11. Distributed solving with work-stealing
12. CDCL learning clause analysis

## License

MIT License - See LICENSE file for details

## References

- Kissat: https://github.com/arminbiere/kissat
- DRAT-trim: https://github.com/marijnheule/drat-trim
- LRAT specification: https://www.cs.utexas.edu/~marijn/publications/lrat.pdf
