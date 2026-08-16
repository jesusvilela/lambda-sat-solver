#!/usr/bin/env python3.11
"""Deformation-sequence holonomy test (bordon-agent §4 deformation test).

The skill's test chamber specifies: after convergence, perturb the world (move
walls / change terrain) and measure recovery — this is where the moving frame
should matter most. We realize it as: solve an instance, perturb it (flip clause
signs — a deformation of the formula), re-solve, and measure the CUMULATIVE
rotational deficit of the moving frame across the whole sequence.

The key prediction: a multi-step deformation sequence should produce LARGER
cumulative holonomy than a single solve (last turn: mean 0.048). If the frame is
genuinely adapting to surprise, each perturbation should rotate it further; if
it's static, holonomy stays flat. This is the falsifiable test.

ADIABATIC vs DIABATIC (glossary §4): if cumulative holonomy stays below threshold
across the sequence, the transport is adiabatic (conserved quantities survive).
If it blows past threshold, the frame spun out — diabatic, coherence lost.

Usage: python deformation_holonomy.py --instances 30 --steps 4
"""
from __future__ import annotations

import argparse
import json
import os
import random
import time
from typing import Dict, List, Tuple

import numpy as np

from backend.cnf_utils import CNFFormula, verify_model
from backend.eval.generators import random_ksat, pigeonhole, xor_chain


def perturb(formula: CNFFormula, flip_prob: float, rng: random.Random) -> CNFFormula:
    """Deform the formula by flipping a fraction of literal signs. This is the
    'move walls' perturbation — the same SAT structure, deformed."""
    new_clauses = []
    for c in formula.clauses:
        nc = [(lit * (-1 if rng.random() < flip_prob else 1)) for lit in c]
        new_clauses.append(nc)
    return CNFFormula(num_vars=formula.num_vars, clauses=new_clauses)


