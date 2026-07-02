"""
Evaluation metrics for SAT solver benchmarking.

Primary metrics (SAT Competition standard):
  - PAR-2: Penalized Average Runtime.  Unsolved instances count as 2× timeout.
  - Solve rate: Fraction of instances solved within timeout.
  - Correctness rate: Fraction of solved instances with verified correct answers.

Secondary metrics:
  - Mean / median / p90 / p99 solve time (for solved instances only).
  - Cactus-plot data (sorted runtimes for survival curves).
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class EvalResult:
    """
    Result for a single solver run on a single CNF instance.

    Attributes:
        instance_name: Human-readable instance identifier.
        category: Problem family (e.g. 'random-3sat', 'pigeonhole').
        status: 'SAT', 'UNSAT', 'TIMEOUT', 'ERROR'.
        expected: Known expected answer, or 'UNKNOWN'.
        runtime: Wall-clock time in seconds.
        correct: True if status matches expected (None when expected='UNKNOWN').
        verified: True if model/proof was independently verified.
        num_vars: Number of variables.
        num_clauses: Number of clauses.
        solver_config: Name of the solver configuration used.
        conflicts: Solver-reported conflict count (if available).
        decisions: Solver-reported decision count (if available).
        memory_mb: Peak memory usage in MB (if available).
        error_message: Error description if status='ERROR'.
    """

    instance_name: str
    category: str
    status: str
    expected: str
    runtime: float
    correct: Optional[bool] = None
    verified: bool = False
    num_vars: int = 0
    num_clauses: int = 0
    solver_config: str = "default"
    conflicts: Optional[int] = None
    decisions: Optional[int] = None
    memory_mb: Optional[float] = None
    error_message: Optional[str] = None

    def __post_init__(self) -> None:
        if self.expected != "UNKNOWN" and self.status in ("SAT", "UNSAT"):
            self.correct = self.status == self.expected


def compute_par2(
    results: List[EvalResult],
    timeout: float,
    penalty_multiplier: float = 2.0,
) -> float:
    """
    Compute PAR-k (Penalized Average Runtime) score.

    Solved instances contribute their actual runtime; unsolved instances
    (TIMEOUT, ERROR) contribute `timeout × penalty_multiplier`.

    Lower is better.

    Args:
        results: List of eval results.
        timeout: Timeout value used for runs (seconds).
        penalty_multiplier: Multiplier for unsolved instances (default 2 = PAR-2).

    Returns:
        PAR-2 score; float('inf') if results is empty.
    """
    if not results:
        return float("inf")

    total = 0.0
    for r in results:
        if r.status in ("SAT", "UNSAT"):
            total += r.runtime
        else:
            total += timeout * penalty_multiplier

    return total / len(results)


def compute_solve_rate(results: List[EvalResult]) -> float:
    """
    Fraction of instances solved (SAT or UNSAT) within the time limit.

    Args:
        results: List of eval results.

    Returns:
        Solve rate in [0, 1].
    """
    if not results:
        return 0.0
    solved = sum(1 for r in results if r.status in ("SAT", "UNSAT"))
    return solved / len(results)


def compute_correctness_rate(results: List[EvalResult]) -> Optional[float]:
    """
    Fraction of solved instances whose answer matches the known expected answer.

    Instances with expected='UNKNOWN' are excluded.

    Args:
        results: List of eval results.

    Returns:
        Correctness rate in [0, 1], or None if no instances have a known answer.
    """
    checkable = [
        r for r in results
        if r.status in ("SAT", "UNSAT") and r.expected != "UNKNOWN"
    ]
    if not checkable:
        return None
    correct = sum(1 for r in checkable if r.correct)
    return correct / len(checkable)


def compute_verification_rate(results: List[EvalResult]) -> float:
    """
    Fraction of solved instances whose answer was independently verified.

    Args:
        results: List of eval results.

    Returns:
        Verification rate in [0, 1].
    """
    solved = [r for r in results if r.status in ("SAT", "UNSAT")]
    if not solved:
        return 0.0
    return sum(1 for r in solved if r.verified) / len(solved)


def _percentile(sorted_data: List[float], p: float) -> float:
    """Return p-th percentile of sorted_data (nearest-rank method)."""
    if not sorted_data:
        return 0.0
    k = max(0, min(len(sorted_data) - 1, int(len(sorted_data) * p / 100)))
    return sorted_data[k]


def compute_time_stats(results: List[EvalResult]) -> Dict[str, float]:
    """
    Compute runtime statistics for solved instances.

    Args:
        results: List of eval results.

    Returns:
        Dict with keys: mean, median, stdev, min, max, p90, p99.
        Returns empty dict if no instances were solved.
    """
    runtimes = sorted(r.runtime for r in results if r.status in ("SAT", "UNSAT"))
    if not runtimes:
        return {}

    return {
        "mean": statistics.mean(runtimes),
        "median": statistics.median(runtimes),
        "stdev": statistics.stdev(runtimes) if len(runtimes) > 1 else 0.0,
        "min": runtimes[0],
        "max": runtimes[-1],
        "p90": _percentile(runtimes, 90),
        "p99": _percentile(runtimes, 99),
    }


def cactus_data(results: List[EvalResult]) -> List[float]:
    """
    Return sorted runtimes of solved instances (for cactus plot).

    The i-th value is the time to solve the (i+1)-th easiest instance.
    This allows comparing solver configurations on the same set of instances.

    Args:
        results: List of eval results.

    Returns:
        Sorted list of runtimes for solved instances.
    """
    return sorted(r.runtime for r in results if r.status in ("SAT", "UNSAT"))


@dataclass
class SuiteReport:
    """Aggregated evaluation report for a solver on a suite."""

    solver_config: str
    suite_name: str
    total_instances: int
    solved: int
    timeouts: int
    errors: int
    solve_rate: float
    par2: float
    correctness_rate: Optional[float]
    verification_rate: float
    time_stats: Dict[str, float]
    per_category: Dict[str, "CategoryReport"] = field(default_factory=dict)

    def __str__(self) -> str:
        lines = [
            f"Suite: {self.suite_name}  Config: {self.solver_config}",
            f"  Instances : {self.total_instances}",
            f"  Solved    : {self.solved} ({self.solve_rate*100:.1f}%)",
            f"  Timeouts  : {self.timeouts}",
            f"  Errors    : {self.errors}",
            f"  PAR-2     : {self.par2:.3f}s",
        ]
        if self.correctness_rate is not None:
            lines.append(f"  Correct   : {self.correctness_rate*100:.1f}%")
        lines.append(f"  Verified  : {self.verification_rate*100:.1f}%")
        if self.time_stats:
            lines.append(
                f"  Time      : mean={self.time_stats['mean']:.3f}s "
                f"median={self.time_stats['median']:.3f}s "
                f"p90={self.time_stats['p90']:.3f}s"
            )
        for cat, rep in self.per_category.items():
            lines.append(f"  [{cat}] solved={rep.solved}/{rep.total} par2={rep.par2:.3f}s")
        return "\n".join(lines)


@dataclass
class CategoryReport:
    """Per-category breakdown within a suite report."""

    category: str
    total: int
    solved: int
    par2: float
    correctness_rate: Optional[float]


def summarize_results(
    results: List[EvalResult],
    timeout: float,
    solver_config: str = "default",
    suite_name: str = "unnamed",
) -> SuiteReport:
    """
    Compute a full SuiteReport from a list of EvalResults.

    Args:
        results: List of eval results for this solver × suite combination.
        timeout: Timeout used during the eval run (seconds).
        solver_config: Name of the solver configuration.
        suite_name: Name of the eval suite.

    Returns:
        Populated SuiteReport.
    """
    solved = sum(1 for r in results if r.status in ("SAT", "UNSAT"))
    timeouts = sum(1 for r in results if r.status == "TIMEOUT")
    errors = sum(1 for r in results if r.status == "ERROR")

    # Per-category breakdown
    categories: Dict[str, List[EvalResult]] = {}
    for r in results:
        categories.setdefault(r.category, []).append(r)

    per_category = {}
    for cat, cat_results in categories.items():
        cat_solved = sum(1 for r in cat_results if r.status in ("SAT", "UNSAT"))
        cat_par2 = compute_par2(cat_results, timeout)
        cat_corr = compute_correctness_rate(cat_results)
        per_category[cat] = CategoryReport(
            category=cat,
            total=len(cat_results),
            solved=cat_solved,
            par2=cat_par2,
            correctness_rate=cat_corr,
        )

    return SuiteReport(
        solver_config=solver_config,
        suite_name=suite_name,
        total_instances=len(results),
        solved=solved,
        timeouts=timeouts,
        errors=errors,
        solve_rate=compute_solve_rate(results),
        par2=compute_par2(results, timeout),
        correctness_rate=compute_correctness_rate(results),
        verification_rate=compute_verification_rate(results),
        time_stats=compute_time_stats(results),
        per_category=per_category,
    )
