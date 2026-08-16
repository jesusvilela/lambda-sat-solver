import Mathlib

open Real

/-!
# VDIS Track B1, Phase 2 — Hypercomplex Algebra Operations

Operations for rotor/torsion channel (S3.4) and Clifford decision scalar (S3.6).

v1 algebras (Correction 1 — octonions excluded):
  - 'R' : m=1, trivial algebra, degenerate/Phase-1 configuration only.
  - 'C' : m=2, complex numbers; even subalgebra of Cl(2,0).
  - 'H' : m=4, quaternions; even subalgebra of Cl(3,0).

For A = C the algebra is commutative, so rotor sandwich is trivial.
S3.4 channel only carries information for noncommutative algebra H.
-/

noncomputable section

namespace VDIS.Algebra

/-- Quaternions (A = 'H', m = 4) — Hamilton product. -/
def quatMul (a b : Fin 4 → ℝ) : Fin 4 → ℝ :=
  fun i =>
    match i with
    | 0 => a 0 * b 0 - a 1 * b 1 - a 2 * b 2 - a 3 * b 3
    | 1 => a 0 * b 1 + a 1 * b 0 + a 2 * b 3 - a 3 * b 2
    | 2 => a 0 * b 2 - a 1 * b 3 + a 2 * b 0 + a 3 * b 1
    | 3 => a 0 * b 3 + a 1 * b 2 - a 2 * b 1 + a 3 * b 0

/-- Quaternion conjugate. -/
def quatConj (a : Fin 4 → ℝ) : Fin 4 → ℝ :=
  fun i =>
    if i = 0 then a 0 else -a i

/-- Quaternion exponential of a bivector. Returns unit quaternion (rotor). -/
def quatExpBivector (omega : Fin 3 → ℝ) : Fin 4 → ℝ :=
  let theta := Real.sqrt (∑ i, (omega i) ^ 2)
  let w := Real.cos theta
  let s : ℝ :=
    if theta > 1e-15 then
      Real.sin theta / theta
    else
      1.0
  fun i =>
    match i with
    | 0 => w
    | 1 => s * omega 0
    | 2 => s * omega 1
    | 3 => s * omega 2

/-- Quaternion normalization. -/
def quatNormalize (a : Fin 4 → ℝ) : Fin 4 → ℝ :=
  let n := Real.sqrt (∑ i, (a i) ^ 2)
  if n > 1e-15 then
    a / n
  else if a 0 = 0 then
    fun i => if i = 0 then 1.0 else 0.0
  else
    fun i => a i / n

/-- Quaternion sandwich: `r * a * conj(r)`. For unit `r` this is a rotation. -/
def quatSandwich (r a : Fin 4 → ℝ) : Fin 4 → ℝ :=
  quatMul (quatMul r a) (quatConj r)

/-- Complex multiplication (A = 'C', m = 2). -/
def cplxMul (a b : Fin 2 → ℝ) : Fin 2 → ℝ :=
  fun i =>
    match i with
    | 0 => a 0 * b 0 - a 1 * b 1
    | 1 => a 0 * b 1 + a 1 * b 0

/-- Complex conjugate. -/
def cplxConj (a : Fin 2 → ℝ) : Fin 2 → ℝ :=
  fun i => if i = 0 then a 0 else -a i

/-- Complex exponential of bivector. -/
def cplxExpBivector (omega : ℝ) : Fin 2 → ℝ :=
  fun i =>
    match i with
    | 0 => Real.cos omega
    | 1 => Real.sin omega

/-- Complex normalization. -/
def cplxNormalize (a : Fin 2 → ℝ) : Fin 2 → ℝ :=
  let n := Real.sqrt (∑ i, (a i) ^ 2)
  if n > 1e-15 then
    a / n
  else if a 0 = 0 then
    fun i => if i = 0 then 1.0 else 0.0
  else
    fun i => a i / n

