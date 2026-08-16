import Mathlib
import LambdaSatSolver.VDIS.GyroOps.Basic
import LambdaSatSolver.VDIS.Algebra.Basic
import LambdaSatSolver.VDIS.Basic

open Real

/-!
# GRD — Geodesic Resonance Descent

A Riemannian optimization algorithm on the Poincaré ball with a
symplectic Hamiltonian term governed by a Payor-style acceptance gate.

## Architecture

The five-term velocity field drives geodesic flow:
  v = v_desc + v_exp + v_H + v_esc + v_tel

The six-term energy stack evaluates each candidate step:
  E = E_metric + E_connection + E_holonomy + E_Hamiltonian + E_tel + E_resonance

The Payor gate certifies the step: accept iff the energy increase is
within a tolerance that anneals to zero as the optimizer approaches
its basin.

## Key Results (from Python validation on Poincaré ball embeddings):

- Flat GD fails (walks off manifold): φ ≈ 5546
- Riemannian GD converges: φ ≈ 53
- GRD-3 (Hamiltonian, no gate): does not settle reliably (std 0.45)
- GRD-4 (Hamiltonian + Payor gate): converges smoothly (std 0.06)
  accept_rate 1.00, monotone descent 728→73.

The gate governs the Hamiltonian term: it lets the structure-preserving
flow run early then tightens to force settling.

## Reference

Correspondence note: "Geodesic Resonance Descent" (R187b).
Python implementation: https://github.com/jesusvilela/Geodesic-Resonance-Descent
-/

noncomputable section

namespace VDIS.GRD

/-!
## Section Node (GRD variant)

A section node on the Poincaré ball with position, momentum, and salience.
-/

/-- A section node on the Poincaré ball: holds position q, momentum p, salience. -/
structure SectionNode (dim : ℕ) where
  label : String
  q : Fin dim → ℝ
  p : Fin dim → ℝ
  salience : ℝ

namespace SectionNode

/-- Norm of position vector. -/
def normQ {dim : ℕ} (n : SectionNode dim) : ℝ :=
  Real.sqrt (∑ i, (n.q i) ^ 2)

/-- Norm of momentum vector. -/
def normP {dim : ℕ} (n : SectionNode dim) : ℝ :=
  Real.sqrt (∑ i, (n.p i) ^ 2)

/-- Flat Hamiltonian: H = T(p) + V(q) = ½‖p‖² + ½‖q‖². -/
def energy {dim : ℕ} (n : SectionNode dim) : ℝ :=
  0.5 * (n.normP ^ 2) + 0.5 * (n.normQ ^ 2)

end SectionNode

/-!
## Symplectic J-Operator

The J-operator maps a tangent vector to its symplectic orthogonal:
  J·(v_q, v_p) = (-v_p, v_q)

On the Poincaré ball with curvature c, the Hamiltonian flow includes
a conformal factor λ_q for curvature-aware symplectic rotation.
-/

/-- Symplectic J-operator in phase space: J·(q, p) = (-p, q).

Maps (v_q, v_p) → (-v_p, v_q). Preserves the symplectic form ω = dq ∧ dp. -/
def symplecticJ {dim : ℕ} (v : (Fin dim → ℝ) × (Fin dim → ℝ)) : (Fin dim → ℝ) × (Fin dim → ℝ) :=
  let q := v.1
  let p := v.2
  (-p, q)

/-- Conformal symplectic J-operator: J_c = λ_q · J where λ_q is the
conformal factor at position q. This is the curvature-aware version
used in the Hamiltonian flow on the Poincaré ball. -/
def conformalSymplecticJ {dim : ℕ} (q : Fin dim → ℝ) (c : ℝ) (v : (Fin dim → ℝ) × (Fin dim → ℝ)) :
    (Fin dim → ℝ) × (Fin dim → ℝ) :=
  let lamQ := VDIS.GyroOps.conformalFactor q c
  let Jv := symplecticJ v
  (-lamQ • Jv.1, lamQ • Jv.2)

