"""
Evaluation runner for the Lambda SAT solver.

Runs an EvalSuite against a solver function and produces a SuiteReport.

Usage (library):
    from backend.eval import StandardSuites
    from backend.eval.runner import run_suite

    suite = StandardSuites.quick()
    report = await run_suite(suite, solver_fn, timeout=10.0, solver_config="vsids")
    print(report)

Usage (CLI):
    python -m backend.eval.runner --suite quick --config conservative
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional

from ..cnf_utils import CNFFormula, verify_model
from .metrics import EvalResult, SuiteReport, summarize_results
from .suite import EvalInstance, EvalSuite


# ---------------------------------------------------------------------------
# Solver function protocol
# ---------------------------------------------------------------------------

# A solver function takes a CNFFormula and optional kwargs, and returns a dict:
# {
#     'status': 'SAT' | 'UNSAT' | 'TIMEOUT' | 'ERROR',
#     'model': Optional[Dict[int, bool]],        # for SAT
#     'verified': Optional[bool],
#     'stats': Optional[dict],
#     'message': Optional[str],
# }
SolverFn = Callable[..., Coroutine[Any, Any, Dict[str, Any]]]


# ---------------------------------------------------------------------------
# Run a single instance
# ---------------------------------------------------------------------------

async def run_instance(
    instance: EvalInstance,
    solver_fn: SolverFn,
    timeout: float,
    solver_config: str = "default",
    **solver_kwargs: Any,
) -> EvalResult:
    """
    Run solver_fn on a single EvalInstance and return an EvalResult.

    Args:
        instance: The EvalInstance to run.
        solver_fn: Async callable (formula, **kwargs) → result dict.
        timeout: Wall-clock timeout in seconds.
        solver_config: Name of the solver config (for reporting).
        **solver_kwargs: Extra arguments forwarded to solver_fn.

    Returns:
        EvalResult with timing, status, and correctness info.
    """
    start = time.monotonic()
    status = "ERROR"
    correct = None
    verified = False
    conflicts = None
    decisions = None
    memory_mb = None
    error_message = None

    try:
        result = await asyncio.wait_for(
            solver_fn(instance.formula, **solver_kwargs),
            timeout=timeout,
        )
        status = result.get("status", "ERROR")
        verified = result.get("verified", False)
        stats = result.get("stats") or {}
        conflicts = stats.get("conflicts")
        decisions = stats.get("decisions")
        memory_mb = stats.get("memory_mb")
        error_message = result.get("message") or result.get("error")

        # Verify model if SAT and model is available
        if status == "SAT" and result.get("model") and not verified:
            verified = verify_model(instance.formula, result["model"])

    except asyncio.TimeoutError:
        status = "TIMEOUT"
    except Exception as exc:
        status = "ERROR"
        error_message = str(exc)

    runtime = time.monotonic() - start

    # Check correctness against known expected answer
    if instance.expected != "UNKNOWN" and status in ("SAT", "UNSAT"):
        correct = status == instance.expected

    return EvalResult(
        instance_name=instance.name,
        category=instance.category,
        status=status,
        expected=instance.expected,
        runtime=runtime,
        correct=correct,
        verified=verified,
        num_vars=instance.formula.num_vars,
        num_clauses=instance.formula.num_clauses,
        solver_config=solver_config,
        conflicts=conflicts,
        decisions=decisions,
        memory_mb=memory_mb,
        error_message=error_message,
    )


# ---------------------------------------------------------------------------
# Run a full suite
# ---------------------------------------------------------------------------

async def run_suite(
    suite: EvalSuite,
    solver_fn: SolverFn,
    timeout: Optional[float] = None,
    solver_config: str = "default",
    parallel: bool = False,
    max_parallel: int = 4,
    verbose: bool = False,
    **solver_kwargs: Any,
) -> SuiteReport:
    """
    Run solver_fn on every instance in suite and return a SuiteReport.

    Args:
        suite: The EvalSuite to run.
        solver_fn: Async callable (formula, **kwargs) → result dict.
        timeout: Per-instance timeout; defaults to suite.timeout.
        solver_config: Name of the solver config (for reporting).
        parallel: If True, run instances concurrently.
        max_parallel: Maximum concurrent solves when parallel=True.
        verbose: If True, print progress to stdout.
        **solver_kwargs: Extra arguments forwarded to solver_fn.

    Returns:
        SuiteReport with aggregated metrics.
    """
    if timeout is None:
        timeout = suite.timeout

    results: List[EvalResult] = []

    if parallel:
        semaphore = asyncio.Semaphore(max_parallel)

        async def bounded(inst: EvalInstance) -> EvalResult:
            async with semaphore:
                r = await run_instance(inst, solver_fn, timeout, solver_config, **solver_kwargs)
                if verbose:
                    _print_progress(r, suite)
                return r

        results = await asyncio.gather(
            *[bounded(inst) for inst in suite.instances]
        )
    else:
        for i, inst in enumerate(suite.instances):
            r = await run_instance(inst, solver_fn, timeout, solver_config, **solver_kwargs)
            results.append(r)
            if verbose:
                _print_progress(r, suite, index=i + 1, total=len(suite.instances))

    return summarize_results(results, timeout, solver_config=solver_config, suite_name=suite.name)


def _print_progress(
    result: EvalResult,
    suite: EvalSuite,
    index: Optional[int] = None,
    total: Optional[int] = None,
) -> None:
    prefix = f"[{index}/{total}] " if index is not None else ""
    verdict = result.status
    if result.correct is False:
        verdict += " (WRONG!)"
    print(
        f"{prefix}{result.instance_name}: {verdict} in {result.runtime:.3f}s"
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

async def _cli_main() -> None:
    import argparse
    import sys
    from pathlib import Path

    from .suite import StandardSuites

    parser = argparse.ArgumentParser(description="Lambda SAT Solver Evaluation Runner")
    parser.add_argument(
        "--suite",
        choices=["quick", "medium", "full", "hardness"],
        default="quick",
        help="Evaluation suite to run (default: quick)",
    )
    parser.add_argument(
        "--config",
        default="conservative",
        help="Solver configuration name (default: conservative)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Per-instance timeout override (seconds)",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run instances in parallel",
    )
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=4,
        help="Maximum parallel solves (default: 4)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-instance progress",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write JSON report to this file",
    )
    args = parser.parse_args()

    # Load suite
    suite_map = {
        "quick": StandardSuites.quick,
        "medium": StandardSuites.medium,
        "full": StandardSuites.full,
        "hardness": StandardSuites.hardness,
    }
    suite = suite_map[args.suite]()
    print(f"Suite: {suite.name} ({len(suite)} instances)")
    print(f"Categories: {suite.categories()}")
    print()

    # Import middleware
    try:
        from ..middleware import create_middleware
        mw = create_middleware(strict_mode=False)
    except Exception as exc:
        print(f"Failed to initialise middleware: {exc}", file=sys.stderr)
        sys.exit(1)

    # Map config name → heuristic / budget dicts
    heuristic_map = {
        "conservative": {
            "branching": "vsids",
            "restarts": "luby",
            "phase": "saved",
            "vivify": False,
        },
        "aggressive": {
            "branching": "vmtf",
            "restarts": "luby",
            "phase": "false",
            "vivify": True,
        },
        "default": {
            "branching": "vmtf",
            "restarts": "block",
            "phase": "saved",
            "vivify": True,
        },
    }
    heuristic = heuristic_map.get(args.config, heuristic_map["default"])
    budget = {"time_limit": int(args.timeout or suite.timeout), "memory_limit": 1024}

    pipeline = mw.create_solve_pipeline(heuristic=heuristic, budget=budget)

    async def solver_fn(formula: CNFFormula) -> dict:
        return await mw.execute_pipeline(pipeline, formula)

    report = await run_suite(
        suite,
        solver_fn,
        timeout=args.timeout,
        solver_config=args.config,
        parallel=args.parallel,
        max_parallel=args.max_parallel,
        verbose=args.verbose,
    )

    print("\n" + "=" * 60)
    print(report)
    print("=" * 60)

    if args.output:
        import json
        import dataclasses

        def _serialise(obj):
            if dataclasses.is_dataclass(obj):
                return dataclasses.asdict(obj)
            raise TypeError(f"Not serialisable: {type(obj)}")

        with open(args.output, "w") as fh:
            json.dump(dataclasses.asdict(report), fh, indent=2, default=_serialise)
        print(f"\nReport written to {args.output}")


if __name__ == "__main__":
    asyncio.run(_cli_main())
