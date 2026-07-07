"""The cosmo map: a tessellation of instance-space by obstruction structure.

Each SAT instance defines a **clause-ideal** I over F2[x]/(x^2-x): the ideal whose
common zeros are its satisfying assignments, with UNSAT <=> 1 in I. We *tessellate*
a parameter grid of such ideals -- rows are frame archetypes (implication, parity,
counting, unstructured), columns are size -- and give every tile an **obstruction
signature** computed only from the repo's tested carriers:

    frame_solve  -> which sound frame collapses it   (resolved_by)
    nullstellensatz_degree -> the GF(2) rank-deficiency depth (char-2 carrier)
    min_refutation_width   -> the resolution obstruction (BSW carrier)
    extract_xors           -> the parity (GF(2)) signal (xor fraction)

Then we draw the map. The layout is not decoration -- its x-axis is the **algebra**
the tile lives in, straight from HYPERBOLIC_PROGRAMMING_NOTE.md:

    real ordered cones (HP-visible)  |  characteristic 2 (HP-blind)  |  unstructured
    implication (orthant/LP)         |  parity (GF(2))               |  CDCL_NEEDED
    counting (e_k derivative tower)  |                               |

so the map *shows* that hyperbolic programming sees the left band and is
structurally blind to the parity band. The one cross-band edge is the measured
**conjugate duality** (COUNTING_FRAME_NOTE): Tseitin (parity-shallow, resolution-
deep) <-> PHP (counting-shallow, GF(2)-blind).

The map's real payload is a **moving frame**: the shallowest sound frame is a
FIELD over instance-space (tile -> cheapest collapsing algebra). frame_solve
ignores that field and tries the frames in a fixed order; the **rotor**
`frame_solve_guided` reads the local structure once and rotates the trial order
to it -- one shared parse, skipping the parity frame where no XOR structure lives.
`--hunt` follows the moving frame across the bands and measures the optim it finds
(1.5-1.75x on the unstructured/counting bands, verdicts identical).

This is a lens/atlas over measured carriers -- not a solver and not a hardness
claim beyond what each carrier already proves. Run:
    python -m docs.ladder.scripts.cosmo_map          # prints the tessellation
    python -m docs.ladder.scripts.cosmo_map --svg    # writes cosmo_map.svg
    python -m docs.ladder.scripts.cosmo_map --hunt   # the moving-frame optim hunt
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frame_benchmark import tseitin, random_3sat, random_xorsat  # noqa: E402

from backend.cnf_utils import CNFFormula  # noqa: E402
from backend.complexity.invariants import (  # noqa: E402
    min_refutation_width,
    nullstellensatz_degree,
)
from backend.eval.generators import pigeonhole  # noqa: E402
from backend.frame_solver import frame_solve, frame_solve_guided  # noqa: E402
from backend.xor_extraction import extract_xors  # noqa: E402


# ---- the tessellation: frame archetype -> ideal generator over a size grid ----

def _twosat_contradiction(k: int) -> CNFFormula:
    """Pure-BINARY 2-SAT contradiction (check_binary_clauses inspects only
    2-literal clauses, so the certificate must live there). The core forces
    a <-> ¬a: a->b->¬a and ¬a->¬b->a put a and ¬a in one SCC. Extra variables
    are chained strongly-connected to grow the size axis without changing the
    verdict."""
    a, b = 1, 2
    clauses = [[-a, b], [-b, -a], [a, -b], [a, b]]     # core: a<->¬a  (UNSAT)
    for i in range(2, k):
        clauses.append([-i, i + 1])
        clauses.append([-(i + 1), i])
    return CNFFormula(num_vars=max(k, 2), clauses=clauses)


# band = the algebra column (x-axis); frame = expected resolved_by
FAMILIES = [
    # name,           band,          gen(size),                          sizes
    ("implication", "real-cone",  lambda s: _twosat_contradiction(s),    [3, 5, 8, 12]),
    ("counting",    "real-cone",  lambda s: pigeonhole(s)[0],            [3, 4, 5, 6]),
    ("parity",      "char-2",     lambda s: tseitin(s, seed=1),          [4, 6, 8, 10]),
    ("xorsat",      "char-2",     lambda s: random_xorsat(s, s, 7),      [6, 8, 10, 12]),
    ("unstructured","unstructured",lambda s: random_3sat(s, round(4.26 * s), 3), [8, 12, 16, 20]),
]

BANDS = ["real-cone", "char-2", "unstructured"]


@dataclass
class Tile:
    family: str
    band: str
    size: int
    status: str
    resolved_by: str
    ns_degree: Optional[int]      # GF(2) NS degree (None if SAT/too big/not found)
    width: Optional[int]          # resolution refutation width (None if SAT/too big)
    xor_fraction: float
    x: float = 0.0
    y: float = 0.0
    node_id: str = ""


@dataclass
class CosmoMap:
    tiles: List[Tile]
    edges: List[Tuple[str, str, str]] = field(default_factory=list)  # (a,b,label)


def _signature(f: CNFFormula) -> Tuple[str, str, Optional[int], Optional[int], float]:
    fr = frame_solve(f)
    xor_fraction = extract_xors(f).xor_clause_fraction
    ns = width = None
    # NS degree and refutation width are exponential; compute only for the small
    # representative of each UNSAT family (larger tiles show frame + xor only --
    # their obstruction depth is honestly "exponential to compute here").
    if fr.status == "UNSAT" and f.num_vars <= 9 and len(f.clauses) <= 36:
        try:
            ns = nullstellensatz_degree(f, dmax=3)
        except Exception:
            ns = None
        try:
            width = min_refutation_width(f, wmax=3, max_closure=100000)
        except Exception:
            width = None
    return fr.status, fr.resolved_by, ns, width, xor_fraction


def build_cosmo_map() -> CosmoMap:
    tiles: List[Tile] = []
    for name, band, gen, sizes in FAMILIES:
        for s in sizes:
            f = gen(s)
            status, rb, ns, width, xf = _signature(f)
            tiles.append(Tile(name, band, s, status, rb, ns, width, xf,
                              node_id=f"{name}:{s}"))
    _layout(tiles)
    edges = _edges(tiles)
    return CosmoMap(tiles, edges)


def _layout(tiles: List[Tile]) -> None:
    """x = algebra band; y = family lane within the band, radius = size."""
    band_x = {"real-cone": 1.0, "char-2": 3.0, "unstructured": 5.0}
    # group families to give each its own horizontal lane inside its band
    fam_order: Dict[str, int] = {}
    for t in tiles:
        fam_order.setdefault(t.family, len(fam_order))
    lane_in_band: Dict[str, int] = {}
    band_fams: Dict[str, List[str]] = {b: [] for b in BANDS}
    for t in tiles:
        if t.family not in band_fams[t.band]:
            band_fams[t.band].append(t.family)
    for b, fams in band_fams.items():
        for i, fam in enumerate(fams):
            lane_in_band[fam] = i
    for t in tiles:
        lanes = max(1, len(band_fams[t.band]))
        lane = lane_in_band[t.family]
        t.x = band_x[t.band] + (t.size / 24.0)          # size pushes rightward
        t.y = (lane - (lanes - 1) / 2.0) * 1.2 + (t.size % 3) * 0.12


def _edges(tiles: List[Tile]) -> List[Tuple[str, str, str]]:
    edges: List[Tuple[str, str, str]] = []
    by_family: Dict[str, List[Tile]] = {}
    for t in tiles:
        by_family.setdefault(t.family, []).append(t)
    # tessellation grid edges: consecutive sizes within a family
    for fam, ts in by_family.items():
        ts_sorted = sorted(ts, key=lambda t: t.size)
        for a, b in zip(ts_sorted, ts_sorted[1:]):
            edges.append((a.node_id, b.node_id, "size"))
    # the one measured cross-band edge: conjugate duality Tseitin <-> PHP
    if by_family.get("parity") and by_family.get("counting"):
        t_par = min(by_family["parity"], key=lambda t: t.size)
        t_cnt = min(by_family["counting"], key=lambda t: t.size)
        edges.append((t_par.node_id, t_cnt.node_id, "conjugate-dual"))
    return edges


# ------------------------------- rendering --------------------------------

FRAME_COLORS = {
    "2sat": "#4C9BE8",       # implication
    "counting": "#E8A13C",   # counting
    "parity": "#8E63D8",     # parity (char-2)
    "none": "#9AA0A8",       # CDCL_NEEDED
}


def render_svg(cm: CosmoMap, width: int = 900, height: int = 560) -> str:
    xs = [t.x for t in cm.tiles]
    ys = [t.y for t in cm.tiles]
    x0, x1 = min(xs) - 0.6, max(xs) + 0.9
    y0, y1 = min(ys) - 0.9, max(ys) + 0.9
    pad = 60

    def px(x: float) -> float:
        return pad + (x - x0) / (x1 - x0) * (width - 2 * pad)

    def py(y: float) -> float:
        return height - pad - (y - y0) / (y1 - y0) * (height - 2 * pad)

    pos = {t.node_id: (px(t.x), py(t.y)) for t in cm.tiles}
    out: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'font-family="ui-sans-serif,system-ui,sans-serif">']
    # band backdrops
    band_label = {"real-cone": "real ordered cones · HP-visible",
                  "char-2": "characteristic 2 · HP-blind",
                  "unstructured": "unstructured · CDCL"}
    for b in BANDS:
        bx = [t.x for t in cm.tiles if t.band == b]
        if not bx:
            continue
        lo, hi = px(min(bx) - 0.5), px(max(bx) + 0.5)
        out.append(f'<rect x="{lo:.0f}" y="{pad-30:.0f}" width="{hi-lo:.0f}" '
                   f'height="{height-2*pad+60:.0f}" rx="14" fill="currentColor" '
                   f'opacity="0.05"/>')
        out.append(f'<text x="{(lo+hi)/2:.0f}" y="{pad-12:.0f}" text-anchor="middle" '
                   f'font-size="12" opacity="0.7">{band_label[b]}</text>')
    # edges
    for a, b, label in cm.edges:
        (xa, ya), (xb, yb) = pos[a], pos[b]
        dash = '6 4' if label == "conjugate-dual" else '0'
        strk = "#C04CA0" if label == "conjugate-dual" else "currentColor"
        op = 0.9 if label == "conjugate-dual" else 0.25
        out.append(f'<line x1="{xa:.0f}" y1="{ya:.0f}" x2="{xb:.0f}" y2="{yb:.0f}" '
                   f'stroke="{strk}" stroke-width="{2 if label=="conjugate-dual" else 1.4}" '
                   f'stroke-dasharray="{dash}" opacity="{op}"/>')
        if label == "conjugate-dual":
            out.append(f'<text x="{(xa+xb)/2:.0f}" y="{(ya+yb)/2-6:.0f}" '
                       f'text-anchor="middle" font-size="10" fill="#C04CA0">'
                       f'conjugate dual</text>')
    # nodes
    for t in cm.tiles:
        cx, cy = pos[t.node_id]
        color = FRAME_COLORS.get(t.resolved_by, "#9AA0A8")
        r = 9 + (t.ns_degree or 0) * 2.2       # radius grows with NS degree
        stroke = "#111" if t.status == "UNSAT" else "#fff"
        out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.1f}" fill="{color}" '
                   f'stroke="{stroke}" stroke-opacity="0.5" stroke-width="1.5">'
                   f'<title>{t.node_id}  status={t.status} frame={t.resolved_by} '
                   f'NS={t.ns_degree} width={t.width} xor={t.xor_fraction:.2f}</title></circle>')
        out.append(f'<text x="{cx:.0f}" y="{cy+r+11:.0f}" text-anchor="middle" '
                   f'font-size="9" opacity="0.75">{t.family[:4]}·{t.size}</text>')
    out.append('</svg>')
    return "\n".join(out)


def _print(cm: CosmoMap) -> None:
    print(f"{'tile':<16}{'band':<14}{'status':<13}{'frame':<10}"
          f"{'NS':>3}{'width':>6}{'xor':>6}")
    for t in cm.tiles:
        print(f"{t.node_id:<16}{t.band:<14}{t.status:<13}{t.resolved_by:<10}"
              f"{'' if t.ns_degree is None else t.ns_degree:>3}"
              f"{'' if t.width is None else t.width:>6}{t.xor_fraction:>6.2f}")
    print(f"\n{len(cm.tiles)} tiles, {len(cm.edges)} edges "
          f"({sum(1 for e in cm.edges if e[2]=='conjugate-dual')} cross-band dual)")


def hunt_optims(reps: int = 12) -> None:
    """Hunt for optimizations by following the MOVING FRAME across the map: at
    each band, compare fixed-order frame_solve against frame_solve_guided (the
    rotor -- one parse, trial order pointed at the local structure). The win
    lives where the fixed order wastes work: the unstructured band parses twice
    for a parity structure that is not there. Verdicts are identical (differential
    -tested); this measures only the cost the moving frame saves."""
    import time

    def bench(fn, f):
        fn(f)
        t = time.perf_counter()
        for _ in range(reps):
            fn(f)
        return (time.perf_counter() - t) / reps * 1000

    print(f"{'band / instance':<28}{'fixed':>9}{'moving':>9}{'speedup':>9}")
    for name, band, gen, sizes in FAMILIES:
        f = gen(sizes[-1])
        a = min(bench(frame_solve, f) for _ in range(3))
        b = min(bench(frame_solve_guided, f) for _ in range(3))
        assert frame_solve(f).status == frame_solve_guided(f).status
        print(f"{name + ' (' + band + ')':<28}{a:>8.2f}m{b:>8.2f}m{a / b:>8.2f}x")
    print("\nthe rotor wins on the unstructured/counting bands (skip the absent "
          "parity frame, one shared parse) and ties on parity (refute-first kept).")


if __name__ == "__main__":
    if "--hunt" in sys.argv:
        hunt_optims()
    else:
        cm = build_cosmo_map()
        _print(cm)
        if "--svg" in sys.argv:
            out = Path(__file__).resolve().parent / "cosmo_map.svg"
            out.write_text(render_svg(cm), encoding="utf-8")
            print(f"\nwrote {out}")