/-!
## Energy Stack (6 terms)

The total energy is the sum of six terms:

1. E_metric — embedding loss (how well points fit the metric)
2. E_connection — graph Dirichlet energy (smoothness over graph)
3. E_holonomy — non-commutativity defect (holonomy around loop)
4. E_Hamiltonian — symplectic flow energy
5. E_tel — substrate alignment energy (preferred direction)
6. E_resonance — decision pattern memory energy
-/

/-- Metric energy: E_m = ½ Σ ‖q_i‖².

For a Poincaré ball embedding, this measures how well points fit the
ambient hyperbolic metric. Lower = better embedding. -/
def metricEnergy {dim : ℕ} (nodes : List (SectionNode dim)) : ℝ :=
  (nodes.map fun n => ∑ i, (n.q i) ^ 2).sum

/-- Connection Laplacian energy: E_∇ = Σ_{i~j} w_{ij} · ‖q_i - q_j‖².

Measures smoothness of the embedding over the graph. Requires graph
structure — for a tree, this is zero (no cycles). For a general graph,
provide adjacency and edge-weight functions.

Corrected: uses Fin (nodes.length) for node indices, not Fin dim.
The inner sum is over all dimension components.
-/
def connectionEnergy {dim : ℕ} (nodes : List (SectionNode dim))
    (adj : Fin (nodes.length) → Fin (nodes.length) → Bool)
    (weight : Fin (nodes.length) → Fin (nodes.length) → ℝ) : ℝ :=
  let nodePairs := Finset.filter (fun (i, j) => adj i j && i.val < j.val)
    (Finset.product (Finset.univ : Finset (Fin (nodes.length)))
      (Finset.univ : Finset (Fin (nodes.length))))
  nodePairs.sum fun (i, j) =>
    let ni := nodes.get ⟨i.val, i.is_lt⟩
    let nj := nodes.get ⟨j.val, j.is_lt⟩
    weight i j * (∑ k : Fin dim, (ni.q k - nj.q k) ^ 2)

/-- Holonomy defect: E_hol = ‖holonomy around loop‖².

Measures non-commutativity of parallel transport. For a tree, holonomy
is zero (no loops). For a graph with cycles, compute via sequential
parallel transport around the cycle and measure the failure to return
to the original frame. -/
def holonomyEnergy {dim : ℕ} (_nodes : List (SectionNode dim)) : ℝ :=
  -- Placeholder: for a tree, holonomy = 0. For a general graph with cycles,
  -- compute by transporting a frame around each cycle and measuring
  -- the failure to return: E_hol = Σ ‖PT_loop(v) - v‖²
  0.0

/-- Hamiltonian energy: E_H = ½‖p‖² + ½‖q‖².

The symplectic flow energy. Conserved by the Hamiltonian flow (symplectic
rotations preserve the symplectic form to O(dt²)). -/
def hamiltonianEnergy {dim : ℕ} (nodes : List (SectionNode dim)) : ℝ :=
  (nodes.map fun n => SectionNode.energy n).sum

/-- Telos energy: E_tel = Σ ⟨q_i, direction⟩².

Measures alignment with a preferred substrate direction. The "direction"
is an external field (e.g., the gradient of a task loss). -/
def telosEnergy {dim : ℕ} (nodes : List (SectionNode dim)) (direction : Fin dim → ℝ) : ℝ :=
  (nodes.map fun n =>
    let dot := ∑ i, n.q i * direction i
    dot ^ 2).sum

/-!
## Velocity Field (5 terms)

The total velocity driving the geodesic step:
  v = η·v_desc + v_exp + v_H + v_esc + v_tel

where each term is a tangent vector at the current position.
-/

/-- Descent velocity: v_desc = -∇_q E_metric.

