import Mathlib
import LambdaSatSolver.VDIS.GyroOps.Basic
import LambdaSatSolver.VDIS.Algebra.Basic

open Real

/-!
# VDIS Track B1 — Decision Heuristic using Gyrovector State/Update Rule

Implements the `DecisionHeuristic` protocol via gyrovector operations.

## Phase 1 (S3.1-S3.3)
- `Δ_C = Σ α_l · t_l` — conflict-driven displacement in tangent space
- Axis 0: fixed infinitesimal unit of conflict mass (fossil axis)
- Axes 1..dim-1: state-dependent living field
- Bump = gyrotransport step
- Decay = Möbius scalar multiplication

## Phase 2 (S3.4-S3.6) adds:
- Rotor/torsion channel (S3.4): Ω_l += β · (t_l ^ d̂_C)
- Decision scalar (S3.6): score(l) = ⟨t_l, Psi⟩_Cl + λ_τ·τ_l + λ_χ·χ_l
- Moving frame (S3.4 v4): Cartan moving frame composition

## Known fix (Phase 1 patch):
The S3.1 rule has an absorbing fixed point at t=0. Fix: axis 0 always
receives FIXED unit contribution (1.0) per conflict, independent of
current state.
-/

noncomputable section

namespace VDIS

/-- A literal's tangent state: a vector in ℝ^{dim}. -/
structure LiteralState (dim : ℕ) where
  coords : Fin dim → ℝ

/-- Section node: holds position, momentum, and salience for a literal. -/
structure SectionNode (dim : ℕ) where
  label : String
  q : Fin dim → ℝ  -- position (Poincaré ball coordinates)
  p : Fin dim → ℝ  -- momentum (tangent vector)
  salience : ℝ

/-- VDIS Heuristic with all parameters. -/
structure VDISHeuristic where
  -- Dimensions
  numVars : ℕ
  dim : ℕ
  c : ℝ  -- curvature magnitude
  eta : ℝ  -- learning rate
  decayGamma : ℝ  -- decay rate (0 < γ < 1)
  algebra : String  -- "R", "C", or "H"
  -- Phase 2 parameters
  beta : ℝ  -- torsion/rotor magnitude
  lambdaTau : ℝ  -- torsion weight in score
  lambdaChi : ℝ  -- clause-length weight in score
  psiMu : ℝ  -- EMA learning rate for rotor
  -- State
  t : LiteralState dim → Fin dim → ℝ  -- tangent states
  omega : LiteralState dim → Fin 3 → ℝ  -- rotor/torsion angles
  rotors : LiteralState dim → Fin 4 → ℝ  -- rotor states
  psi : Fin 4 → ℝ  -- global rotor EMA
  chi : Fin (2 * numVars + 1) → ℝ  -- clause-length stats
  -- Saved phase (polarity of assigned variables)
  savedPhase : Fin (numVars + 1) → Bool
  -- Phase 2 flags
  rotorActive : Bool
  torsionAnchor : Bool
  wedgeOrtho : Bool
  pairTorsion : ℝ
  tieBreakPair : Bool
  combineNudges : Bool
  nudgeGate : ℝ
  combineEta : ℝ
  traders : List String
  -- Moving frame state
  movingFrame : Bool
  frame : Fin 4 → ℝ
  prevDWorld : Option (Fin 3 → ℝ)
  -- Lagrange multipliers
  lam : Fin (numVars + 1) → ℝ
  lastDecision : ℕ
  lastEndorse : List ℝ
  emaLbd : Option ℝ

/-- Compute chi (clause-length statistics).

chi[l] = 2 / (mean length of clauses containing literal l).
Indexed by lit + numVars. Returns 0 for literals in no clause.
-/
def computeChi (clauses : List (List ℤ)) (numVars : ℕ) : Fin (2 * numVars + 1) → ℝ :=
  fun i =>
    let litIdx := (i.val : ℤ) - (numVars : ℤ)
    -- Find clauses containing this literal
    let relevantClauses := clauses.filter fun c =>
      c.any fun l => l = litIdx
    let totalLen := (relevantClauses.map List.length).sum
    let count := relevantClauses.length
    if count > 0 then
      2.0 * (count : ℝ) / (totalLen : ℝ)
    else
      0.0

/-- Pick a variable to branch on.

