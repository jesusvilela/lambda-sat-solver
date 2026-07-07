# docs/vdis/ — speculative research archive (read the CHARTER first)

**This directory is the periphery, not the core.** It is the honest paper trail
of an exploratory research program (VDIS: hypercomplex / geometric decision
heuristics — octonions, braids, gyrovectors, connection Laplacians, Garrabrant
induction, holographic-screen and moving-frame ideas). It is kept for provenance
and because a few genuine threads were pulled out of it — but by
`docs/CHARTER.md`'s standard, most of it is **lens, not contract**: evocative
framing that has *not* earned a computable, tested obligation.

If you are here to understand how the solver works, you are in the wrong place —
go to `docs/ladder/README.md` (the research that landed as tested code) and the
top-level `README.md` (the solver). This folder is the compost, not the crop.

## Keep-or-drop verdict: KEEP, valued by CONTRIBUTION (not equivalence)

The question was posed as "lift VDIS to semantic equivalence, or drop it." The
honest answer is that neither the drop nor the equivalence-lift is right, because
**equivalence is the wrong test.** VDIS is a bed of *generative heuristics and
metaphors*; a heuristic is never "semantically equivalent" to a sound frame, so
that test would condemn every generative idea by construction. The test that
matters is **contribution** — and VDIS's contribution is already banked and
tested: the shallow-frame metaphor became the three sound frames; the
fixpoint/self-reference thread became `lambda_sat.fixpoint_sat`; the
connection/signed-Laplacian became a tested (and honestly scoped-out) carrier.
Metaphor is a first-class contributing quality — it generates the reframings that
later earn frames — so VDIS is **kept as the labeled generative archive it is**,
not deleted. `backend/vdis/` stays isolated (nothing in core imports it) and
tested; every live claim still links to a passing test, everything else is
labelled lens. Compost has value precisely because the crop grew from it.

## What graduated from here into tested code

- **the shallow-frame idea** → the three sound frames
  (`binary_clause_check`, `xor_extraction`, `cardinality_check`) and the
  `cross_algebra_depth` corollary.
- **the fixpoint / self-reference thread** → `lambda_sat.fixpoint_sat`
  (bounded fixpoint unrolling = the ε>0 remainder, tested).
- **the connection/signed Laplacian** → tested and *honestly scoped out* as a
  hardness carrier (`signed_laplacian_frustration`; see `RUNG2_REPORT.md`).

## What remains lens (unbuilt, honestly labelled)

Curvature/holonomy scoring, octonionic non-associativity of clauses,
zero-divisor "annihilation channels" as a solver mechanism, holographic screens,
the ToE/UTAI framings. These are ideas, recorded as ideas. None decides SAT
today, and none is claimed to. Each stays here until — if ever — it earns a frame
contract the way parity and counting did.

## Status

Point-in-time reports (`REPO_STATE.md`, the `MAXGEO_*`, `VDIS*_PREREG/REPORT`
files, etc.) are dated snapshots — accurate when written, not live instructions.
Treat every claim in this folder as **speculative** unless it links to a passing
test in `backend/tests/`.