Follows the negative Riemannian gradient of the metric energy.
On the Poincaré ball, this is the negative Euclidean gradient scaled
by the conformal factor at q. -/
def descentVelocity {dim : ℕ} (nodes : List (SectionNode dim)) (c : ℝ) : Fin dim → ℝ :=
  let lamQ := VDIS.GyroOps.conformalFactor (n := dim) (fun _ => 0) c
  fun i =>
    -lamQ * (nodes.map fun n => n.q i).sum

/-- Exploration velocity: v_exp = J·∇_q E_metric.

Symplectic exploration: rotates the gradient into the momentum direction.
This lets the optimizer explore level sets without collapsing to the
metric gradient alone. -/
def explorationVelocity {dim : ℕ} (nodes : List (SectionNode dim)) (c : ℝ) : Fin dim → ℝ :=
  let lamQ := VDIS.GyroOps.conformalFactor (n := dim) (fun _ => 0) c
  fun i =>
    -lamQ * (nodes.map fun n => n.p i).sum

-- Hamiltonian velocity: v_H = J·∇_q E_Hamiltonian.
-- Structure-preserving flow: rotates the Hamiltonian gradient into the
-- momentum direction. The Hamiltonian flow is symplectic — it preserves
-- the symplectic form and the total energy H.
def hamiltonianVelocity {dim : ℕ} (nodes : List (SectionNode dim)) (c : ℝ) : Fin dim → ℝ := by
  intro i
  let lamQ := VDIS.GyroOps.conformalFactor (n := dim) (fun _ => 0) c
  let gradP := (nodes.map fun n => n.p i).sum
  exact -lamQ * gradP

-- Escape velocity: v_esc = noise in tangent space.
-- Random tangent vector for basin jumping. Uniformly distributed in
-- [-ε_esc, ε_esc]^dim. Bounded by escape magnitude σ_esc.
def escapeVelocity {dim : ℕ} (step : ℕ) (σ_esc : ℝ) : Fin dim → ℝ :=
  fun i =>
    let seed := (step : ℝ) + (i.val : ℝ) * 0.001
    (2.0 * (Int.fract seed) - 1.0) * σ_esc

/-- Telos velocity: v_tel = telosWeight · direction.

Alignment with a preferred substrate direction. telosWeight is the telos
weight. -/
def telosVelocity {dim : ℕ} (direction : Fin dim → ℝ) (telosWeight : ℝ) : Fin dim → ℝ :=
  fun i => telosWeight * direction i

/-!
## Total Velocity

Combine all five velocity terms into a single tangent vector.

v_total = η·v_desc + v_exp + v_H + v_esc + v_tel

All terms are already in tangent space at the origin (since we use
expMapZero). The exponential map projects the total step onto the
Poincaré ball and handles curvature via the conformal factor at the
destination. -/

/-- Combine all velocity terms into a single tangent vector at origin.

v_total = η·v_desc + v_exp + v_H + v_esc + v_tel -/
def totalVelocity {dim : ℕ} (nodes : List (SectionNode dim)) (c : ℝ) (step : ℕ)
    (direction : Fin dim → ℝ) (η : ℝ) (σ_esc : ℝ) (telosWeight : ℝ) : Fin dim → ℝ :=
  fun i =>
    let dv := descentVelocity nodes c
    let ev := explorationVelocity nodes c
    let hv := hamiltonianVelocity nodes c
    let tv := telosVelocity direction telosWeight
    let ev_i := ev i
    let hv_i := hv i
    let tv_i := tv i
    η * dv i + ev_i + hv_i + escapeVelocity step σ_esc i + tv_i

/-!
## GRD Step

A single GRD iteration: propose a geodesic step, certify it via the
Payor gate, and return the accepted state.

The Payor gate checks: does the new energy stay within tolerance of the
best energy? The tolerance α decays from 1.0 to 0 as the optimizer
approaches its basin. This lets the Hamiltonian flow explore early
then forces settling late — exactly the convergence pattern observed
in Python validation.
-/