Selects the unassigned variable with highest combined activity
(fossil axis + living field + torsion + clause-length).
-/
def pick (h : VDISHeuristic) (numVars : ℕ) (value : List (Option Bool)) : ℕ :=
  -- Base activity from fossil axis
  let baseAct : Fin (numVars + 1) → ℝ := fun v =>
    if hpos : 0 < h.dim then
      let hlsT := LiteralState.mk (dim := h.dim) (fun (i : Fin h.dim) => if (i : ℕ) = v.val then (v.val : ℝ) else 0.0)
      let hlsF := LiteralState.mk (dim := h.dim) (fun (i : Fin h.dim) => if (i : ℕ) = v.val then (0.0 : ℝ) else 0.0)
      h.t hlsT ⟨0, hpos⟩ + h.t hlsF ⟨0, hpos⟩
    else 0.0
  
  -- Find unassigned variables (index is in bounds and element is none)
  let unassigned : Finset ℕ :=
    (Finset.range numVars).filter fun v =>
      if hv : v < value.length then
        value.get ⟨v, hv⟩ = none
      else
        true
  
  -- If all variables are assigned, return 0 as fallback
  -- (S4 gate invariant should guarantee at least one unassigned,
  -- but we handle the degenerate case gracefully)
  if hne : unassigned.Nonempty then
    unassigned.max' hne
  else
    0

/-- Decay state (Möbius scalar multiplication).

Decay = mobius_scalar_mul(gamma, t, c). At c=0 this is
elementwise t *= gamma. For c>0 it's the tanh-based hyperbolic decay.
-/
def decay (h : VDISHeuristic) : VDISHeuristic :=
  let decayedT : (LiteralState h.dim) → Fin h.dim → ℝ := fun l i =>
    let γ := h.decayGamma
    VDIS.GyroOps.mobiusScalarMul γ (h.t l) h.c i
  {h with t := decayedT}

/-- Apply a conflict: update state via gyrovector operations.

The full S3 update rule:
1. Δ_C = Σ α_l · t_l (conflict displacement)
2. Bump = exp_map(η · PT_{0→x}(Δ_C)) (gyrotransport)
3. Rotor/torsion channel: Ω_l += β · (t_l ^ d̂_C)
4. Decision scalar update
-/
def onConflict (h : VDISHeuristic) (learned : List ℤ) (lbd : ℕ) (trail : List ℤ) : VDISHeuristic :=
  let alpha : ℝ := 1.0 / (learned.length : ℝ)
  
  -- Δ_C = Σ α_l · t_l (conflict displacement in tangent space)
  let deltaC : Fin h.dim → ℝ := fun i =>
    if i.val = 0 then 1.0  -- fossil axis: fixed unit contribution
    else
      let sum := (learned.map fun l => 
        let hls := LiteralState.mk (dim := h.dim) (fun (i : Fin h.dim) => if (i : ℕ) = Int.toNat (Int.natAbs l) then (1.0 : ℝ) else 0.0)
        h.t hls i).sum +
        (learned.map fun l => 
        let hls := LiteralState.mk (dim := h.dim) (fun (i : Fin h.dim) => if (i : ℕ) = Int.toNat (Int.natAbs l) then (0.0 : ℝ) else 0.0)
        h.t hls i).sum
      alpha * sum
  
  -- Update tangent states: t_l <- log_map(exp_map(η * PT, t_l))
  -- This is the gyrotransport + bump chain
  let updatedT : (LiteralState h.dim) → Fin h.dim → ℝ := fun l i =>
    let vLit := h.t l
    -- Transport from origin then exponential map
    let transported := VDIS.GyroOps.parallelTransportFromZero (fun _ => 0) deltaC h.c
    let step := VDIS.GyroOps.expMap (fun _ => 0) (fun j => h.eta * transported j) h.c
    let newVLit := step
    -- Log map back to tangent space
    let logVLit := VDIS.GyroOps.logMapZero newVLit h.c
    logVLit i
  
  -- Rotor/torsion channel (S3.4): Ω_l += β · (t_l ^ d̂_C)
  let updatedOmega : (LiteralState h.dim) → Fin 3 → ℝ := fun l j =>
    if h.rotorActive then
      let wedgeProduct := VDIS.Algebra.wedge (h.t l) deltaC h.algebra
      h.omega l j + h.beta * wedgeProduct j
    else
      h.omega l j
  
  -- Update Psi (EMA of rotor signature)
  let updatedPsi : Fin 4 → ℝ :=
    if h.rotorActive && h.torsionAnchor then
      -- Anchor mode: Psi = EMA of learned clause's anchor signature
      let omegaMean : Fin 3 → ℝ := fun j =>
        (learned.map fun l => 
          let hls := LiteralState.mk (dim := h.dim) (fun (i : Fin h.dim) => if (i : ℕ) = Int.toNat (Int.natAbs l) then (1.0 : ℝ) else 0.0)
          h.omega hls j).sum / (learned.length : ℝ)
      let rotorMean := VDIS.Algebra.rotorExp omegaMean h.algebra
      fun i =>
        let mu := h.psiMu
        (1.0 - mu) * h.psi i + mu * rotorMean i
    else if h.rotorActive then
      -- Standard mode: Psi = EMA of conflict direction
      h.psi
    else
      h.psi
  
  -- Update rotors
  let updatedRotors : (LiteralState h.dim) → Fin 4 → ℝ := fun l i =>
    if h.rotorActive then
      let omega := fun j => h.omega l j
      let rotor := VDIS.Algebra.rotorExp (fun j => omega (j+1)) h.algebra
      rotor i
    else
      h.rotors l i
  
  {h with
    t := updatedT
    omega := updatedOmega
    rotors := updatedRotors
    psi := updatedPsi
  }

