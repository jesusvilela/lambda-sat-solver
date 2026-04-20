"""
Benchmarking harness for SAT solvers

Supports:
- Multiple benchmark instances
- Multiple solver configurations
- PAR-2 scoring (penalized average runtime)
- Result aggregation and reporting
- CSV export
"""

import asyncio
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import statistics

from .cnf_utils import CNFFormula, parse_dimacs_file
from .kissat_wrapper import KissatWrapper, Heuristic, Budget, SolverResult
from .portfolio import PortfolioConfig, PortfolioSolver


@dataclass
class BenchmarkInstance:
    """Single benchmark instance"""
    name: str
    path: Path
    expected_result: Optional[str] = None  # 'SAT' or 'UNSAT' if known
    category: str = "unknown"


@dataclass
class BenchmarkResult:
    """Result for a single instance/config pair"""
    instance_name: str
    config_name: str
    status: str  # 'SAT', 'UNSAT', 'TIMEOUT', 'ERROR'
    runtime: float  # seconds
    memory_used: Optional[float] = None  # MB
    conflicts: Optional[int] = None
    decisions: Optional[int] = None
    verified: bool = False
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)


class BenchmarkHarness:
    """
    Benchmarking harness for SAT solvers

    Runs multiple solver configurations on multiple instances and
    computes aggregate statistics including PAR-2 scores.
    """

    def __init__(
        self,
        kissat_binary: str = "kissat",
        timeout: float = 300.0,
        memory_limit: int = 2048
    ):
        """
        Initialize benchmark harness

        Args:
            kissat_binary: Path to Kissat binary
            timeout: Default timeout in seconds
            memory_limit: Memory limit in MB
        """
        self.kissat = KissatWrapper(kissat_binary)
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.results: List[BenchmarkResult] = []

    async def run_single(
        self,
        instance: BenchmarkInstance,
        config: PortfolioConfig
    ) -> BenchmarkResult:
        """
        Run single instance with single configuration

        Args:
            instance: Benchmark instance
            config: Solver configuration

        Returns:
            Benchmark result
        """
        print(f"Running {instance.name} with {config.name}...", end=' ', flush=True)

        start_time = time.time()

        try:
            # Parse CNF
            cnf = parse_dimacs_file(instance.path)

            # Run solver
            result = self.kissat.solve(
                cnf,
                config.heuristic,
                config.budget,
                produce_proof=False  # Skip proof for benchmarking speed
            )

            runtime = time.time() - start_time

            # Extract stats
            stats = result.stats or {}

            benchmark_result = BenchmarkResult(
                instance_name=instance.name,
                config_name=config.name,
                status=result.result.name,
                runtime=runtime,
                memory_used=stats.get('memory_mb'),
                conflicts=stats.get('conflicts'),
                decisions=stats.get('decisions'),
                verified=False  # Could add model verification here
            )

            print(f"{result.result.name} in {runtime:.2f}s")
            return benchmark_result

        except Exception as e:
            runtime = time.time() - start_time
            print(f"ERROR: {str(e)}")
            return BenchmarkResult(
                instance_name=instance.name,
                config_name=config.name,
                status='ERROR',
                runtime=runtime,
                error_message=str(e)
            )

    async def run_benchmark(
        self,
        instances: List[BenchmarkInstance],
        configs: List[PortfolioConfig],
        parallel: bool = False
    ) -> List[BenchmarkResult]:
        """
        Run full benchmark suite

        Args:
            instances: List of benchmark instances
            configs: List of solver configurations
            parallel: If True, run instances in parallel (one config at a time)

        Returns:
            List of benchmark results
        """
        results = []

        for config in configs:
            print(f"\n{'='*60}")
            print(f"Configuration: {config.name} - {config.description}")
            print(f"{'='*60}")

            if parallel:
                # Run all instances in parallel for this config
                tasks = [
                    self.run_single(instance, config)
                    for instance in instances
                ]
                config_results = await asyncio.gather(*tasks)
                results.extend(config_results)
            else:
                # Run instances sequentially
                for instance in instances:
                    result = await self.run_single(instance, config)
                    results.append(result)

        self.results = results
        return results

    def compute_par2_score(
        self,
        config_name: str,
        timeout_penalty: Optional[float] = None
    ) -> float:
        """
        Compute PAR-2 score for a configuration

        PAR-2 (Penalized Average Runtime) counts timeouts as 2x the timeout value.
        This penalizes solvers that time out while still giving credit for solved instances.

        Args:
            config_name: Configuration name
            timeout_penalty: Timeout penalty multiplier (default: 2.0)

        Returns:
            PAR-2 score (lower is better)
        """
        if timeout_penalty is None:
            timeout_penalty = 2.0

        config_results = [r for r in self.results if r.config_name == config_name]

        if not config_results:
            return float('inf')

        total_time = 0.0
        for result in config_results:
            if result.status in ['SAT', 'UNSAT']:
                total_time += result.runtime
            elif result.status == 'TIMEOUT':
                total_time += self.timeout * timeout_penalty
            else:  # ERROR
                total_time += self.timeout * timeout_penalty

        return total_time / len(config_results)

    def compute_statistics(self, config_name: str) -> Dict[str, Any]:
        """
        Compute detailed statistics for a configuration

        Args:
            config_name: Configuration name

        Returns:
            Dictionary of statistics
        """
        config_results = [r for r in self.results if r.config_name == config_name]

        if not config_results:
            return {}

        solved = [r for r in config_results if r.status in ['SAT', 'UNSAT']]
        timeouts = [r for r in config_results if r.status == 'TIMEOUT']
        errors = [r for r in config_results if r.status == 'ERROR']

        solve_times = [r.runtime for r in solved]

        stats = {
            'config_name': config_name,
            'total_instances': len(config_results),
            'solved': len(solved),
            'timeouts': len(timeouts),
            'errors': len(errors),
            'solve_rate': len(solved) / len(config_results) if config_results else 0.0,
            'par2_score': self.compute_par2_score(config_name),
        }

        if solve_times:
            stats.update({
                'mean_time': statistics.mean(solve_times),
                'median_time': statistics.median(solve_times),
                'min_time': min(solve_times),
                'max_time': max(solve_times),
                'stdev_time': statistics.stdev(solve_times) if len(solve_times) > 1 else 0.0
            })

        return stats

    def generate_report(self) -> str:
        """
        Generate human-readable benchmark report

        Returns:
            Report string
        """
        if not self.results:
            return "No benchmark results available."

        # Get unique configs
        configs = sorted(set(r.config_name for r in self.results))

        report = []
        report.append("=" * 80)
        report.append("BENCHMARK REPORT")
        report.append("=" * 80)
        report.append("")

        # Summary table
        report.append("Summary:")
        report.append("-" * 80)
        report.append(f"{'Config':<20} {'Solved':<10} {'Timeouts':<10} {'Errors':<10} {'PAR-2':<12}")
        report.append("-" * 80)

        config_stats = []
        for config in configs:
            stats = self.compute_statistics(config)
            config_stats.append(stats)
            report.append(
                f"{stats['config_name']:<20} "
                f"{stats['solved']:<10} "
                f"{stats['timeouts']:<10} "
                f"{stats['errors']:<10} "
                f"{stats['par2_score']:<12.2f}"
            )

        report.append("-" * 80)
        report.append("")

        # Detailed statistics
        report.append("Detailed Statistics:")
        report.append("-" * 80)

        for stats in config_stats:
            report.append(f"\n{stats['config_name']}:")
            report.append(f"  Total instances: {stats['total_instances']}")
            report.append(f"  Solved: {stats['solved']} ({stats['solve_rate']*100:.1f}%)")
            report.append(f"  Timeouts: {stats['timeouts']}")
            report.append(f"  Errors: {stats['errors']}")
            report.append(f"  PAR-2 score: {stats['par2_score']:.2f}s")

            if 'mean_time' in stats:
                report.append(f"  Mean solve time: {stats['mean_time']:.2f}s")
                report.append(f"  Median solve time: {stats['median_time']:.2f}s")
                report.append(f"  Min solve time: {stats['min_time']:.2f}s")
                report.append(f"  Max solve time: {stats['max_time']:.2f}s")
                if stats.get('stdev_time'):
                    report.append(f"  Std dev: {stats['stdev_time']:.2f}s")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

    def export_csv(self, output_path: Path) -> None:
        """
        Export results to CSV

        Args:
            output_path: Path to output CSV file
        """
        if not self.results:
            print("No results to export")
            return

        with open(output_path, 'w') as f:
            # Header
            f.write("instance,config,status,runtime,memory_mb,conflicts,decisions,verified,error\n")

            # Results
            for result in self.results:
                f.write(
                    f"{result.instance_name},"
                    f"{result.config_name},"
                    f"{result.status},"
                    f"{result.runtime:.4f},"
                    f"{result.memory_used or ''},"
                    f"{result.conflicts or ''},"
                    f"{result.decisions or ''},"
                    f"{result.verified},"
                    f"{result.error_message or ''}\n"
                )

        print(f"Results exported to {output_path}")

    def export_json(self, output_path: Path) -> None:
        """
        Export results to JSON

        Args:
            output_path: Path to output JSON file
        """
        if not self.results:
            print("No results to export")
            return

        data = {
            'results': [r.to_dict() for r in self.results],
            'statistics': [
                self.compute_statistics(config)
                for config in sorted(set(r.config_name for r in self.results))
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Results exported to {output_path}")

    def compare_configs(self, config1: str, config2: str) -> Dict[str, Any]:
        """
        Compare two configurations head-to-head

        Args:
            config1: First configuration name
            config2: Second configuration name

        Returns:
            Comparison statistics
        """
        results1 = {r.instance_name: r for r in self.results if r.config_name == config1}
        results2 = {r.instance_name: r for r in self.results if r.config_name == config2}

        common_instances = set(results1.keys()) & set(results2.keys())

        if not common_instances:
            return {'error': 'No common instances found'}

        wins1 = 0
        wins2 = 0
        ties = 0

        speedups = []

        for instance in common_instances:
            r1 = results1[instance]
            r2 = results2[instance]

            # Only compare solved instances
            if r1.status in ['SAT', 'UNSAT'] and r2.status in ['SAT', 'UNSAT']:
                if r1.runtime < r2.runtime * 0.99:  # 1% threshold for ties
                    wins1 += 1
                    speedups.append(r2.runtime / r1.runtime)
                elif r2.runtime < r1.runtime * 0.99:
                    wins2 += 1
                    speedups.append(r1.runtime / r2.runtime)
                else:
                    ties += 1

        stats1 = self.compute_statistics(config1)
        stats2 = self.compute_statistics(config2)

        return {
            'config1': config1,
            'config2': config2,
            'common_instances': len(common_instances),
            'wins_config1': wins1,
            'wins_config2': wins2,
            'ties': ties,
            'mean_speedup': statistics.mean(speedups) if speedups else 1.0,
            'par2_config1': stats1.get('par2_score'),
            'par2_config2': stats2.get('par2_score'),
            'par2_improvement': (
                (stats1['par2_score'] - stats2['par2_score']) / stats1['par2_score'] * 100
                if stats1.get('par2_score') and stats2.get('par2_score')
                else None
            )
        }


def discover_benchmarks(directory: Path, pattern: str = "*.cnf") -> List[BenchmarkInstance]:
    """
    Discover benchmark instances in a directory

    Args:
        directory: Directory to search
        pattern: File pattern to match (default: *.cnf)

    Returns:
        List of benchmark instances
    """
    instances = []

    for path in directory.rglob(pattern):
        # Try to infer category from directory structure
        category = path.parent.name if path.parent != directory else "unknown"

        # Try to infer expected result from filename
        expected = None
        if 'sat' in path.stem.lower() and 'unsat' not in path.stem.lower():
            expected = 'SAT'
        elif 'unsat' in path.stem.lower():
            expected = 'UNSAT'

        instances.append(BenchmarkInstance(
            name=path.stem,
            path=path,
            expected_result=expected,
            category=category
        ))

    return instances
