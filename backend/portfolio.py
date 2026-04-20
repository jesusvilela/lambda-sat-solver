"""
Portfolio SAT Solving

Runs multiple solver configurations in parallel and returns the first successful result.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import time

from .cnf_utils import CNFFormula
from .kissat_wrapper import KissatWrapper, Heuristic, Budget, SolverResult
from .proof_checking import DRATChecker


@dataclass
class PortfolioConfig:
    """Configuration for portfolio solver"""
    name: str
    heuristic: Heuristic
    budget: Budget
    description: str = ""


class PortfolioSolver:
    """
    Portfolio SAT solver that runs multiple configurations in parallel

    The portfolio approach runs different heuristic configurations simultaneously
    and returns the first result. This is effective because different heuristics
    perform better on different problem instances.
    """

    def __init__(
        self,
        kissat_binary: str = "kissat",
        drat_trim_binary: str = "drat-trim",
        max_parallel: int = 4
    ):
        """
        Initialize portfolio solver

        Args:
            kissat_binary: Path to Kissat binary
            drat_trim_binary: Path to drat-trim binary
            max_parallel: Maximum number of parallel solvers to run
        """
        self.kissat = KissatWrapper(kissat_binary)
        self.drat_checker = DRATChecker(drat_trim_binary)
        self.max_parallel = max_parallel

    def get_default_portfolio(self) -> List[PortfolioConfig]:
        """
        Get default portfolio configurations

        Returns diverse set of heuristics covering different search strategies:
        - Conservative (VSIDS): Good for structured problems
        - Aggressive (LRB): Good for hard combinatorial problems
        - Random: Good for breaking symmetries
        - CHB: Good for industrial problems
        """
        return [
            PortfolioConfig(
                name="conservative",
                heuristic=Heuristic(
                    branching='vsids',
                    restarts='geometric',
                    phase='saved',
                    vivify=False
                ),
                budget=Budget(time_limit=300, memory_limit=512),
                description="VSIDS branching with geometric restarts"
            ),
            PortfolioConfig(
                name="aggressive",
                heuristic=Heuristic(
                    branching='lrb',
                    restarts='luby',
                    phase='false',
                    vivify=True
                ),
                budget=Budget(time_limit=300, memory_limit=512),
                description="LRB branching with Luby restarts and vivification"
            ),
            PortfolioConfig(
                name="random",
                heuristic=Heuristic(
                    branching='random',
                    restarts='fixed',
                    phase='random',
                    vivify=False
                ),
                budget=Budget(time_limit=300, memory_limit=512),
                description="Random branching for symmetry breaking"
            ),
            PortfolioConfig(
                name="chb",
                heuristic=Heuristic(
                    branching='chb',
                    restarts='geometric',
                    phase='saved',
                    vivify=True
                ),
                budget=Budget(time_limit=300, memory_limit=512),
                description="CHB branching for industrial problems"
            )
        ]

    async def _solve_with_config(
        self,
        cnf: CNFFormula,
        config: PortfolioConfig,
        produce_proof: bool = True
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Solve with a single configuration

        Args:
            cnf: CNF formula to solve
            config: Portfolio configuration
            produce_proof: Whether to produce proof for UNSAT

        Returns:
            Tuple of (config_name, result_dict)
        """
        start_time = time.time()

        try:
            result = self.kissat.solve(cnf, config.heuristic, config.budget, produce_proof)

            solve_time = time.time() - start_time

            return (config.name, {
                'status': result.result.name,
                'config': config.name,
                'time': solve_time,
                'model': result.model,
                'proof_path': str(result.proof_path) if result.proof_path else None,
                'stats': result.stats,
                'description': config.description
            })

        except Exception as e:
            return (config.name, {
                'status': 'ERROR',
                'config': config.name,
                'error': str(e),
                'time': time.time() - start_time
            })

    async def solve_portfolio(
        self,
        cnf: CNFFormula,
        configs: Optional[List[PortfolioConfig]] = None,
        return_first: bool = True,
        verify_proofs: bool = False
    ) -> Dict[str, Any]:
        """
        Solve using portfolio approach

        Args:
            cnf: CNF formula to solve
            configs: List of configurations to try (default: use default portfolio)
            return_first: If True, return as soon as first solver finishes
            verify_proofs: If True, verify UNSAT proofs before returning

        Returns:
            Result dictionary with status, winning config, and all results
        """
        if configs is None:
            configs = self.get_default_portfolio()

        # Limit number of parallel solvers
        configs = configs[:self.max_parallel]

        print(f"Running portfolio with {len(configs)} configurations...")

        start_time = time.time()

        # Create tasks for all configurations
        tasks = [
            asyncio.create_task(self._solve_with_config(cnf, config))
            for config in configs
        ]

        results = []
        winning_config = None
        winning_result = None

        if return_first:
            # Wait for first successful result
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            # Cancel remaining tasks
            for task in pending:
                task.cancel()

            # Get first result
            for task in done:
                config_name, result = await task
                if result['status'] in ['SAT', 'UNSAT']:
                    winning_config = config_name
                    winning_result = result
                    break

            # Try to get any other completed results
            try:
                for task in pending:
                    try:
                        await asyncio.wait_for(task, timeout=0.1)
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        pass
            except Exception:
                pass

        else:
            # Wait for all configurations to complete
            all_results = await asyncio.gather(*tasks, return_exceptions=True)
            for config_name, result in all_results:
                results.append(result)
                if result['status'] in ['SAT', 'UNSAT'] and winning_config is None:
                    winning_config = config_name
                    winning_result = result

        total_time = time.time() - start_time

        # Verify proof if requested and result is UNSAT
        if verify_proofs and winning_result and winning_result['status'] == 'UNSAT':
            if winning_result.get('proof_path'):
                proof_path = Path(winning_result['proof_path'])
                if proof_path.exists():
                    proof_check = self.drat_checker.check_proof(cnf, proof_path)
                    winning_result['proof_verified'] = proof_check.valid
                    winning_result['proof_message'] = proof_check.message

        return {
            'status': winning_result['status'] if winning_result else 'UNKNOWN',
            'winning_config': winning_config,
            'winning_result': winning_result,
            'total_time': total_time,
            'num_configs': len(configs),
            'all_results': results if not return_first else [winning_result] if winning_result else []
        }

    async def solve_sequential(
        self,
        cnf: CNFFormula,
        configs: Optional[List[PortfolioConfig]] = None,
        max_time_per_config: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Solve using sequential portfolio (try each config in order until one succeeds)

        Args:
            cnf: CNF formula to solve
            configs: List of configurations to try
            max_time_per_config: Maximum time per configuration

        Returns:
            Result dictionary
        """
        if configs is None:
            configs = self.get_default_portfolio()

        start_time = time.time()

        for i, config in enumerate(configs):
            print(f"Trying configuration {i+1}/{len(configs)}: {config.name}")

            # Adjust budget if max_time_per_config specified
            budget = config.budget
            if max_time_per_config:
                budget = Budget(
                    time_limit=min(config.budget.time_limit, max_time_per_config),
                    memory_limit=config.budget.memory_limit,
                    conflict_limit=config.budget.conflict_limit
                )

            config_name, result = await self._solve_with_config(
                cnf,
                PortfolioConfig(
                    name=config.name,
                    heuristic=config.heuristic,
                    budget=budget,
                    description=config.description
                )
            )

            if result['status'] in ['SAT', 'UNSAT']:
                total_time = time.time() - start_time
                return {
                    'status': result['status'],
                    'winning_config': config_name,
                    'winning_result': result,
                    'total_time': total_time,
                    'configs_tried': i + 1,
                    'num_configs': len(configs)
                }

        total_time = time.time() - start_time
        return {
            'status': 'UNKNOWN',
            'winning_config': None,
            'winning_result': None,
            'total_time': total_time,
            'configs_tried': len(configs),
            'num_configs': len(configs)
        }


def create_custom_portfolio(
    time_budget: float,
    num_configs: int = 4
) -> List[PortfolioConfig]:
    """
    Create custom portfolio with given time budget

    Args:
        time_budget: Total time budget to split among configs
        num_configs: Number of configurations

    Returns:
        List of portfolio configurations
    """
    time_per_config = time_budget / num_configs

    configs = [
        PortfolioConfig(
            name=f"vsids_{i}",
            heuristic=Heuristic(
                branching='vsids',
                restarts='geometric',
                phase='saved' if i % 2 == 0 else 'false',
                vivify=False
            ),
            budget=Budget(time_limit=time_per_config, memory_limit=512),
            description=f"VSIDS variant {i}"
        )
        for i in range(num_configs // 2)
    ]

    configs.extend([
        PortfolioConfig(
            name=f"lrb_{i}",
            heuristic=Heuristic(
                branching='lrb',
                restarts='luby' if i % 2 == 0 else 'geometric',
                phase='false',
                vivify=True
            ),
            budget=Budget(time_limit=time_per_config, memory_limit=512),
            description=f"LRB variant {i}"
        )
        for i in range(num_configs - num_configs // 2)
    ])

    return configs