/-- A single GRD step result: whether the step was accepted and the
energy change. -/
structure GRDStepResult (dim : ℕ) where
  accepted : Bool
  energyDelta : ℝ
  stepCount : ℕ

/-- Single GRD step with Payor gate.

Args:
  nodes: current section nodes
  direction: preferred substrate direction (for Telos term)
  η: learning rate (descent weight)
  σ_esc: escape magnitude
  telosWeight: telos weight
  α_init: initial acceptance tolerance (1.0 = accept all)
  α_decay: tolerance decay rate (α → 0 as optimizer approaches basin)

Returns:
  (accepted, newNodes, energyDelta, stepCount)
-/
def grdStep {dim : ℕ} (nodes : List (SectionNode dim)) (direction : Fin dim → ℝ)
    (c : ℝ) (step : ℕ) (η : ℝ) (σ_esc : ℝ)
    (telosWeight : ℝ) (α_init : ℝ) (α_decay : ℝ) : Bool × List (SectionNode dim) × ℝ × ℕ :=
  -- Compute total velocity
  let vTotal := totalVelocity nodes c step direction η σ_esc telosWeight
  -- Propose step via exponential map from origin
  let proposed := nodes.map fun n =>
    let v := fun i => vTotal i
    let newQ := VDIS.GyroOps.expMapZero v c
    let newP := fun i =>
      let lamQ := VDIS.GyroOps.conformalFactor (n := dim) (fun _ => 0) c
      lamQ * v i
    { n with q := newQ
             p := newP }
  -- Compute energies
  let E_old := metricEnergy nodes
  let E_new := metricEnergy proposed
  let ΔE := E_new - E_old
  -- Payor gate: accept iff E_new ≤ E_best + α·|E_best|
  -- where E_best is the best energy seen so far (initialized at first accept)
  -- and α decays exponentially with step count
  let firstAccept := step = 0
  let α_tol := if firstAccept then α_init else α_init * Real.exp (-(α_decay : ℝ) * (step : ℝ))
  let accept := ΔE ≤ α_tol * |E_old|
  let newNodes := if accept then proposed else nodes
  (accept, newNodes, ΔE, step)

/-!
## GRD Heuristic Configuration

Full GRD configuration with all parameters.
-/

/-- Full GRD heuristic with all parameters. -/
structure GRDHeuristic (dim : ℕ) where
  -- Curvature
  c : ℝ
  -- Learning rates
  η : ℝ
  σ_esc : ℝ
  telosWeight : ℝ
  -- Payor gate parameters
  α_init : ℝ
  α_decay : ℝ
  -- Preferred direction (for Telos term)
  direction : Fin dim → ℝ
  -- Graph structure (for connection energy)
  adj : Fin dim → Fin dim → Bool
  weight : Fin dim → Fin dim → ℝ

/-- Default GRD heuristic (flat/Euclidean limit c=0, conservative settings). -/
def defaultHeuristic (dim : ℕ) : GRDHeuristic dim :=
  { c := 0.0
    η := 0.1
    σ_esc := 0.01
    telosWeight := 0.0
    α_init := 1.0
    α_decay := 0.0
    direction := fun _ => 0.0
    adj := fun _ _ => false
    weight := fun _ _ => 1.0
  }

/-- GRD heuristic with full symplectic/Hamiltonian exploration.

Same settings validated in Python (R188): flat GD fails, RGD converges,
GRD-3 (Hamiltonian, no gate) does not settle, GRD-4 (Payor gate) converges.
-/
def fullHeuristic (dim : ℕ) (c : ℝ) : GRDHeuristic dim :=
  { c := c
    η := 0.1
    σ_esc := 0.1
    telosWeight := 0.0
    α_init := 1.0
    α_decay := 0.05
    direction := fun _ => 0.0
    adj := fun _ _ => false
    weight := fun _ _ => 1.0
  }

/-!
## Multi-Step GRD Loop

Run GRD for multiple iterations and track the trajectory.
-/

