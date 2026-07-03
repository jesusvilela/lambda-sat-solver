"""Phase 3 benchmark runner. Implements docs/vdis/PHASE_3_PREREG.md
exactly - instance sets, configs, seeds, caps, and metrics are pinned
there; this script is mechanism only. Results append to a JSONL file
(one record per run) so partial progress survives interruption and the
analysis is a separate, rerunnable step (phase3_analyze.py).

Stages (selected by argv[1], so stages can run as parallel processes):
  b13     - B13' x (8 sweep configs + EVSIDS + LRB + Random) x seeds 0-4
  ablation WINNER_SPEC - winner config with beta=0 on B13' x seeds 0-4
  p4 WINNER_SPEC       - held-out set, per-family kappa vs global -1
  suite WINNER_SPEC    - quick+medium context run, winner + baselines

WINNER_SPEC format: algebra,lambda_tau,lambda_chi e.g. "C,0.1,0.0"
(determined by phase3_analyze.py from the b13 stage before the
dependent stages run - the winner rule is pre-registered, so this
ordering leaks no freedom).
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from backend.eval.generators import graph_coloring, pigeonhole, random_ksat
from backend.eval.suite import StandardSuites
from backend.refsolver.solver import CDCLSolver
from backend.refsolver.heuristics import EVSIDSHeuristic, LRBHeuristic, RandomHeuristic
from backend.vdis.kappa_table import kappa_for
from backend.vdis.vdis_heuristic import VDISHeuristic, compute_chi

MAX_CONFLICTS = 100_000
SEEDS = (0, 1, 2, 3, 4)
RESULTS = os.path.join(os.path.dirname(__file__), "phase3_results.jsonl")


def b13_instances():
    out = []
    for n in (5, 6, 7, 8):
        cnf, _ = pigeonhole(n)
        out.append((f"php_{n}_{n-1}", "pigeonhole", cnf))
    for n in (50, 75, 100):
        for s in (1, 2, 3):
            cnf, _ = random_ksat(n, int(n * 4.267), k=3, seed=s)
            out.append((f"r3sat_n{n}_s{s}", "random-3sat", cnf))
    return out


def heldout_instances():
    out = []
    for n, m, tag in ((50, int(50 * 4.267), "r3sat_n50"), (100, int(100 * 4.267), "r3sat_n100")):
        for s in range(1000, 1005):
            cnf, _ = random_ksat(n, m, k=3, seed=s)
            out.append((f"{tag}_s{s}", "random-3sat", cnf))
    for s in range(1000, 1005):
        cnf, _ = random_ksat(40, int(40 * 9.93), k=4, seed=s)
        out.append((f"r4sat_n40_s{s}", "random-4sat", cnf))
    for v, k, p in ((10, 3, 0.5), (15, 4, 0.4)):
        for s in range(1000, 1005):
            cnf, _ = graph_coloring(v, k, edge_probability=p, seed=s)
            out.append((f"color_v{v}k{k}_s{s}", "graph-coloring", cnf))
    return out


def make_vdis(cnf, family, algebra, lt, lc, seed, beta=0.1, global_kappa=None):
    kappa = global_kappa if global_kappa is not None else kappa_for(algebra, family)
    return VDISHeuristic(
        cnf.num_vars, dim=32, c=-kappa, algebra=algebra,
        beta=beta, lambda_tau=lt, lambda_chi=lc,
        chi=compute_chi(cnf.clauses, cnf.num_vars) if lc != 0.0 else None,
        seed=seed,
    )


def run_one(stage, name, family, cnf, config_label, make, seed, done):
    key = f"{stage}|{name}|{config_label}|{seed}"
    if key in done:
        return
    t0 = time.perf_counter()
    solver = CDCLSolver(cnf, make(seed), max_conflicts=MAX_CONFLICTS)
    result, _ = solver.solve()
    rec = {
        "stage": stage, "instance": name, "family": family,
        "config": config_label, "seed": seed, "result": result.name,
        "decisions": solver.stats.decisions, "conflicts": solver.stats.conflicts,
        "wall_s": round(time.perf_counter() - t0, 3),
    }
    with open(RESULTS, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(key, rec["result"], rec["decisions"], f"{rec['wall_s']}s", flush=True)


def load_done():
    done = set()
    if os.path.exists(RESULTS):
        with open(RESULTS) as f:
            for line in f:
                r = json.loads(line)
                done.add(f"{r['stage']}|{r['instance']}|{r['config']}|{r['seed']}")
    return done


def sweep_configs():
    for algebra in ("C", "H"):
        for lt in (0.0, 0.1):
            for lc in (0.0, 0.1):
                yield algebra, lt, lc


def vdis_label(algebra, lt, lc, suffix=""):
    return f"VDIS-{algebra},lt={lt},lc={lc}{suffix}"


BASELINES = {
    "EVSIDS": lambda cnf: (lambda seed: EVSIDSHeuristic(cnf.num_vars, seed=seed)),
    "LRB": lambda cnf: (lambda seed: LRBHeuristic(cnf.num_vars, seed=seed)),
    "Random": lambda cnf: (lambda seed: RandomHeuristic(cnf.num_vars, seed=seed)),
}


def stage_b13(done):
    for name, family, cnf in b13_instances():
        for label, mk in BASELINES.items():
            for seed in SEEDS:
                run_one("b13", name, family, cnf, label, mk(cnf), seed, done)
        for algebra, lt, lc in sweep_configs():
            label = vdis_label(algebra, lt, lc)
            for seed in SEEDS:
                run_one(
                    "b13", name, family, cnf, label,
                    lambda seed, a=algebra, l1=lt, l2=lc: make_vdis(cnf, family, a, l1, l2, seed),
                    seed, done,
                )


def parse_winner(spec):
    algebra, lt, lc = spec.split(",")
    return algebra, float(lt), float(lc)


def stage_ablation(done, spec):
    algebra, lt, lc = parse_winner(spec)
    label = vdis_label(algebra, lt, lc, ",beta=0")
    for name, family, cnf in b13_instances():
        for seed in SEEDS:
            run_one(
                "ablation", name, family, cnf, label,
                lambda seed: make_vdis(cnf, family, algebra, lt, lc, seed, beta=0.0),
                seed, done,
            )


def stage_p4(done, spec):
    algebra, lt, lc = parse_winner(spec)
    for name, family, cnf in heldout_instances():
        for glob, suffix in ((None, ",kappa=family"), (-1.0, ",kappa=-1")):
            label = vdis_label(algebra, lt, lc, suffix)
            for seed in SEEDS:
                run_one(
                    "p4", name, family, cnf, label,
                    lambda seed, g=glob: make_vdis(cnf, family, algebra, lt, lc, seed, global_kappa=g),
                    seed, done,
                )


def stage_suite(done, spec):
    algebra, lt, lc = parse_winner(spec)
    instances = (
        StandardSuites.quick().instances + StandardSuites.medium().instances
    )
    for inst in instances:
        cnf = inst.formula
        for label, mk in BASELINES.items():
            for seed in SEEDS:
                run_one("suite", inst.name, inst.category, cnf, label, mk(cnf), seed, done)
        label = vdis_label(algebra, lt, lc)
        for seed in SEEDS:
            run_one(
                "suite", inst.name, inst.category, cnf, label,
                lambda seed: make_vdis(cnf, inst.category, algebra, lt, lc, seed),
                seed, done,
            )


def stage_b13v2(done):
    """VDIS v2 sweep per VDIS2_PREREG.md: H only, {A, B, AB} variants x
    lambda_tau {0.1, 0.3}; lambda_chi=0.1, beta=0.1, kappa per family.
    Baselines reused from the b13 stage, not rerun."""
    variants = (("A", True, False), ("B", False, True), ("AB", True, True))
    for name, family, cnf in b13_instances():
        chi = compute_chi(cnf.clauses, cnf.num_vars)
        for tag, anchor, ortho in variants:
            for lt in (0.1, 0.3):
                label = f"VDIS2-H,{tag},lt={lt}"
                for seed in SEEDS:
                    def mk(seed, a=anchor, o=ortho, l=lt):
                        return VDISHeuristic(
                            cnf.num_vars, dim=32, c=-kappa_for("H", family),
                            algebra="H", beta=0.1, lambda_tau=l, lambda_chi=0.1,
                            chi=chi, torsion_anchor=a, wedge_ortho=o, seed=seed,
                        )
                    run_one("b13v2", name, family, cnf, label, mk, seed, done)


def stage_b13v3(done):
    """VDIS v3 sweep per VDIS3_PREREG.md: polarity-pair torsion.
    H, dim=32, beta=0 (rotor machinery off), lambda_chi=0.1, kappa per
    family. Configs: P@0.1, P@0.3, PA, P@0.1+PA."""
    configs = (
        ("P,lp=0.1", 0.1, False),
        ("P,lp=0.3", 0.3, False),
        ("PA", 0.0, True),
        ("P,lp=0.1+PA", 0.1, True),
    )
    for name, family, cnf in b13_instances():
        chi = compute_chi(cnf.clauses, cnf.num_vars)
        for tag, lp, tie in configs:
            label = f"VDIS3-H,{tag}"
            for seed in SEEDS:
                def mk(seed, l=lp, t=tie):
                    return VDISHeuristic(
                        cnf.num_vars, dim=32, c=-kappa_for("H", family),
                        algebra="H", beta=0.0, lambda_chi=0.1, chi=chi,
                        pair_torsion=l, tie_break_pair=t, seed=seed,
                    )
                run_one("b13v3", name, family, cnf, label, mk, seed, done)


def stage_b13v4(done):
    """VDIS v4 sweep per VDIS4_PREREG.md: moving-frame rotor on the v3
    PA setup. H, dim=32, lambda_chi=0.1, kappa per family.
    CTRL is the beta=0-plain attribution control."""
    configs = (
        ("CTRL", dict(beta=0.0)),
        ("MF1", dict(beta=0.1, moving_frame=True, tie_break_pair=True,
                     tie_break_frame=1.0)),
        ("MF2", dict(beta=0.1, moving_frame=True, tie_break_frame=1.0)),
        ("MF3", dict(beta=0.1, moving_frame=True, tie_break_pair=True,
                     tie_break_frame=1.0, torsion_anchor=True)),
    )
    for name, family, cnf in b13_instances():
        chi = compute_chi(cnf.clauses, cnf.num_vars)
        for tag, extra in configs:
            label = f"VDIS4-H,{tag}"
            for seed in SEEDS:
                def mk(seed, e=extra):
                    return VDISHeuristic(
                        cnf.num_vars, dim=32, c=-kappa_for("H", family),
                        algebra="H", lambda_chi=0.1, chi=chi, seed=seed, **e,
                    )
                run_one("b13v4", name, family, cnf, label, mk, seed, done)


def main():
    done = load_done()
    stage = sys.argv[1]
    if stage == "b13":
        stage_b13(done)
    elif stage == "b13v2":
        stage_b13v2(done)
    elif stage == "b13v3":
        stage_b13v3(done)
    elif stage == "b13v4":
        stage_b13v4(done)
    elif stage == "ablation":
        stage_ablation(done, sys.argv[2])
    elif stage == "p4":
        stage_p4(done, sys.argv[2])
    elif stage == "suite":
        stage_suite(done, sys.argv[2])
    else:
        raise SystemExit(f"unknown stage {stage!r}")
    print(f"stage {stage} complete", flush=True)


if __name__ == "__main__":
    main()
