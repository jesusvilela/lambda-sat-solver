"""
Command-line interface for benchmarking SAT solvers
"""

import argparse
import asyncio
import sys
from pathlib import Path

from .benchmark import BenchmarkHarness, BenchmarkInstance, discover_benchmarks
from .portfolio import PortfolioConfig, create_custom_portfolio
from .kissat_wrapper import Heuristic, Budget


async def main():
    parser = argparse.ArgumentParser(
        description='SAT Solver Benchmarking Harness'
    )

    parser.add_argument(
        'benchmark_dir',
        type=Path,
        help='Directory containing benchmark instances'
    )

    parser.add_argument(
        '--pattern',
        nargs='+',
        default=['*.cnf', '*.xz', '*.lzma'],
        help='File patterns to match (default: *.cnf *.xz *.lzma)'
    )

    parser.add_argument(
        '--timeout',
        type=float,
        default=300.0,
        help='Timeout per instance in seconds (default: 300)'
    )

    parser.add_argument(
        '--memory',
        type=int,
        default=2048,
        help='Memory limit in MB (default: 2048)'
    )

    parser.add_argument(
        '--configs',
        type=int,
        default=4,
        help='Number of solver configurations to test (default: 4)'
    )

    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Run instances in parallel (within each config)'
    )

    parser.add_argument(
        '--output-csv',
        type=Path,
        help='Export results to CSV file'
    )

    parser.add_argument(
        '--output-json',
        type=Path,
        help='Export results to JSON file'
    )

    parser.add_argument(
        '--compare',
        nargs=2,
        metavar=('CONFIG1', 'CONFIG2'),
        help='Compare two configurations'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of instances to run'
    )

    args = parser.parse_args()

    # Validate benchmark directory
    if not args.benchmark_dir.exists():
        print(f"Error: Benchmark directory not found: {args.benchmark_dir}", file=sys.stderr)
        sys.exit(1)

    # Discover benchmarks
    print(f"Discovering benchmarks in {args.benchmark_dir}...")
    instances = discover_benchmarks(args.benchmark_dir, args.pattern)

    if not instances:
        print(f"Error: No benchmark instances found matching pattern '{args.pattern}'", file=sys.stderr)
        sys.exit(1)

    # Limit instances if requested
    if args.limit:
        instances = instances[:args.limit]

    print(f"Found {len(instances)} instances")

    # Create configurations
    configs = create_custom_portfolio(args.timeout, args.configs)

    print(f"\nTesting {len(configs)} configurations:")
    for config in configs:
        print(f"  - {config.name}: {config.description}")

    # Create harness
    harness = BenchmarkHarness(
        timeout=args.timeout,
        memory_limit=args.memory
    )

    # Run benchmark
    print(f"\n{'='*80}")
    print("Starting benchmark...")
    print(f"{'='*80}\n")

    try:
        results = await harness.run_benchmark(
            instances=instances,
            configs=configs,
            parallel=args.parallel
        )

        # Generate report
        print(f"\n{harness.generate_report()}")

        # Export results
        if args.output_csv:
            harness.export_csv(args.output_csv)

        if args.output_json:
            harness.export_json(args.output_json)

        # Compare configurations if requested
        if args.compare:
            config1, config2 = args.compare
            comparison = harness.compare_configs(config1, config2)

            print(f"\n{'='*80}")
            print(f"HEAD-TO-HEAD COMPARISON: {config1} vs {config2}")
            print(f"{'='*80}")

            if 'error' in comparison:
                print(f"Error: {comparison['error']}")
            else:
                print(f"Common instances: {comparison['common_instances']}")
                print(f"Wins for {config1}: {comparison['wins_config1']}")
                print(f"Wins for {config2}: {comparison['wins_config2']}")
                print(f"Ties: {comparison['ties']}")
                print(f"Mean speedup: {comparison['mean_speedup']:.2f}x")
                print(f"PAR-2 {config1}: {comparison['par2_config1']:.2f}s")
                print(f"PAR-2 {config2}: {comparison['par2_config2']:.2f}s")
                if comparison['par2_improvement'] is not None:
                    print(f"PAR-2 improvement: {comparison['par2_improvement']:.1f}%")

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nError during benchmark: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