/-- Complex sandwich (same as cplxMul since commutative). -/
def cplxSandwich (r a : Fin 2 → ℝ) : Fin 2 → ℝ :=
  cplxMul (cplxMul r a) (cplxConj r)

/-- Wedge product in ℝ³ (for H algebra). Returns bivector coords.

The wedge `u ^ v` has coordinates equal to MINUS the cross product:
u ^ v = (u₂v₃ - u₃v₂, u₃v₁ - u₁v₃, u₁v₂ - u₂v₁) = -(u × v). -/
def wedge3 (u v : Fin 3 → ℝ) : Fin 3 → ℝ :=
  fun i =>
    match i with
    | 0 => -(u 1 * v 2 - u 2 * v 1)
    | 1 => -(u 2 * v 0 - u 0 * v 2)
    | 2 => -(u 0 * v 1 - u 1 * v 0)

/-- Wedge product in ℝ² (for C algebra). Returns scalar. -/
def wedge2 (u v : Fin 2 → ℝ) : ℝ :=
  u 0 * v 1 - u 1 * v 0

/-- Algebra dimensions and dispatch table. -/
def algebraDims (algebra : String) : ℕ × ℕ :=
  match algebra with
  | "R" => (1, 0)
  | "C" => (2, 1)
  | "H" => (4, 3)
  | _ => throw <| RuntimeError.mk s!"unknown algebra {algebra}"

/-- Rotor exponential dispatch. -/
def rotorExp (omega : Fin 3 → ℝ) (algebra : String) : Fin 4 → ℝ :=
  match algebra with
  | "H" => quatExpBivector omega
  | "C" =>
    let θ := Real.sqrt (∑ i, (omega i) ^ 2)
    if θ > 1e-15 then
      fun i => if i = 0 then Real.cos θ else (Real.sin θ / θ) * omega (i-1)
    else
      fun i => if i = 0 then 1.0 else 0.0
  | _ => throw <| RuntimeError.mk s!"no rotor structure for algebra {algebra}"

/-- Rotor sandwich dispatch. -/
def rotorSandwich (r a : Fin 4 → ℝ) (algebra : String) : Fin 4 → ℝ :=
  match algebra with
  | "H" => quatSandwich r a
  | "C" => cplxSandwich r a
  | _ => throw <| RuntimeError.mk s!"no rotor structure for algebra {algebra}"

/-- Rotor normalization dispatch. -/
def rotorNormalize (a : Fin 4 → ℝ) (algebra : String) : Fin 4 → ℝ :=
  match algebra with
  | "H" => quatNormalize a
  | "C" => cplxNormalize a
  | _ => throw <| RuntimeError.mk s!"no rotor structure for algebra {algebra}"

/-- Vector part extraction (grade-1 vector from algebra element). -/
def vectorPart (element : Fin 4 → ℝ) (algebra : String) : Fin 3 → ℝ :=
  match algebra with
  | "H" => fun i => element (i+1)
  | "C" => fun i =>
    match i with
    | 0 => element 0
    | 1 => element 1
  | _ => throw <| RuntimeError.mk s!"no vector structure for algebra {algebra}"

/-- Wedge product dispatch. -/
def wedge (u v : Fin 3 → ℝ) (algebra : String) : Fin 3 → ℝ :=
  match algebra with
  | "H" => wedge3 u v
  | "C" =>
    let s := wedge2 u v
    fun i => if i = 0 then s else 0.0
  | _ => throw <| RuntimeError.mk s!"no wedge structure for algebra {algebra}"

/-- Identity rotor. -/
def identityRotor (algebra : String) : Fin 4 → ℝ :=
  match algebra with
  | "H" => fun i => if i = 0 then 1.0 else 0.0
  | "C" => fun i => if i = 0 then 1.0 else 0.0
  | "R" => fun i => if i = 0 then 1.0 else 0.0
  | _ => throw <| RuntimeError.mk s!"no rotor structure for algebra {algebra}"

end VDIS.Algebra