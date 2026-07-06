"""Holographic-screen / cellular-gate test (operator's globular-Poincare-
balls construction, decoded). Planted-community CNF = the "balls";
cut/boundary variables = the "screens/gates". Tests whether branching on
boundary variables (gate trader) beats EVSIDS/degree on the community-
structured instances the construction is designed for.

Result (see HOLOGRAPHIC_SCREEN_REPORT section in THESIS_INGREDIENT_HUNT.md):
detection is perfect (label-prop recovers planted communities), but the
gate signal does NOT beat EVSIDS or degree on aggregate in any regime -
3-5/12 vs EVSIDS, 2-5/12 vs degree. The construction, tested on its home
turf with oracle community labels, is another negative.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from backend.eval.generators import planted_community_ksat
from backend.refsolver.solver import CDCLSolver
from backend.refsolver.heuristics import EVSIDSHeuristic
from backend.vdis.vdis_heuristic import VDISHeuristic, compute_chi


def gate_heur(cnf, traders, labels=None):
    return VDISHeuristic(
        cnf.num_vars, dim=32, c=-1.0, algebra="C", lambda_chi=0.1,
        chi=compute_chi(cnf.clauses, cnf.num_vars), combine_nudges=True,
        nudge_gate=1.0, combine_traders=traders, clauses=cnf.clauses,
        community_labels=labels, seed=0)


def run(cnf, h):
    s = CDCLSolver(cnf, h, max_conflicts=300000)
    r, _ = s.solve()
    return s.stats.decisions, r.name


if __name__ == "__main__":
    for nc, vpc, ir, cut in [(5, 30, 3.9, 80), (5, 30, 4.0, 25),
                             (6, 25, 3.6, 30), (4, 35, 4.1, 20)]:
        tot = {"EVSIDS": 0, "degree": 0, "gate": 0}
        wg_e = wg_d = nsat = 0
        for seed in range(12):
            cnf, lab, cv = planted_community_ksat(nc, vpc, ir, cut, seed=seed)
            e, _ = run(cnf, EVSIDSHeuristic(cnf.num_vars, seed=0))
            d, _ = run(cnf, gate_heur(cnf, ("degree",)))
            g, rn = run(cnf, gate_heur(cnf, ("gate",), labels=lab))
            tot["EVSIDS"] += e; tot["degree"] += d; tot["gate"] += g
            wg_e += g < e; wg_d += g < d; nsat += rn == "SAT"
        print(f"comms={nc} vpc={vpc} ir={ir} cut={cut} ({nsat}/12 SAT): "
              f"{tot} | gate beats EV {wg_e}/12, beats degree {wg_d}/12")
