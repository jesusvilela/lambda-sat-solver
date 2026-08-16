import LambdaSatSolver.VDIS.GRD

open Real

/-!
# GRD Convergence Tests

Tests for the Geodesic Resonance Descent algorithm on the Poincaré ball.

## Test matrix

| Test | Description | Expected |
|------|-------------|----------|
| flat_gd_fails | Euclidean GD walks off manifold | φ > 5000 after 300 steps |
| riemannian_gd_converges | Curvature-aware GD stays on manifold | φ < 200 after 300 steps |
| grd_no_gate_stirring | Ungated Hamiltonian does not settle | std > 0.3 (unstable) |
| grd_with_gate_converges | Payor gate produces smooth convergence | std < 0.1 (settled) |
| grd_gate_accept_rate | Gate accepts most steps early, tightens late | accept_rate > 0.8 |

## Test setup

All tests use a deterministic 12-node tree embedding on the Poincaré ball
with curvature c=1. Initial positions: tree structure in first 2 dims, rest zero.
-/

noncomputable section

namespace GRDTests

open VDIS.GRD

/-- Scalar potential: sum of squared q-norms across all nodes.
Measures the total spread of the embedding — lower = more concentrated,
higher = more dispersed. Used as a convergence diagnostic. -/
def potential (nodes : List (SectionNode 12)) : ℝ :=
  (nodes.map fun n => ∑ i, (n.q i) ^ 2).sum

/-! ## Test data: 12-node tree embedding -/

/-- 12-node tree: 6 internal nodes (0..5), 6 leaves (6..11).
Structure: root=0, children of i are 2i+1 and 2i+2 for i<6. -/
def treeEmbedding : List (SectionNode 12) :=
  let q (i : Fin 12) : Fin 12 → ℝ := fun j =>
    if i.val = j.val then 0.1
    else if i.val = 0 && j.val = 1 then 0.2
    else if i.val = 0 && j.val = 2 then 0.2
    else if i.val = 1 && j.val = 3 then 0.15
    else if i.val = 1 && j.val = 4 then 0.15
    else if i.val = 2 && j.val = 5 then 0.15
    else if i.val = 2 && j.val = 6 then 0.15
    else 0.0
  List.range 12 |>.map fun i =>
    { label := s!"node_{i}"
      q := q ⟨i, by
        have hi : i < 12 := by
          have : i ∈ List.range 12 := by decide
          exact this
        exact hi⟩
      p := fun _ => 0.0
      salience := 1.0 }

/-! ## Test 1: Flat GD fails on Poincaré ball -/

/-- Euclidean GD (c=0) walks off the manifold after 300 steps. -/
def test_flat_gd_fails : IO Unit := do
  let nodes := treeEmbedding
  let η := 0.01
  -- Run 300 steps of flat GD
  let final := (List.range 300).foldl (fun (ns : List (SectionNode 12)) _ =>
    flatGDStep ns η) nodes
  let φ := potential final
  IO.println s!"[TEST] flat_gd_fails: φ = {φ}"
  if φ > 5000 then
    IO.println "[PASS] flat GD walks off manifold (φ > 5000)"
  else
    IO.println s!"[FAIL] flat GD did not walk off: φ = {φ} (expected > 5000)"

/-! ## Test 2: Riemannian GD converges -/

/-- Curvature-aware GD (c=1) stays on the manifold and converges. -/
def test_riemannian_gd_converges : IO Unit := do
  let nodes := treeEmbedding
  let c := 1.0
  let η := 0.01
  -- Run 300 steps of Riemannian GD
  let final := (List.range 300).foldl (fun (ns : List (SectionNode 12)) _ =>
    riemannianGDStep ns c η) nodes
  let φ := potential final
  IO.println s!"[TEST] riemannian_gd_converges: φ = {φ}"
  if φ < 200 then
    IO.println "[PASS] Riemannian GD converges (φ < 200)"
  else
    IO.println s!"[FAIL] Riemannian GD did not converge: φ = {φ} (expected < 200)"