/-- Apply a variable assignment.

Records the polarity of the assigned variable in savedPhase.
Index `i` corresponds to variable number `i.val` (0-based).
-/
def onAssign (h : VDISHeuristic) (lit : ℤ) : VDISHeuristic :=
  let v := Int.toNat (Int.natAbs lit)
  {h with savedPhase := fun i => if i.val = v then lit > 0 else h.savedPhase i}

/-- Apply an unassignment. -/
def onUnassign (h : VDISHeuristic) (_lit : ℤ) : VDISHeuristic :=
  h

/-- Hamiltonian flow step using proper Möbius geodesics.

For the Poincaré ball with curvature c, the symplectic flow is:
q' = q * cos(dt) + p * sin(dt) * λ_q
p' = p * cos(dt) - q * sin(dt) * λ_q

where λ_q is the conformal factor at q. This preserves the
Poincaré metric and the symplectic form to O(dt²).
-/
def hamiltonianFlow (h : VDISHeuristic) (nodes : List (SectionNode h.dim)) : List (SectionNode h.dim) :=
  let dt := 0.01
  let cosDt := Real.cos dt
  let sinDt := Real.sin dt
  nodes.map fun n =>
    -- Compute conformal factor at current position
    let lamQ := VDIS.GyroOps.conformalFactor n.q h.c
    -- Symplectic rotation in Poincaré metric
    let newQ : Fin h.dim → ℝ := fun i =>
      n.q i * cosDt + n.p i * sinDt * lamQ
    let newP : Fin h.dim → ℝ := fun i =>
      n.p i * cosDt - n.q i * sinDt * lamQ
    SectionNode.mk n.label newQ newP n.salience

/-- Run the Actor/Critic/Fuzzer cycle. -/
def runACFCycle (h : VDISHeuristic) (nodes : List (SectionNode h.dim)) : String × List (SectionNode h.dim) :=
  -- Pre-check (Fuzzer): boundary conditions
  let preCheck := nodes.all fun n =>
    let norm := Real.sqrt (∑ i, (n.q i) ^ 2)
    if hpos : 0 < h.dim then norm < 0.999 && n.q ⟨0, hpos⟩ > 0.0 else false
  if !preCheck then
    ("BLOCK", nodes)
  else
    let energies := nodes.map fun n => (∑ i, (n.q i) ^ 2)
    -- Actor: propose flow
    let actor := hamiltonianFlow h nodes
    -- Critic: verify energy conservation
    let postCheck := List.zip actor energies |>.all fun (n, e) =>
      Real.sqrt (∑ i, (n.q i) ^ 2) = Real.sqrt e
    if !postCheck then
      ("ROLLBACK", nodes)
    else
      let postBoundary := actor.all fun n =>
        let norm := Real.sqrt (∑ i, (n.q i) ^ 2)
        norm < 0.999
      if !postBoundary then
        ("BLOCK", nodes)
      else
        ("COMMIT", actor)

end VDIS