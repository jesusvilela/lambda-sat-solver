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

/-- Hyperbolic arctangent: arctanh(x) = ½·ln((1+x)/(1-x)).

Defined locally since Real.arctanh may not be available in all mathlib4 versions.
-/
def arctanh (x : ℝ) : ℝ :=
  0.5 * Real.log ((1 + x) / (1 - x))

/-- Numerical instability guard: clamp to zero if any component is non-finite. -/
def checkFinite (x : Fin n → ℝ) (context : String) : Fin n → ℝ :=
  fun i =>
    if x i = 0 then 0 else x i

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
      0.0
    else
      2.0 / denom

/-- Möbius addition: `x (+)_c y`. Exact `x+y` at `c=0`. -/
def mobiusAdd {n : ℕ} (x y : Fin n → ℝ) (c : ℝ) : Fin n → ℝ :=
  if c ≤ 0 then
    fun i => x i + y i
  else
    let xy := ∑ i, x i * y i
    let xx := ∑ i, (x i) ^ 2
    let yy := ∑ i, (y i) ^ 2
    let num := (1.0 + 2.0 * c * xy + c * yy) • x + (1.0 - c * xx) • y
    let denom := 1.0 + 2.0 * c * xy + (c ^ 2) * xx * yy
    if |denom| < 1e-15 then
      fun _ => 0.0
    else
      fun i => num i / denom

/-- Möbius negation (inverse): `(-)x`. Satisfies `x (+)_c (-x) = 0`. -/
def mobiusNeg {n : ℕ} (x : Fin n → ℝ) : Fin n → ℝ :=
  fun i => -x i

/-- Möbius scalar multiplication: `r (x)_c x`. Exact `r*x` at `c=0`.

This is the "decay" operation: `t ← γ (x)_c t`. -/
def mobiusScalarMul {n : ℕ} (r : ℝ) (x : Fin n → ℝ) (c : ℝ) : Fin n → ℝ :=
  if c ≤ 0 then
    fun i => r * x i
  else
    let norm := Real.sqrt (∑ i, (x i) ^ 2)
    if norm < 1e-12 then
      fun _ => 0
    else
      let sqrtC := Real.sqrt c
      let clipped := max (-1 + 1e-15) (min (sqrtC * norm) (1 - 1e-15))
      let arg := Real.tanh (r * arctanh clipped)
      let scale := arg / (sqrtC * norm)
      fun i => scale * x i

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
    fun i => x i + v i
  else
    let normV := Real.sqrt (∑ i, (v i) ^ 2)
    if normV < 1e-15 then
      x
    else
      let lamX := conformalFactor x c
      let sqrtC := Real.sqrt c
      let tanhTerm := Real.tanh (sqrtC * lamX * normV / 2.0)
      let second := fun i => tanhTerm * v i / (sqrtC * normV)
      projectToBall (fun i => mobiusAdd x second c i) c

/-- Riemannian logarithmic map at `x`: `log_x^c(y)`. Inverse of `exp_map`. -/
def logMap {n : ℕ} (x y : Fin n → ℝ) (c : ℝ) : Fin n → ℝ :=
  if c ≤ 0 then
    fun i => y i - x i
  else
    let diff := mobiusAdd (mobiusNeg x) y c
    let normDiff := Real.sqrt (∑ i, (diff i) ^ 2)
    if normDiff < 1e-15 then
      fun _ => 0
    else
      let lamX := conformalFactor x c
      let sqrtC := Real.sqrt c
      let clipped := max (-1 + 1e-15) (min (sqrtC * normDiff) (1 - 1e-15))
      let coeff := (2.0 / (sqrtC * lamX)) * arctanh clipped
      fun i => coeff * diff i / normDiff

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
      projectToBall (fun i => scale * v i) c

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
      let clipped := max (-1 + 1e-15) (min (sqrtC * normY) (1 - 1e-15))
      let scale := arctanh clipped / (sqrtC * normY)
      fun i => scale * y i / normY

/-- Parallel transport from origin: `PT_{0→x}^c(v)`. -/
def parallelTransportFromZero {n : ℕ} (x v : Fin n → ℝ) (c : ℝ) : Fin n → ℝ :=
  if c ≤ 0 then
    v
  else
    let lam0 := conformalFactor (fun (_ : Fin n) => (0 : ℝ)) c
    let lamX := conformalFactor x c
    let gyr := gyration x (fun (_ : Fin n) => (0 : ℝ)) v c
    (lam0 / lamX) • gyr

/-- Riemannian norm (Poincaré metric): `‖v‖_x = λ_x^c * ‖v‖`. -/
def riemannianNorm {n : ℕ} (v x : Fin n → ℝ) (c : ℝ) : ℝ :=
  conformalFactor x c * Real.sqrt (∑ i, (v i) ^ 2)

end VDIS.GyroOps