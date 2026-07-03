# VDIS v5 pre-registration — the C branch gets the tie-break; fresh instances

**Origin: operator instruction "self reflect and proceed at your
leisure." The self-reflection pass found a real reporting error (see
the correction note in VDIS4_REPORT.md): VDIS-C from the original
Phase 3 sweep holds the true track-best total (20 043) and php medians
(14 623 / 1 371), and every v2–v4 mechanism generation was built on
the H lineage only. Two consequences drive this prereg's design; the
operator's inspiration material (hyperbolic/hypercomplex/HDC
synthesis) contributes one lens noted below and no imported
machinery.**

## Motivation, pinned before running

1. **The obvious unrun experiment**: the pair-θ anti-ambiguous
   tie-break — the one mechanism with a measured positive contribution
   (+1 win / −1 759 total on H, v4's CTRL decomposition) — was never
   applied to the C branch, which dominates H on aggregate while using
   half the dimensions per slot. C-PA is well-defined (θ from 2-dim
   living vectors; geometry verified; liveness probed: θ spread 0.334,
   tie-breaks fire on fresh r3sat).
2. **In-sample selection risk, now acute**: four generations of
   best-of-grid selection have reused the same B13′ instances
   (~1 900 runs). Aggregate-total claims are increasingly fitted to
   those 13 instances. v5's primary arbiter is therefore **B13″**:
   the same recipe with FRESH r3sat seeds. The deterministic php
   instances cannot be freshened and are carried unchanged (declared,
   not hidden).
3. On the inspiration material: its checkable physics claims
   (quaternions bounding/resolving Navier–Stokes singularities — an
   open Millennium problem; κ = (h ln 2)² as a curvature law; 10⁴-dim
   hypervectors) have no input→invariant→action→benchmark contract
   here and import nothing (the S3.7 budget stays at dim ≤ 64). The
   one lens retained: HDC's identity-code principle (near-orthogonal
   high-dim codes carrying identity robustly) is a fair post-hoc
   description of what the precessing prime anchors did on php ties —
   now correctly scoped as a −7% within-H effect that the C branch's
   curvature choice dwarfs (−23%). No new mechanism is built from the
   document.

## Instance set B13″

- pigeonhole(5..8) — identical to B13′ (deterministic; declared).
- random_ksat(n, int(n·4.267), k=3, seed=s) for n ∈ {50, 75, 100} ×
  s ∈ {11, 12, 13} — fresh, never used anywhere in this track.

## Configs (all κ per frozen family table, λχ = 0.1, dim = 32, seeds 0–4, cap 100 000)

| Label | Description |
|---|---|
| EVSIDS / LRB / Random | baselines, rerun on B13″ |
| C-plain | the corrected incumbent (algebra C, no tie-break) |
| **C-PA** | C-plain + pair-θ anti-ambiguous tie-break (the new config) |
| H-PA | v3's config, fresh-data regression row |
| H-MF3 | v4's config, fresh-data regression row |

## Gates and pre-registered predictions

- **X1 (liveness)**: done before this prereg's benchmark — C-PA θ
  spread 0.334 and 2 tie-break fires on fresh r3sat_n100_s11. PASS.
- **X2 (selection-regression, a prediction about our own history)**:
  the incumbents' fresh-r3sat win-rates will regress relative to their
  B13′ r3sat win-rates (C-plain: 4/9 on B13′; H-PA: 4/9; H-MF3: 4/9).
  Direction predicted: down. Quantified either way — if they hold up,
  the totals story was not in-sample-inflated and that is worth
  knowing too.
- **X3 (primary)**: best VDIS config beats EVSIDS on ≥ 7/13 of B13″.
- **X4 (transfer)**: C-PA ≥ C-plain on B13″ (win count; ties broken by
  total). Does the H-measured tie-break benefit transfer to C?
- **Floor**: ≥ 11/13 vs Random on B13″.
- **No-rescue**: grid final for v5.
