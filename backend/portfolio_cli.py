"""
Command-line interface for portfolio SAT solving
"""

import argparse
import asyncio
import sys
import json
from pathlib import Path

from .portfolio import PortfolioSolver, PortfolioConfig, create_custom_portfolio
from .cnf_utils import parse_dimacs_file


async def main():
    parser = argparse.ArgumentParser(
        description='Portfolio SAT Solver - Run multiple configurations in parallel'
    )

    parser.add_argument(
        'input',
        type=Path,
        help='Input CNF file'
    )

    parser.add_argument(
        '--mode',
        choices=['parallel', 'sequential'],
        default='parallel',
        help='Solving mode (default: parallel)'
    )

    parser.add_argument(
        '--configs',
        type=int,
        default=4,
        help='Number of configurations to use (default: 4)'
    )

    parser.add_argument(
        '--timeout',
        type=float,
        default=300.0,
        help='Timeout per configuration in seconds (default: 300)'
    )

    parser.add_argument(
        '--return-first',
        action='store_true',
        help='Return as soon as first solver finishes (parallel mode only)'
    )

    parser.add_argument(
        '--verify-proofs',
        action='store_true',
        help='Verify UNSAT proofs'
    )

    parser.add_argument(
        '--output',
        type=Path,
        help='Output file for results (JSON format)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Validate input file
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Parse CNF
    try:
        cnf = parse_dimacs_file(args.input)
        print(f"Loaded CNF: {cnf.num_vars} variables, {cnf.num_clauses} clauses")
    except Exception as e:
        print(f"Error parsing CNF: {e}", file=sys.stderr)
        sys.exit(1)

    # Create portfolio solver
    try:
        solver = PortfolioSolver(max_parallel=args.configs)
    except Exception as e:
        print(f"Error initializing solver: {e}", file=sys.stderr)
        sys.exit(1)

    # Create configurations
    configs = create_custom_portfolio(args.timeout, args.configs)

    if args.verbose:
        print(f"\nConfigurations:")
        for config in configs:
            print(f"  {config.name}: {config.description}")
        print()

    # Solve
    try:
        if args.mode == 'parallel':
            result = await solver.solve_portfolio(
                cnf,
                configs=configs,
                return_first=args.return_first,
                verify_proofs=args.verify_proofs
            )
        else:
            result = await solver.solve_sequential(
                cnf,
                configs=configs,
                max_time_per_config=args.timeout
            )

        # Print result
        print(f"\nStatus: {result['status']}")
        if result['winning_config']:
            print(f"Winning configuration: {result['winning_config']}")
        print(f"Total time: {result['total_time']:.2f}s")

        if result['status'] == 'SAT' and result.get('winning_result'):
            model = result['winning_result'].get('model')
            if model and args.verbose:
                print(f"\nModel (first 10 vars):")
                for var in sorted(model.keys())[:10]:
                    print(f"  x{var} = {model[var]}")

        # Save to output file if requested
        if args.output:
            with open(args.output, 'w') as f:
                # Convert Path objects to strings for JSON serialization
                result_copy = result.copy()
                if 'winning_result' in result_copy and result_copy['winning_result']:
                    if 'proof_path' in result_copy['winning_result']:
                        result_copy['winning_result']['proof_path'] = str(
                            result_copy['winning_result']['proof_path']
                        )
                json.dump(result_copy, f, indent=2)
            print(f"\nResults saved to {args.output}")

        # Exit code
        if result['status'] == 'SAT':
            sys.exit(10)
        elif result['status'] == 'UNSAT':
            sys.exit(20)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"Error during solving: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