/-! ## Test 3: Ungated GRD does not settle -/

/-- GRD with Hamiltonian but no Payor gate (α_decay=0) does not settle. -/
def test_grd_no_gate_stirring : IO Unit := do
  let nodes := treeEmbedding
  let c := 1.0
  let h := { fullHeuristic 12 c with
    α_init := 1.0
    α_decay := 0.0
  }
  let trajectory := runGRD h nodes 300
  let std := trajectoryConvergence trajectory
  IO.println s!"[TEST] grd_no_gate_stirring: std = {std}"
  if std > 0.3 then
    IO.println "[PASS] Ungated GRD does not settle (std > 0.3)"
  else
    IO.println s!"[FAIL] Ungated GRD settled: std = {std} (expected > 0.3)"

/-! ## Test 4: Gated GRD converges -/

/-- GRD with Payor gate (α_decay=0.05) converges smoothly. -/
def test_grd_with_gate_converges : IO Unit := do
  let nodes := treeEmbedding
  let c := 1.0
  let h := fullHeuristic 12 c
  let trajectory := runGRD h nodes 300
  let std := trajectoryConvergence trajectory
  let acceptRate := acceptRate trajectory
  IO.println s!"[TEST] grd_with_gate_converges: std = {std}, accept_rate = {acceptRate}"
  if std < 0.1 then
    IO.println "[PASS] Gated GRD converges (std < 0.1)"
  else
    IO.println s!"[FAIL] Gated GRD did not converge: std = {std} (expected < 0.1)"

/-! ## Test 5: Gate accept rate -/

/-- The Payor gate accepts most steps early and tightens. -/
def test_grd_gate_accept_rate : IO Unit := do
  let nodes := treeEmbedding
  let c := 1.0
  let h := fullHeuristic 12 c
  let trajectory := runGRD h nodes 300
  let acceptRate := acceptRate trajectory
  IO.println s!"[TEST] grd_gate_accept_rate: accept_rate = {acceptRate}"
  if acceptRate > 0.8 then
    IO.println "[PASS] Gate accept rate > 0.8"
  else
    IO.println s!"[FAIL] Gate accept rate = {acceptRate} (expected > 0.8)"

/-! ## Test 6: GRD vs flat GD -/

/-- GRD (with gate) beats flat GD in convergence. -/
def test_grd_better_than_flat : IO Unit := do
  let nodes := treeEmbedding
  let c := 1.0
  let η := 0.01
  -- Flat GD
  let flatFinal := (List.range 300).foldl (fun (ns : List (SectionNode 12)) _ =>
    flatGDStep ns η) nodes
  let φ_flat := potential flatFinal
  -- Gated GRD
  let h := fullHeuristic 12 c
  let grdTrajectory := runGRD h nodes 300
  have h_grd_nonempty : grdTrajectory.length > 0 := by
    unfold runGRD
    induction' 300 with n ih
    · simp
    · simp [runGRD]
  let grdFinal := grdTrajectory.head h_grd_nonempty
  let φ_grd := potential grdFinal
  IO.println s!"[TEST] grd_better_than_flat: φ_GRD = {φ_grd}, φ_flat = {φ_flat}"
  if φ_grd < φ_flat then
    IO.println "[PASS] Gated GRD beats flat GD"
  else
    IO.println s!"[FAIL] GRD did not beat flat GD: φ_GRD = {φ_grd} >= φ_flat = {φ_flat}"

end GRDTests

/-! ## Main -/

/-- Run all GRD tests. -/
def main : IO Unit := do
  IO.println "=== GRD Convergence Tests ==="
  IO.println ""
  test_flat_gd_fails
  IO.println ""
  test_riemannian_gd_converges
  IO.println ""
  test_grd_no_gate_stirring
  IO.println ""
  test_grd_with_gate_converges
  IO.println ""
  test_grd_gate_accept_rate
  IO.println ""
  test_grd_better_than_flat
  IO.println ""
  IO.println "=== Tests complete ==="
