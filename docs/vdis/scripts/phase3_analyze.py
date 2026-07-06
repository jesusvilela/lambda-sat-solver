"""Phase 3 analysis. Reads phase3_results.jsonl, applies the
pre-registered decision rules (PHASE_3_PREREG.md) mechanically, prints
the P1-P4 verdicts and the tables for the report. Rerunnable; contains
no thresholds that aren't in the prereg."""

import json
import os
import sys
from collections import defaultdict
from statistics import median

RESULTS = os.path.join(os.path.dirname(__file__), "phase3_results.jsonl")
INF = float("inf")


def load(stage):
    # med[config][instance] = median-over-seeds decisions (capped = +inf)
    per = defaultdict(lambda: defaultdict(list))
    fam = {}
    with open(RESULTS) as f:
        for line in f:
            r = json.loads(line)
            if r["stage"] != stage:
                continue
            d = r["decisions"] if r["result"] != "UNKNOWN" else INF
            per[r["config"]][r["instance"]].append(d)
            fam[r["instance"]] = r["family"]
    med = {
        cfg: {inst: median(v) for inst, v in by_inst.items()}
        for cfg, by_inst in per.items()
    }
    return med, fam


def beats(a, b, instances):
    """#instances where config-a median < config-b median (strict)."""
    return sum(1 for i in instances if a.get(i, INF) < b.get(i, INF))


def pick_winner(med, instances):
    ev = med["EVSIDS"]
    best, best_key = None, None
    for cfg in med:
        if not cfg.startswith("VDIS-"):
            continue
        wins = beats(med[cfg], ev, instances)
        total = sum(min(med[cfg].get(i, INF), 10**9) for i in instances)
        key = (-wins, total)
        if best_key is None or key < best_key:
            best_key, best = key, cfg
    return best, -best_key[0]


def main():
    med, fam = load("b13")
    instances = sorted(med["EVSIDS"].keys())
    assert len(instances) == 13, instances

    winner, p1_count = pick_winner(med, instances)
    print(f"winner config: {winner}  (beats EVSIDS on {p1_count}/13)")
    print(f"P1 (>=7/13): {'PASS' if p1_count >= 7 else 'FAIL'}")

    p2_count = beats(med[winner], med["Random"], instances)
    print(f"P2: winner beats Random on {p2_count}/13 (>=12): "
          f"{'PASS' if p2_count >= 12 else 'FAIL'}")

    print("\nper-instance medians (b13):")
    cfgs = ["EVSIDS", "LRB", "Random", winner]
    print(f"{'instance':22s}" + "".join(f"{c:>26s}" for c in cfgs))
    for i in instances:
        print(f"{i:22s}" + "".join(f"{med[c].get(i, INF):>26.1f}" for c in cfgs))

    if len(sys.argv) > 1 and sys.argv[1] == "winner-only":
        return

    # P3: ablation stage
    try:
        amed, _ = load("ablation")
        (acfg,) = list(amed.keys())
        a_count = beats(amed[acfg], med["EVSIDS"], instances)
        print(f"\nP3: beta=0 ablation beats EVSIDS on {a_count}/13 "
              f"(winner: {p1_count}); degradation >=1: "
              f"{'PASS' if a_count <= p1_count - 1 else 'FAIL'}")
    except (FileNotFoundError, ValueError):
        print("\nP3: ablation stage not run yet")

    # P4: held-out per-family kappa vs global
    try:
        pmed, pfam = load("p4")
        fam_cfg = next(c for c in pmed if "kappa=family" in c)
        glob_cfg = next(c for c in pmed if "kappa=-1" in c)
        by_family = defaultdict(lambda: [0.0, 0.0])
        for inst in pmed[fam_cfg]:
            f = pfam[inst]
            by_family[f][0] += min(pmed[fam_cfg].get(inst, INF), 10**9)
            by_family[f][1] += min(pmed[glob_cfg].get(inst, INF), 10**9)
        wins = 0
        print("\nP4 held-out, summed per-instance medians:")
        for f, (a, b) in sorted(by_family.items()):
            w = a < b
            wins += w
            print(f"  {f:16s} family-kappa={a:10.1f}  global-1={b:10.1f}  "
                  f"{'WIN' if w else 'loss/tie'}")
        print(f"P4 (>=2/3): {'PASS' if wins >= 2 else 'FAIL'}")
    except (FileNotFoundError, StopIteration):
        print("\nP4: stage not run yet")

    # suite context
    try:
        smed, sfam = load("suite")
        vcfg = next(c for c in smed if c.startswith("VDIS-"))
        insts = sorted(smed["EVSIDS"].keys())
        print(f"\nsuite context ({len(insts)} instances), "
              f"#instances with fewer median decisions than EVSIDS:")
        for c in ("LRB", "Random", vcfg):
            print(f"  {c:30s} {beats(smed[c], smed['EVSIDS'], insts):3d}"
                  f" / ties {sum(1 for i in insts if smed[c].get(i, INF) == smed['EVSIDS'].get(i, INF))}")
        caps = defaultdict(int)
        with open(RESULTS) as f:
            for line in f:
                r = json.loads(line)
                if r["stage"] == "suite" and r["result"] == "UNKNOWN":
                    caps[r["config"]] += 1
        if caps:
            print("  capped runs:", dict(caps))
    except (FileNotFoundError, StopIteration):
        print("\nsuite: stage not run yet")


if __name__ == "__main__":
    main()
