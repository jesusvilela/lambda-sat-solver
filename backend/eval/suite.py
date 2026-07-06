"""
Standard evaluation suites for the Lambda SAT solver.

Each EvalSuite is a named collection of (CNFFormula, expected_result, category)
triples that can be used to measure solver correctness and performance.

Predefined suites
-----------------
StandardSuites.quick   – 30 tiny instances, finishes in < 1 s; for CI/smoke tests.
StandardSuites.medium  – 100 instances spanning all families, default for dev.
StandardSuites.full    – 500 instances for performance regression tracking.
StandardSuites.hardness – Phase-transition 3-SAT for hardness profiling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from ..cnf_utils import CNFFormula
from .generators import (
    graph_coloring,
    ladder_encoding,
    mutilated_chessboard,
    pigeonhole,
    random_ksat,
    xor_chain,
)


@dataclass
class EvalInstance:
    """A single instance in an evaluation suite."""

    name: str
    formula: CNFFormula
    expected: str          # 'SAT', 'UNSAT', or 'UNKNOWN'
    category: str
    difficulty: str = "medium"   # 'easy', 'medium', 'hard'


@dataclass
class EvalSuite:
    """
    A named collection of evaluation instances.

    Attributes:
        name: Human-readable suite name.
        description: What the suite tests.
        timeout: Default per-instance timeout in seconds.
        instances: List of EvalInstance objects.
    """

    name: str
    description: str
    timeout: float
    instances: List[EvalInstance] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.instances)

    def categories(self) -> List[str]:
        """Return unique categories in the suite."""
        return sorted({i.category for i in self.instances})

    def filter_by_category(self, category: str) -> "EvalSuite":
        """Return a new suite containing only instances from `category`."""
        return EvalSuite(
            name=f"{self.name}/{category}",
            description=f"{self.description} [{category}]",
            timeout=self.timeout,
            instances=[i for i in self.instances if i.category == category],
        )

    def filter_by_difficulty(self, difficulty: str) -> "EvalSuite":
        """Return a new suite containing only instances of given difficulty."""
        return EvalSuite(
            name=f"{self.name}/{difficulty}",
            description=f"{self.description} [{difficulty}]",
            timeout=self.timeout,
            instances=[i for i in self.instances if i.difficulty == difficulty],
        )


# ---------------------------------------------------------------------------
# Suite builder helpers
# ---------------------------------------------------------------------------

def _random_sat_batch(
    base_name: str,
    configs: List[Tuple[int, int, int, int]],  # (n, m, k, seed)
    label: str = "random-ksat",
    difficulty: str = "medium",
) -> List[EvalInstance]:
    instances = []
    for n, m, k, seed in configs:
        formula, expected = random_ksat(n, m, k=k, seed=seed)
        instances.append(EvalInstance(
            name=f"{base_name}_n{n}_m{m}_seed{seed}",
            formula=formula,
            expected=expected,
            category=label,
            difficulty=difficulty,
        ))
    return instances


def _pigeonhole_batch(
    ns: List[int],
    difficulty_map: Optional[dict] = None,
) -> List[EvalInstance]:
    if difficulty_map is None:
        difficulty_map = {}
    instances = []
    for n in ns:
        formula, expected = pigeonhole(n)
        diff = difficulty_map.get(n, "medium")
        instances.append(EvalInstance(
            name=f"php_{n}_{n-1}",
            formula=formula,
            expected=expected,
            category="pigeonhole",
            difficulty=diff,
        ))
    return instances


def _xor_batch(
    configs: List[Tuple[int, bool, int]],  # (n, sat, seed)
) -> List[EvalInstance]:
    instances = []
    for n, sat, seed in configs:
        formula, expected = xor_chain(n, expected_sat=sat, seed=seed)
        diff = "easy" if n <= 20 else ("medium" if n <= 100 else "hard")
        instances.append(EvalInstance(
            name=f"xor_n{n}_{'sat' if sat else 'unsat'}_seed{seed}",
            formula=formula,
            expected=expected,
            category="xor-chain",
            difficulty=diff,
        ))
    return instances


def _coloring_batch(
    configs: List[Tuple[int, int, float, int]],  # (v, k, p, seed)
) -> List[EvalInstance]:
    instances = []
    for v, k, p, seed in configs:
        formula, expected = graph_coloring(v, k, edge_probability=p, seed=seed)
        instances.append(EvalInstance(
            name=f"coloring_v{v}_k{k}_p{int(p*100)}_seed{seed}",
            formula=formula,
            expected=expected,
            category="graph-coloring",
            difficulty="medium",
        ))
    return instances


def _ladder_batch(
    configs: List[Tuple[int, int]],  # (n, seed)
) -> List[EvalInstance]:
    instances = []
    for n, seed in configs:
        formula, expected = ladder_encoding(n, seed=seed)
        instances.append(EvalInstance(
            name=f"ladder_n{n}_seed{seed}",
            formula=formula,
            expected=expected,
            category="ladder",
            difficulty="easy",
        ))
    return instances


# ---------------------------------------------------------------------------
# Predefined suites
# ---------------------------------------------------------------------------

class StandardSuites:
    """Factory for predefined evaluation suites."""

    @staticmethod
    def quick() -> EvalSuite:
        """
        30 tiny instances for smoke testing / CI.
        All instances should solve in < 0.1 s on any modern SAT solver.
        """
        suite = EvalSuite(
            name="quick",
            description="Smoke test suite: 30 tiny instances across all families",
            timeout=10.0,
        )

        # Tiny random 3-SAT (well below phase transition → almost always SAT)
        suite.instances += _random_sat_batch(
            "r3sat_easy",
            [(10, 20, 3, s) for s in range(5)],
            label="random-3sat",
            difficulty="easy",
        )
        # Slightly harder (near phase transition)
        suite.instances += _random_sat_batch(
            "r3sat_pt",
            [(20, 86, 3, s) for s in range(5)],   # ratio ≈ 4.3
            label="random-3sat",
            difficulty="medium",
        )
        # Pigeonhole (small, always UNSAT)
        suite.instances += _pigeonhole_batch(
            [3, 4, 5],
            difficulty_map={3: "easy", 4: "easy", 5: "medium"},
        )
        # XOR chains (guaranteed known answer)
        suite.instances += _xor_batch(
            [(10, True, s) for s in range(5)] + [(10, False, s) for s in range(5)]
        )
        # Ladder (always SAT)
        suite.instances += _ladder_batch([(20, s) for s in range(5)])
        # Tiny graph coloring
        suite.instances += _coloring_batch([(6, 3, 0.4, s) for s in range(2)])

        return suite

    @staticmethod
    def medium() -> EvalSuite:
        """
        ~100 instances for routine performance regression tracking.
        Mix of easy, medium and hard instances across all problem families.
        Default timeout: 60 s per instance.
        """
        suite = EvalSuite(
            name="medium",
            description="Medium eval suite: ~100 instances, all families",
            timeout=60.0,
        )

        # Random 3-SAT at/near phase transition
        suite.instances += _random_sat_batch(
            "r3sat_n50",
            [(50, int(50 * 4.267), 3, s) for s in range(10)],
            label="random-3sat",
            difficulty="medium",
        )
        suite.instances += _random_sat_batch(
            "r3sat_n100",
            [(100, int(100 * 4.267), 3, s) for s in range(10)],
            label="random-3sat",
            difficulty="hard",
        )
        # Random 4-SAT
        suite.instances += _random_sat_batch(
            "r4sat_n40",
            [(40, int(40 * 9.93), 4, s) for s in range(5)],
            label="random-4sat",
            difficulty="medium",
        )

        # Pigeonhole (n = 4..8)
        suite.instances += _pigeonhole_batch(
            list(range(4, 9)),
            difficulty_map={4: "easy", 5: "easy", 6: "medium", 7: "hard", 8: "hard"},
        )

        # XOR chains (SAT and UNSAT, medium size)
        suite.instances += _xor_batch(
            [(50, True, s) for s in range(5)]
            + [(50, False, s) for s in range(5)]
            + [(200, True, s) for s in range(3)]
            + [(200, False, s) for s in range(3)]
        )

        # Graph coloring
        suite.instances += _coloring_batch([
            (10, 3, 0.5, s) for s in range(5)
        ] + [
            (15, 4, 0.4, s) for s in range(5)
        ])

        # Ladder encoding (easy, always SAT)
        suite.instances += _ladder_batch([(50, s) for s in range(5)])

        # Mutilated chessboard (always UNSAT, 4×4 and 6×6)
        for n in [4, 6]:
            formula, expected = mutilated_chessboard(n)
            suite.instances.append(EvalInstance(
                name=f"mutilated_{n}x{n}",
                formula=formula,
                expected=expected,
                category="mutilated-chessboard",
                difficulty="medium" if n <= 4 else "hard",
            ))

        return suite

    @staticmethod
    def full() -> EvalSuite:
        """
        ~500 instances for comprehensive performance profiling.
        Suitable for measuring PAR-2 against SOTA solvers.
        Default timeout: 300 s per instance (SAT competition standard).
        """
        suite = EvalSuite(
            name="full",
            description="Full eval suite: ~500 instances, SAT competition style",
            timeout=300.0,
        )

        # Random 3-SAT, various sizes
        for n in [50, 100, 200, 300]:
            m = int(n * 4.267)
            suite.instances += _random_sat_batch(
                f"r3sat_n{n}",
                [(n, m, 3, s) for s in range(20)],
                label="random-3sat",
                difficulty="easy" if n <= 50 else ("medium" if n <= 150 else "hard"),
            )

        # Random 4-SAT and 5-SAT
        for k, n, ratio in [(4, 50, 9.93), (5, 30, 20.8)]:
            m = int(n * ratio)
            suite.instances += _random_sat_batch(
                f"r{k}sat_n{n}",
                [(n, m, k, s) for s in range(10)],
                label=f"random-{k}sat",
                difficulty="medium",
            )

        # Pigeonhole (n = 4..12)
        suite.instances += _pigeonhole_batch(
            list(range(4, 13)),
            difficulty_map={
                n: "easy" if n <= 5 else ("medium" if n <= 8 else "hard")
                for n in range(4, 13)
            },
        )

        # XOR chains
        suite.instances += _xor_batch(
            [(n, sat, s)
             for n in [20, 50, 100, 500, 1000]
             for sat in [True, False]
             for s in range(4)]
        )

        # Graph coloring
        suite.instances += _coloring_batch([
            (v, k, p, s)
            for v in [10, 15, 20]
            for k in [3, 4]
            for p in [0.4, 0.6]
            for s in range(3)
        ])

        # Ladder encoding
        suite.instances += _ladder_batch(
            [(n, s) for n in [50, 100, 200] for s in range(5)]
        )

        # Mutilated chessboard (4×4, 6×6, 8×8)
        for n in [4, 6, 8]:
            formula, expected = mutilated_chessboard(n)
            suite.instances.append(EvalInstance(
                name=f"mutilated_{n}x{n}",
                formula=formula,
                expected=expected,
                category="mutilated-chessboard",
                difficulty="hard",
            ))

        return suite

    @staticmethod
    def hardness() -> EvalSuite:
        """
        Phase-transition 3-SAT at exactly the critical ratio (4.267).
        Useful for measuring raw CDCL hardness without formula structure.
        """
        suite = EvalSuite(
            name="hardness",
            description="Phase-transition 3-SAT hardness profiling",
            timeout=300.0,
        )
        for n in [50, 75, 100, 125, 150]:
            m = int(n * 4.267)
            suite.instances += _random_sat_batch(
                f"pt3sat_n{n}",
                [(n, m, 3, s) for s in range(20)],
                label="random-3sat-pt",
                difficulty="hard",
            )
        return suite