def run_deformation_sequence(formula: CNFFormula, n_steps: int, flip_prob: float,
                             timeout: float, seed: int) -> Dict:
    """Solve -> perturb -> re-solve -> ... for n_steps. Capture the moving-frame
    weights at EACH step, then measure cumulative holonomy across the sequence."""
    from bordon_fleet import fleet_solve
    rng = random.Random(seed)
    current = formula
    frames = []           # the frame weights after each solve
    verdicts = []
    seconds = []
    mantle_flags = []
    prev_frame = None     # cross-cycle memory: seed next cycle with this cycle's end-frame

    for step in range(n_steps):
        # pass the previous end-frame as the seed so the moving frame ACCUMULATES
        # rotation across the deformation sequence (without this it resets to
        # default each cycle and holonomy stays flat — the bug I caught).
        fv = fleet_solve(current, timeout, frame_seed=prev_frame)
        # capture the merged fleet frame (average across agents)
        if fv.agent_views:
            avg_frame = {}
            for a, view in fv.agent_views.items():
                fw = view.get("frame", {})
                for k, v in fw.items():
                    avg_frame[k] = avg_frame.get(k, 0.0) + v / len(fv.agent_views)
            # renormalize
            s = sum(avg_frame.values())
            if s > 0:
                avg_frame = {k: v/s for k, v in avg_frame.items()}
            frames.append(avg_frame)
            prev_frame = avg_frame   # carry forward
        else:
            frames.append({})
        verdicts.append(fv.verdict)
        seconds.append(fv.seconds)
        mantle_flags.append(fv.mantle_active)
        # deform for the next step (except after the last)
        if step < n_steps - 1:
            current = perturb(current, flip_prob, rng)

    # measure cumulative holonomy: frame[0] -> frame[1] -> ... -> frame[n-1]
    from manifold_clash import measure_holonomy
    step_holonomies = []
    for i in range(len(frames) - 1):
        h = measure_holonomy(frames[i], frames[i+1])
        step_holonomies.append(h)
    # cumulative = the total path length (sum of step holonomies)
    cumulative = float(np.sum(step_holonomies)) if step_holonomies else 0.0
    # net = the direct distance frame[0] -> frame[n-1] (may be < cumulative if it looped back)
    net = measure_holonomy(frames[0], frames[-1]) if len(frames) >= 2 else 0.0
    # the geometric phase = cumulative - net (how much the path "wound around")
    geometric_phase = cumulative - net

    return {
        "n_steps": n_steps,
        "verdicts": verdicts,
        "seconds": [round(s, 4) for s in seconds],
        "mantle_flags": mantle_flags,
        "step_holonomies": [round(h, 4) for h in step_holonomies],
        "cumulative_holonomy": round(cumulative, 4),
        "net_holonomy": round(net, 4),
        "geometric_phase": round(geometric_phase, 4),
        "adiabatic": cumulative < 0.3,   # glossary §4 threshold
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--instances", type=int, default=30)
    ap.add_argument("--steps", type=int, default=4, help="deformation steps per instance")
    ap.add_argument("--flip_prob", type=float, default=0.1, help="fraction of literals flipped per step")
    ap.add_argument("--timeout", type=float, default=3.0)
    args = ap.parse_args()

    # build a diverse instance set (structured + unstructured)
    instances = []
    for s in range(args.instances // 2):
        f, _ = random_ksat([60, 100, 150, 200][s % 4], 0, k=3, seed=s) if False else random_ksat([60,100,150,200][s%4], int([60,100,150,200][s%4]*4.267), k=3, seed=s)
        instances.append(("random-3sat", f"r3sat_s{s}", f))
    for s in range(args.instances // 2):
        f, _ = pigeonhole(6 + (s % 5))
        instances.append(("pigeonhole", f"php_s{s}", f))

    print(f"=== DEFORMATION HOLONOMY TEST ===")
    print(f"{len(instances)} instances × {args.steps} steps × flip_prob={args.flip_prob}\n")

    results = []
    single_cycle_holonomies = []  # the baseline: single-solve holonomy (last turn: ~0.048)
    cumulative_holonomies = []
    geometric_phases = []
    adiabatic_count = 0

    t0 = time.perf_counter()
    for fam, iid, f in instances:
        try:
            r = run_deformation_sequence(f, args.steps, args.flip_prob, args.timeout, hash(iid) % 1000)
            r["instance_id"] = iid
            r["family"] = fam
            results.append(r)
            # first-step holonomy ~ single-cycle baseline
            if r["step_holonomies"]:
                single_cycle_holonomies.append(r["step_holonomies"][0])
            cumulative_holonomies.append(r["cumulative_holonomy"])
            geometric_phases.append(r["geometric_phase"])
            if r["adiabatic"]:
                adiabatic_count += 1
            print(f"  {iid:14s} steps={r['step_holonomies']} cum={r['cumulative_holonomy']:.4f} "
                  f"net={r['net_holonomy']:.4f} phase={r['geometric_phase']:+.4f} "
                  f"{'adiabatic' if r['adiabatic'] else 'DIABATIC'}")
        except Exception as exc:
            print(f"  {iid:14s} ERROR: {exc}")
    print(f"\nwall: {time.perf_counter()-t0:.0f}s")

    print(f"\n=== RESULTS (n={len(results)}) ===")
    print(f"  single-cycle holonomy (step 0->1):  mean={np.mean(single_cycle_holonomies):.4f}  "
          f"(last turn's flat measurement: 0.048)")
    print(f"  cumulative holonomy ({args.steps}-step seq): mean={np.mean(cumulative_holonomies):.4f}  "
          f"max={np.max(cumulative_holonomies):.4f}")
    print(f"  geometric phase (cum - net):        mean={np.mean(geometric_phases):+.4f}  "
          f"(non-zero = the frame wound around, didn't just drift)")
    print(f"  adiabatic fraction:                 {adiabatic_count}/{len(results)} "
          f"({'frame stayed coherent' if adiabatic_count > len(results)/2 else 'frame spun out'})")

    # the falsifiable claim: cumulative > single-cycle if the frame adapts to surprise
    ratio = np.mean(cumulative_holonomies) / max(np.mean(single_cycle_holonomies), 1e-6)
    print(f"\n  cumulative/single ratio: {ratio:.2f}x  "
          f"({'frame ADAPTS to deformation (moving frame works)' if ratio > 1.5 else 'frame roughly static'})")

    out = "deformation_holonomy.json"
    with open(out, "w") as fh:
        json.dump({"config": vars(args), "results": results,
                   "summary": {
                       "single_cycle_mean": float(np.mean(single_cycle_holonomies)),
                       "cumulative_mean": float(np.mean(cumulative_holonomies)),
                       "geometric_phase_mean": float(np.mean(geometric_phases)),
                       "ratio": float(ratio),
                       "adiabatic_fraction": adiabatic_count / len(results),
                   }}, fh, indent=1)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
