import Mathlib

open Real

/-!
# VDIS Track B1, Phase 1 — Möbius Gyrovector Operations on the Poincaré Ball

Closed-form Möbius gyrovector operations (Ungar's gyrovector spaces;
formulas as used in Ganea, Becigneul & Hofmann, "Hyperbolic Neural
Networks", NeurIPS 2018).

## Convention
The spec writes curvature `κ < 0`. This module takes curvature
MAGNITUDE `c = -κ ≥ 0` throughout (`c=0` is Euclidean limit,
`c>0` gives standard Ganea et al. formulas over a ball of radius
`1/√c`). Mixing sign conventions is a silent, hard-to-catch bug.
-/

noncomputable section

namespace VDIS.GyroOps

/-- Numerical instability guard: raise if any component is non-finite. -/
def checkFinite (x : Fin n → ℝ) (where : String) : Fin n → ℝ :=
  if h : ∀ i, x i ∈ Set.finite (Set.univ : Set ℝ) then
    x
  else
    throw <| RuntimeError.mk s!"non-finite value produced in {where}"

/-- Ball radius for curvature magnitude `c ≥ 0` (`c=0` is unbounded). -/
def maxNorm (c : ℝ) : ℝ :=
  if c ≤ 0 then
    0  -- represents ∞
  else
    1 / Real.sqrt c - 1e-5

/-- Clamp a point to stay strictly inside the ball (numerics requirement). -/
def projectToBall {n : ℕ} (x : Fin n → ℝ) (c : ℝ) : Fin n → ℝ :=
  let r := maxNorm c
  let norm := Real.sqrt (∑ i, (x i) ^ 2)
  if norm > r then
    fun i => x i * (r / norm)
  else
    x

/-- Conformal factor: λ_x^c = 2 / (1 - c * ‖x‖²). -/
def conformalFactor {n : ℕ} (x : Fin n → ℝ) (c : ℝ) : ℝ :=
  if c ≤ 0 then
    2.0
  else
    let denom := 1.0 - c * (∑ i, (x i) ^ 2)
    if denom ≤ 1e-15 then
      throw <| RuntimeError.mk s!"conformal factor denominator collapsed: {denom}"
    2.0 / denom

/-- Möbius addition: `x (+)_c y`. Exact `x+y` at `c=0`. -/
def mobiusAdd {n : ℕ} (x y : Fin n → ℝ) (c : ℝ) : Fin n → ℝ :=
  if c ≤ 0 then
    checkFinite (fun i => x i + y i) "mobius_add(c=0)"
  else
    let xy := ∑ i, x i * y i
    let xx := ∑ i, (x i) ^ 2
    let yy := ∑ i, (y i) ^ 2
    let num := (1.0 + 2.0 * c * xy + c * yy) • x + (1.0 - c * xx) • y
    let denom := 1.0 + 2.0 * c * xy + (c ^ 2) * xx * yy
    if |denom| < 1e-15 then
      throw <| RuntimeError.mk s!"mobius_add denominator collapsed: {denom}"
    checkFinite (fun i => num i / denom) "mobius_add"

/-- Möbius negation (inverse): `(-)x`. Satisfies `x (+)_c (-x) = 0`. -/
def mobiusNeg {n : ℕ} (x : Fin n → ℝ) : Fin n → ℝ :=
  fun i => -x i

/-- Möbius scalar multiplication: `r (x)_c x`. Exact `r*x` at `c=0`.

This is the "decay" operation: `t ← γ (x)_c t`. -/
def mobiusScalarMul {n : ℕ} (r : ℝ) (x : Fin n → ℝ) (c : ℝ) : Fin n → ℝ :=
  if c ≤ 0 then
    checkFinite (fun i => r * x i) "mobius_scalar_mul(c=0)"
  else
    let norm := Real.sqrt (∑ i, (x i) ^ 2)
    if norm < 1e-12 then
      fun _ => 0
    else
      let sqrtC := Real.sqrt c
      let arg := Real.tanh (r * Real.arctanh (Real.clip (sqrtC * norm) (-1 + 1e-15) (1 - 1e-15)))
      let scale := arg / (sqrtC * norm)
      checkFinite (fun i => scale * x i)

/-- Gyration: `gyr[x,y]v`, computed via its defining identity.

`x (+)_c (y (+)_c v) = (x (+)_c y) (+)_c gyr[x,y]v`

Three Möbius additions — slower but correctness reduces to `mobius_add`. -/
def gyration {n : ℕ} (x y v : Fin n → ℝ) (c : ℝ) : Fin n → ℝ :=
  if c ≤ 0 then
    v
  else
    mobiusAdd (mobiusNeg (mobiusAdd x y c)) (mobiusAdd x (mobiusAdd y v c) c) c

/-- Riemannian exponential map at `x`: `exp_x^c(v)`. Exact `x+v` at `c=0`. -/
def expMap {n : ℕ} (x v : Fin n → ℝ) (c : ℝ) : Fin n → ℝ :=
  if c ≤ 0 then
    checkFinite (fun i => x i + v i) "exp_map(c=0)"
  else
    let normV := Real.sqrt (∑ i, (v i) ^ 2)
    if normV < 1e-15 then
      x
    else
      let lamX := conformalFactor x c
      let sqrtC := Real.sqrt c
      let second := Real.tanh (sqrtC * lamX * normV / 2.0) • v / (sqrtC * normV)
      projectToBall (mobiusAdd x second c) c

/-- Riemannian logarithmic map at `x`: `log_x^c(y)`. Inverse of `exp_map`. -/
def logMap {n : ℕ} (x y : Fin n → ℝ) (c : ℝ) : Fin n → ℝ :=
  if c ≤ 0 then
    checkFinite (fun i => y i - x i) "log_map(c=0)"
  else
    let diff := mobiusAdd (mobiusNeg x) y c
    let normDiff := Real.sqrt (∑ i, (diff i) ^ 2)
    if normDiff < 1e-15 then
      fun _ => 0
    else
      let lamX := conformalFactor x c
      let sqrtC := Real.sqrt c
      let coeff := (2.0 / (sqrtC * lamX)) * Real.arctanh (Real.clip (sqrtC * normDiff) (-1 + 1e-15) (1 - 1e-15))
      (coeff • diff) / normDiff

/-- Exponential map from origin: `exp_0^c(v)`. -/
def expMapZero {n : ℕ} (v : Fin n → ℝ) (c : ℝ) : Fin n → ℝ :=
  if c ≤ 0 then
    v
  else
    let normV := Real.sqrt (∑ i, (v i) ^ 2)
    if normV < 1e-15 then
      fun _ => 0
    else
      let sqrtC := Real.sqrt c
      let scale := Real.tanh (sqrtC * normV) / (sqrtC * normV)
      projectToBall (scale • v) c

/-- Logarithmic map from origin: `log_0^c(y)`. -/
def logMapZero {n : ℕ} (y : Fin n → ℝ) (c : ℝ) : Fin n → ℝ :=
  if c ≤ 0 then
    y
  else
    let normY := Real.sqrt (∑ i, (y i) ^ 2)
    if normY < 1e-15 then
      fun _ => 0
    else
      let sqrtC := Real.sqrt c
      let scale := Real.arctanh (Real.clip (sqrtC * normY) (-1 + 1e-15) (1 - 1e-15)) / (sqrtC * normY)
      scale • y / normY

/-- Parallel transport from origin: `PT_{0→x}^c(v)`. -/
def parallelTransportFromZero {n : ℕ} (x v : Fin n → ℝ) (c : ℝ) : Fin n → ℝ :=
  if c ≤ 0 then
    v
  else
    let lam0 := conformalFactor (fun _ => 0) c
    let lamX := conformalFactor x c
    let gyr := gyration x (fun _ => 0) v c
    (lam0 / lamX) • gyr

/-- Riemannian norm (Poincaré metric): `‖v‖_x = λ_x^c * ‖v‖`. -/
def riemannianNorm {n : ℕ} (v x : Fin n → ℝ) (c : ℝ) : ℝ :=
  conformalFactor x c * Real.sqrt (∑ i, (v i) ^ 2)

end VDIS.GyroOps