"""Tests for the cosmo map (tessellation of instance-space by obstruction).

Pins the frame each archetype tile lands in (the map's coordinates are the
carriers' verdicts) and the graph structure, without running the slow full
build (NS degree is exponential) -- the archetype assignments ARE the claim.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "docs/ladder/scripts"))

from cosmo_map import (  # noqa: E402
    CosmoMap,
    Tile,
    _edges,
    _layout,
    _twosat_contradiction,
    render_svg,
)
from frame_benchmark import random_3sat, tseitin  # noqa: E402

from backend.eval.generators import pigeonhole  # noqa: E402
from backend.frame_solver import frame_solve  # noqa: E402


class TestTileFrames:
    def test_implication_tile_lands_in_2sat(self):
        f = _twosat_contradiction(6)
        r = frame_solve(f)
        assert r.status == "UNSAT" and r.resolved_by == "2sat"

    def test_large_pigeonhole_lands_in_counting(self):
        # PHP(3->2) is 2-SAT-shallow (2 holes -> all binary); PHP with >=3 holes
        # has 3-literal ALO and needs the counting frame -- the map surfaces this.
        r = frame_solve(pigeonhole(5)[0])
        assert r.status == "UNSAT" and r.resolved_by == "counting"

    def test_tseitin_tile_lands_in_parity(self):
        r = frame_solve(tseitin(4, seed=1))
        assert r.status == "UNSAT" and r.resolved_by == "parity"

    def test_unstructured_tile_needs_cdcl(self):
        r = frame_solve(random_3sat(12, round(4.26 * 12), 3))
        assert r.resolved_by == "none" and r.status == "CDCL_NEEDED"


class TestCosmoGraph:
    def _fixture(self):
        tiles = [
            Tile("implication", "real-cone", 3, "UNSAT", "2sat", 2, 2, 1.0,
                 node_id="implication:3"),
            Tile("parity", "char-2", 4, "UNSAT", "parity", 3, None, 1.0,
                 node_id="parity:4"),
            Tile("counting", "real-cone", 5, "UNSAT", "counting", None, None, 0.0,
                 node_id="counting:5"),
        ]
        return tiles

    def test_conjugate_dual_edge_present(self):
        edges = _edges(self._fixture())
        duals = [e for e in edges if e[2] == "conjugate-dual"]
        assert len(duals) == 1
        assert set(duals[0][:2]) == {"parity:4", "counting:5"}

    def test_layout_places_bands_left_to_right(self):
        tiles = self._fixture()
        _layout(tiles)
        by = {t.family: t.x for t in tiles}
        # real-cone band is left of char-2 band is left of ... (unstructured absent)
        assert by["implication"] < by["parity"]
        assert by["counting"] < by["parity"]

    def test_render_svg_is_wellformed(self):
        tiles = self._fixture()
        _layout(tiles)
        svg = render_svg(CosmoMap(tiles, _edges(tiles)))
        assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
        assert svg.count("<circle") == len(tiles)
        assert "conjugate dual" in svg
