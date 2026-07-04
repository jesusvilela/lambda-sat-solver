# VDIS v8 pre-registration — self-reference centrality prior

**Operator chose this over the λ replication. Committed before any run.
The computable form of Gödelian self-reference — a score defined
self-consistently in terms of itself — is eigenvector centrality over
the variable-interaction graph. It is a STRUCTURAL signal (reads the
instance's topology), the first candidate orthogonal to activity by
construction, and the one lens from
`SELFREF_RECOGNITION_NOTE.md` with a real contract AND fresh material.**

## Mechanism (pinned)

Variable-interaction graph A: A_ij = #clauses containing both variables
i and j (the co-occurrence graph, same as the ascendency network).
Eigenvector centrality c = principal eigenvector: c_v ∝ Σ_u A_vu c_u —
"a variable is important if its neighbours are important," the
fixed-point / diagonal made computable. Computed once at construction by
power iteration (c ← Ac/‖Ac‖, ≤ 100 iters or ‖Δ‖<1e-8), O(edges)/iter,
static for the solve. Trader score = min-max-normalized c over
unassigned vars, added to the v6/v7 combiner as an expert.

## The pinned scientific tension (predicted before running)

Eigenvector centrality is **symmetry-respecting**: variables in the
same graph-automorphism orbit get *equal* centrality. Pigeonhole's
variable graph is near-vertex-transitive, so its centrality is predicted
**near-uniform → no signal → cannot help php**. Symmetry-breaking needs
a symmetry-*breaking* signal (the arbitrary prime order); centrality, by
respecting symmetry, is the wrong tool for the most symmetric family and
the right tool only where structure is *heterogeneous* (random-3sat,
possibly mutilated). This is the honest hypothesis, pre-registered so a
php failure is a confirmed prediction, not an excuse.

## Configs (algebra C, dim 32, κ per family, seeds 0–4)

| Label | Traders |
|---|---|
| EVSIDS | baseline |
| C-plain | none |
| λ-only | Lagrange (v7 best) |
| cent-only | centrality |
| cent+λ | centrality + Lagrange |

## Instance set (the v7 set, for direct comparability)

pigeonhole 5–8; mutilated-chessboard 8, 10; random-3sat n=90 seeds
300–314 (15). LRB run post-hoc on the same instances as in v7.

## Gates and pre-registered predictions

- **V0 (premise/liveness)**: centrality converges, and is **decorrelated
  from base activity** (mean |rank-corr| < 0.5 on r3sat). If centrality
  ≈ activity, the "fresh orthogonal signal" premise is FALSE and v8 is
  reported dead-on-arrival — this is a real gate, checked at the probe.
- **V0b (symmetry prediction)**: centrality variance across variables is
  near-zero on pigeonhole (< 10% of its r3sat variance). Pre-registers
  the symmetry-respecting claim.
- **V1 (primary)**: cent-only or cent+λ beats EVSIDS on decisions on
  random-3sat (≥ 60% of 15) — the heterogeneous family where centrality
  should have signal.
- **V2 (the recognition/resonance unlock)**: cent+λ beats λ-only on
  aggregate over the union set — do TWO decorrelated signals (structural
  centrality + history-diversifying λ) combine better than λ alone? This
  is the first test of whether a second orthogonal axis helps, the
  precondition the note flagged for recognition/resonance.
- **V3 (control)**: on pigeonhole, cent-only ≈ C-plain (no signal), per
  V0b — a positive here would falsify the symmetry-respecting claim.
- **Floor**: ≥ EVSIDS's Random-beat-count.
- **No-rescue**: mechanism (100 power-iters, co-occurrence graph, min-max
  norm) and grid final.