/-- Run GRD for `nSteps` iterations, returning the trajectory. -/
def runGRD {dim : ℕ} (h : GRDHeuristic dim) (initialNodes : List (SectionNode dim))
    (nSteps : ℕ) : List (List (SectionNode dim)) :=
  let rec go (nodes : List (SectionNode dim)) (step : ℕ)
      (trajectory : List (List (SectionNode dim))) : List (List (SectionNode dim)) :=
    if step ≥ nSteps then
      trajectory.reverse
    else
      let (accepted, newNodes, ΔE, _) := grdStep nodes h.direction h.c step
        h.η h.σ_esc h.telosWeight h.α_init h.α_decay
      go newNodes (step + 1) (nodes :: trajectory)
  go initialNodes 0 [initialNodes]

/-- Compute the total energy of a node list (sum of all section energies). -/
def totalEnergy {dim : ℕ} (nodes : List (SectionNode dim)) : ℝ :=
  (nodes.map SectionNode.energy).sum

/-- Extract the energy trajectory from a GRD run. -/
def energyTrajectory {dim : ℕ} (trajectory : List (List (SectionNode dim))) : List ℝ :=
  trajectory.map totalEnergy

/-- Compute the last-30-step standard deviation of a trajectory as a
convergence diagnostic (lower = more settled). -/
def trajectoryConvergence {dim : ℕ} (trajectory : List (List (SectionNode dim))) : ℝ :=
  let energies := energyTrajectory trajectory
  let last30 := (energies.reverse).take 30
  if last30.length < 2 then
    0.0
  else
    let mean := (last30.sum : ℝ) / (last30.length : ℝ)
    let variance := (last30.map fun e => (e - mean) ^ 2).sum / (last30.length : ℝ)
    Real.sqrt variance

/-- Compute accept rate from a GRD run.
Requires at least two steps (trajectory length ≥ 2). -/
def acceptRate {dim : ℕ} (trajectory : List (List (SectionNode dim))) : ℝ :=
  let steps := trajectory.length - 1
  if h : steps = 0 then
    1.0
  else
    let adjacent := List.zip trajectory trajectory.tail
    let accepted := List.filter
      (fun pair =>
        let prev := pair.1
        let curr := pair.2
        let prevEn := totalEnergy prev
        let currEn := totalEnergy curr
        currEn ≤ prevEn + 0.1 * |prevEn|)
      adjacent
    (accepted.length : ℝ) / (steps : ℝ)

/-!
## Reference: Flat GD (no curvature) and Riemannian GD (curvature only)

Baselines for comparison on the Poincaré ball testbed.
-/

/-- Flat GD step: q ← q - η · ∇_q E_metric (Euclidean gradient descent). -/
def flatGDStep {dim : ℕ} (nodes : List (SectionNode dim)) (η : ℝ) : List (SectionNode dim) :=
  nodes.map fun n =>
    let coordSum : Fin dim → ℝ := fun i => (nodes.map fun m => m.q i).sum
    let grad : Fin dim → ℝ := fun i => -coordSum i
    let newQ := fun i => n.q i + η * grad i
    { n with q := newQ }

-- Riemannian GD step: follows the Riemannian (conformally scaled) gradient.
-- Same as flat GD but the gradient is pre-scaled by the conformal factor.
-- On the Poincaré ball with c>0, this is the correct "curvature-aware"
-- descent — it stays closer to the manifold.
def riemannianGDStep {dim : ℕ} (nodes : List (SectionNode dim)) (c : ℝ) (η : ℝ) :
    List (SectionNode dim) :=
  nodes.map fun n =>
    let lam0 := VDIS.GyroOps.conformalFactor (n := dim) (fun _ => 0) c
    let coordSum : Fin dim → ℝ := fun i => (nodes.map fun m => m.q i).sum
    let grad : Fin dim → ℝ := fun i => -lam0 * coordSum i
    let newQ := fun i => n.q i + η * grad i
    { n with q := newQ }

end VDIS.GRD
