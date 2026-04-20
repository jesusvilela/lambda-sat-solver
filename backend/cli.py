"""
Command-line interface for Lambda SAT Middleware
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .middleware import create_middleware
from .cnf_utils import parse_dimacs, parse_dimacs_file
from .lambda_dsl import abs_, effect, var, literal


async def main():
    parser = argparse.ArgumentParser(
        description='Lambda SAT Middleware - Math-aligned SAT solver with proof certification'
    )

    parser.add_argument(
        'input',
        type=str,
        help='Input CNF file (DIMACS format) or CNF string'
    )

    parser.add_argument(
        '--heuristic',
        type=str,
        choices=['conservative', 'aggressive', 'random'],
        default='conservative',
        help='Heuristic strategy'
    )

    parser.add_argument(
        '--budget',
        type=str,
        choices=['quick', 'standard', 'thorough'],
        default='standard',
        help='Resource budget'
    )

    parser.add_argument(
        '--strict',
        action='store_true',
        help='Require proof verification for UNSAT'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Output file for results (JSON)'
    )

    args = parser.parse_args()

    # Parse input
    input_path = Path(args.input)
    if input_path.exists():
        cnf = parse_dimacs_file(input_path)
        print(f"Loaded CNF from {input_path}")
    else:
        try:
            cnf = parse_dimacs(args.input)
            print("Parsed CNF from command line")
        except Exception as e:
            print(f"Error parsing CNF: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"Formula: {cnf.num_vars} variables, {cnf.num_clauses} clauses")

    # Configure heuristic
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

    heuristic = heuristic_map[args.heuristic]
    budget = budget_map[args.budget]

    print(f"Heuristic: {args.heuristic}")
    print(f"Budget: {args.budget} ({budget['time_limit']}s, {budget['memory_limit']}MB)")
    print()

    # Create middleware
    try:
        middleware = create_middleware(strict_mode=args.strict)
    except RuntimeError as e:
        print(f"Error initializing middleware: {e}", file=sys.stderr)
        print("Make sure Kissat and drat-trim are installed and in PATH")
        sys.exit(1)

    # Create solve pipeline
    pipeline = middleware.create_solve_pipeline(
        heuristic=heuristic,
        budget=budget
    )

    print("Executing solver pipeline...")
    print()

    # Execute pipeline
    try:
        result = await middleware.execute_pipeline(pipeline, cnf)

        # Print results
        print("═" * 60)
        print("RESULT")
        print("═" * 60)
        print(f"Status: {result['status']}")

        if result['status'] == 'SAT':
            print(f"Verified: {result.get('verified', False)}")
            if result.get('model'):
                print(f"Model: {len(result['model'])} assignments")
                # Print first few assignments
                model_items = list(result['model'].items())[:10]
                for var, val in model_items:
                    print(f"  x{var} = {val}")
                if len(result['model']) > 10:
                    print(f"  ... and {len(result['model']) - 10} more")

        elif result['status'] == 'UNSAT':
            print(f"Verified: {result.get('verified', False)}")
            if result.get('proof_message'):
                print(f"Proof: {result['proof_message']}")

        elif result['status'] == 'ERROR':
            print(f"Error: {result.get('message', 'Unknown error')}")

        # Print stats
        if result.get('stats'):
            print()
            print("Statistics:")
            for key, value in result['stats'].items():
                print(f"  {key}: {value}")

        print("═" * 60)

        # Save to output file if specified
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\nResults saved to {output_path}")

        # Exit with appropriate code
        if result['status'] == 'SAT':
            sys.exit(10)  # Standard SAT solver exit code
        elif result['status'] == 'UNSAT':
            sys.exit(20)  # Standard UNSAT exit code
        else:
            sys.exit(1)

    except Exception as e:
        print(f"Error executing pipeline: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
