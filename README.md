# Lambda SAT Middleware

A math-aligned λ-logic middleware for Boolean satisfiability (SAT) solving with proof certification.

## Overview

Lambda SAT Middleware is a full-stack educational and production SAT solving system that combines:

- **TypeScript/React Frontend** - Interactive educational interface for learning SAT solving
- **Python Backend** - Production-grade λ-middleware with Kissat integration and proof checking
- **Functional Programming** - Lambda calculus DSL for composable solver pipelines
- **Proof Certification** - Model verification (SAT) and DRAT/LRAT proof checking (UNSAT)

## Features

### Frontend (TypeScript/React)
- Interactive CNF formula input and visualization
- Step-by-step DPLL solver visualization
- Lambda middleware configuration UI
- Heuristic and budget selection
- Real-time solver execution
- Educational tooltips and examples

### Backend (Python)
- Typed lambda DSL with effect management
- Kissat SAT solver integration
- Model verification for SAT results
- DRAT/LRAT proof checking for UNSAT results
- Configurable heuristics (VSIDS, LRB, CHB, random)
- Resource budgets (time, memory, conflicts)
- RESTful API for frontend integration

## Quick Start

### Docker (Recommended)

```bash
# Start both frontend and backend
docker-compose up

# Frontend: http://localhost:5173
# Backend API: http://localhost:5001
```

### Local Development

#### Backend

```bash
# Install dependencies (requires Python 3.11+)
cd backend
pip install -r requirements.txt

# Install Kissat and drat-trim (see BACKEND_README.md)

# Run API server
python -m backend.api_server

# Or use CLI
python -m backend.cli examples/simple_sat.cnf --heuristic aggressive
```

#### Frontend

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build
```

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ CNF Input   │  │ Visualization │  │ Lambda Config │      │
│  └─────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST API
┌────────────────────────┴────────────────────────────────────┐
│                   Backend (Python)                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Lambda Middleware Kernel                 │  │
│  │  ┌─────────┐  ┌──────────┐  ┌────────────────┐      │  │
│  │  │ Type    │  │ Effect   │  │ Pipeline       │      │  │
│  │  │ Checker │  │ Handlers │  │ Executor       │      │  │
│  │  └─────────┘  └──────────┘  └────────────────┘      │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│  ┌──────────┐  ┌───────┴──────┐  ┌────────────────┐       │
│  │ Kissat   │  │ Model        │  │ DRAT/LRAT      │       │
│  │ Wrapper  │  │ Verifier     │  │ Checkers       │       │
│  └──────────┘  └──────────────┘  └────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Lambda Pipeline Example

```python
# λ cnf. solve(cnf, heuristic, budget)
pipeline = abs_('cnf',
    effect('solve',
        var('cnf'),
        literal({'branching': 'vsids', 'restarts': 'geometric'}),
        literal({'time_limit': 30, 'memory_limit': 256})
    )
)

# Type check: CNF -> Result
middleware.type_checker.check(pipeline)

# Execute with verification
result = await middleware.execute_pipeline(pipeline, cnf)
```

## Correctness Guarantees

### Trusted Computing Base (TCB)

The minimal trusted components:
1. CNF parser (DIMACS format)
2. Tseitin transformation (formula → equisatisfiable CNF)
3. Model checker (verifies SAT assignments)
4. DRAT/LRAT proof checkers (verifies UNSAT proofs)

**Kissat is NOT in the TCB** - all results are independently verified.

### Certification

- **SAT results** → Model verified against original formula
- **UNSAT results** → DRAT/LRAT proof verified by independent checker

## Examples

### Simple SAT Formula

```
p cnf 3 3
1 2 0
-1 3 0
-2 -3 0
```

Result: **SATISFIABLE**
Model: `x₁=T, x₂=T, x₃=T`

### Simple UNSAT Formula

```
p cnf 2 4
1 0
-1 0
2 0
-2 0
```

Result: **UNSATISFIABLE** (with DRAT proof)

### Pigeonhole Principle (3 → 2)

```
p cnf 6 10
1 2 0     # Pigeon 1 must be in hole 1 or 2
3 4 0     # Pigeon 2 must be in hole 1 or 2
5 6 0     # Pigeon 3 must be in hole 1 or 2
-1 -3 0   # Pigeons 1 and 2 cannot both be in hole 1
...
```

Result: **UNSATISFIABLE** (classical combinatorial example)

## API Reference

### Endpoints

**POST /api/solve-lambda**
```json
{
  "formula": {
    "variables": 3,
    "clauses": [[1, 2], [-1, 3], [-2, -3]]
  },
  "heuristic": "conservative",
  "budget": "standard"
}
```

**POST /api/verify-model**
```json
{
  "cnf": "p cnf 3 3\n1 2 0\n...",
  "model": {"1": true, "2": true, "3": true}
}
```

See [BACKEND_README.md](BACKEND_README.md) for full API documentation.

## Heuristics

- **Conservative** (VSIDS, Geometric restarts) - Default, balanced
- **Aggressive** (LRB, Luby restarts, Vivify) - For hard instances
- **Random** - For experimentation and comparison

## Budgets

- **Quick** (1s, 64MB) - Fast results for simple formulas
- **Standard** (30s, 256MB) - Default for most use cases
- **Thorough** (5m, 1GB) - For challenging instances

## Development

### Project Structure

```
lambda-sat-solver/
├── backend/              # Python middleware
│   ├── lambda_dsl.py    # Lambda calculus DSL
│   ├── cnf_utils.py     # CNF parsing and verification
│   ├── kissat_wrapper.py # Kissat solver integration
│   ├── proof_checking.py # DRAT/LRAT verification
│   ├── middleware.py    # Main kernel
│   ├── api_server.py    # Flask REST API
│   └── cli.py          # Command-line interface
├── src/                 # React frontend
│   ├── App.tsx         # Main application
│   ├── lib/            # Frontend utilities
│   └── components/     # UI components
├── examples/            # Example CNF files
├── Dockerfile          # Backend container
├── Dockerfile.frontend # Frontend container
└── docker-compose.yml  # Full stack orchestration
```

### Running Tests

```bash
# Backend tests
cd backend
python -m pytest tests/

# Frontend tests
npm test
```

### Building

```bash
# Build backend Docker image
docker build -t lambda-sat-backend .

# Build frontend
npm run build

# Build and run full stack
docker-compose up --build
```

## Contributing

Contributions welcome! Please see the issues for planned enhancements:

- [ ] Full Tseitin transformation for arbitrary formulas
- [ ] Quantifier expansion (∀/∃) over finite domains
- [ ] Portfolio solving with parallel execution
- [ ] Benchmarking harness with PAR-2 scoring
- [ ] Extended Kissat configuration options
- [ ] LCF-style certificate generation

## License

MIT License - See LICENSE file for details

## References

- **SATLUTION**: Repo-scale solver evolution research
- **Kissat**: Fast SAT solver by Armin Biere
- **DRAT**: Deletion Resolution Asymmetric Tautology proofs
- **LRAT**: Extended LRAT format for certified proofs

## Acknowledgments

Built with:
- React + TypeScript + Vite
- Python 3.11 + Flask
- Kissat SAT Solver
- Radix UI Components
- TailwindCSS
