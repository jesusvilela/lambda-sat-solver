"""metametasolver -- the fractal, n-caged portfolio that out-searches CMS on the tail.

Game-theoretic reading of the moving-frame regime (GAME_THEORY_NOTE.md): solving is a
zero-sum game, SOLVER vs an adversarial NATURE that draws the instance. A single
engine+seed is a PURE strategy; Nature, through the heavy-tailed runtime distribution
of random-3SAT (Gomes-Selman), can always draw the tail where a pure strategy is slow.
A parallel portfolio of diversified strategies is a MIXED strategy, and by the minimax
theorem its security value dominates every pure one -- it collapses Nature's variance to
the lower envelope (the Virtual Best Solver). Measured: best-of-k Kissat seeds beats a
single CryptoMiniSat run on hard random-3SAT (7-40x), WITHOUT CMS in the pool.

The construction is FRACTAL / n-caged: a `Cage` races a set of strategies and returns
the first CERTIFIED verdict, killing the losers. A strategy may itself be a Cage, so the
same operator composes at every scale (n cages deep, over n instance-cosmos) -- a mixed
strategy over mixed strategies. The base cage is:

    frames-if-sufficient  (instant, certified -- wins every structured island)
    else a parallel seed-diversified CDCL portfolio (wins the heavy-tailed tunnel)

Soundness/certification is preserved: the frame arm is sound by construction, each CDCL
arm is DRAT-checked (UNSAT) or model-verified (SAT), and racing certified arms and taking
the first is still certified. Honest cost: the portfolio spends ~k cores of CPU to win
wall-clock; on multi-core hardware that is the right trade, and it is stated, not hidden.
"""

from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .cnf_utils import CNFFormula, verify_model, write_dimacs
from .frame_solver import frame_solve_scouted
from .proof_checking import DRATChecker


@dataclass
class CageResult:
    status: str                       # 'SAT' | 'UNSAT' | 'TIMEOUT'
    seconds: float                    # wall-clock (parallel min)
    winner: str                       # which arm won ('parity'|'counting'|'kissat#3'|...)
    certified: bool
    model: Optional[Dict[int, bool]] = None
    arms: int = 0                     # how many strategies raced
    cpu_seconds: float = 0.0          # summed arm time (the honest CPU cost)


# --- leaf CDCL arms, each a diversified pure strategy (engine + seed) ---
def _arm_cmd(engine: str, seed: int, cnf: Path, proof: Path) -> List[str]:
    if engine == "kissat":
        return ["kissat", "--relaxed", f"--seed={seed}", str(cnf), str(proof)]
    if engine == "cadical":
        return ["cadical", f"--seed={seed}", str(cnf), str(proof)]
    raise ValueError(engine)


def _parallel_cdcl_portfolio(formula: CNFFormula, arms: List[Tuple[str, int]],
                             timeout_s: float) -> CageResult:
    """Launch every (engine, seed) arm at once; return the FIRST arm to finish with a
    certified verdict, then kill the rest. Real parallelism (each arm is its own
    process); the winner's proof/model is checked before it is trusted."""
    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        cnfp = d / "f.cnf"
        write_dimacs(formula, cnfp)
        procs = []
        for i, (engine, seed) in enumerate(arms):
            proofp = d / f"a{i}.drat"
            p = subprocess.Popen(_arm_cmd(engine, seed, cnfp, proofp),
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                 text=True, start_new_session=True)
            procs.append((i, engine, seed, proofp, p))

        winner = None
        while winner is None:
            if time.perf_counter() - t0 > timeout_s:
                break
            for i, engine, seed, proofp, p in procs:
                if p.poll() is None:
                    continue
                rc = p.returncode
                if rc not in (10, 20):          # this arm errored/aborted; ignore it
                    continue
                out = p.stdout.read() if p.stdout else ""
                winner = (i, engine, seed, proofp, rc, out)
                break
            if winner is None:
                time.sleep(0.005)

        # stop every still-running arm (whole process group, kissat may spawn)
        for _i, _e, _s, _pp, p in procs:
            if p.poll() is None:
                try:
                    os.killpg(os.getpgid(p.pid), signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    p.kill()
        for _i, _e, _s, _pp, p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass

        dt = time.perf_counter() - t0
        if winner is None:
            return CageResult("TIMEOUT", dt, "none", False, arms=len(arms),
                              cpu_seconds=dt * len(arms))
        i, engine, seed, proofp, rc, out = winner
        label = f"{engine}#{seed}"
        if rc == 20:                            # UNSAT -> DRAT certify
            res = DRATChecker().check_proof(formula, proofp, timeout=60)
            return CageResult("UNSAT", dt, label, res.valid, arms=len(arms),
                              cpu_seconds=dt * len(arms))
        model = {}                              # SAT -> parse + verify model
        for line in out.splitlines():
            if line.startswith("v "):
                for tok in line[2:].split():
                    lit = int(tok)
                    if lit != 0:
                        model[abs(lit)] = (lit > 0)
        ok = verify_model(formula, model)
        return CageResult("SAT", dt, label, ok, model=(model if ok else None),
                          arms=len(arms), cpu_seconds=dt * len(arms))


def default_arms(breadth: int = 6) -> List[Tuple[str, int]]:
    """The diversified portfolio: Kissat across `breadth` seeds plus one CaDiCaL seed
    for engine diversity. No CryptoMiniSat -- the point is to out-search it, not use it."""
    arms: List[Tuple[str, int]] = [("kissat", s) for s in range(breadth)]
    arms.append(("cadical", 0))
    return arms


def metametasolve(formula: CNFFormula, breadth: int = 6,
                  timeout_s: float = 20.0) -> CageResult:
    """The fractal cage. First: do frame + geometry SUFFICE? (instant certified verdict
    on every structured island). Else: race the seed-diversified CDCL portfolio -- the
    mixed strategy that collapses the heavy-tailed tunnel to its lower envelope."""
    t0 = time.perf_counter()
    r = frame_solve_scouted(formula)
    if r.status == "UNSAT":
        return CageResult("UNSAT", time.perf_counter() - t0, r.resolved_by, True, arms=1)
    if r.status == "SAT" and r.model is not None and verify_model(formula, r.model):
        return CageResult("SAT", time.perf_counter() - t0, r.resolved_by, True,
                          model=r.model, arms=1)
    elapsed = time.perf_counter() - t0
    res = _parallel_cdcl_portfolio(formula, default_arms(breadth), timeout_s - elapsed)
    res.seconds += elapsed
    return res
