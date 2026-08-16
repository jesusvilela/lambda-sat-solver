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
    fun i => a i / n
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
    fun i => a i / n
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
  | _ => (0, 0)

/-- Rotor exponential dispatch. -/
def rotorExp (omega : Fin 3 → ℝ) (algebra : String) : Fin 4 → ℝ :=
  match algebra with
  | "H" => quatExpBivector omega
  | "C" =>
    let θ := Real.sqrt (∑ i, (omega i) ^ 2)
    if θ > 1e-15 then
      fun i => if i.val = 0 then Real.cos θ else (Real.sin θ / θ) * omega ⟨i.val - 1, by
        have h := i.is_lt
        have : i.val - 1 < 3 := by
          omega
        exact this⟩
    else
      fun i => if i.val = 0 then 1.0 else 0.0
  | _ => fun _ => 0.0

/-- Rotor sandwich dispatch.

For algebra 'C' (complex), the rotor r lives in the even subalgebra
so we extract its first 2 components, apply cplxSandwich, and embed
back into Fin 4. -/
def rotorSandwich (r a : Fin 4 → ℝ) (algebra : String) : Fin 4 → ℝ :=
  match algebra with
  | "H" => quatSandwich r a
  | "C" =>
    let r' : Fin 2 → ℝ := fun i => r ⟨i.val, by
      have h := i.is_lt
      omega⟩
    let a' : Fin 2 → ℝ := fun i => a ⟨i.val, by
      have h := i.is_lt
      omega⟩
    let result := cplxSandwich r' a'
    fun i =>
      match i with
      | ⟨0, _⟩ => result 0
      | ⟨1, _⟩ => result 1
      | ⟨2, _⟩ => 0.0
      | ⟨3, _⟩ => 0.0
  | _ => fun _ => 0.0

/-- Rotor normalization dispatch.

For algebra 'C' (complex), we normalize only the first 2 components
since the rotor lives in the even subalgebra of Cl(2,0). -/
def rotorNormalize (a : Fin 4 → ℝ) (algebra : String) : Fin 4 → ℝ :=
  match algebra with
  | "H" => quatNormalize a
  | "C" =>
    let n := Real.sqrt ((a 0) ^ 2 + (a 1) ^ 2)
    if n > 1e-15 then
      fun i => if i.val = 0 then a 0 / n else if i.val = 1 then a 1 / n else 0.0
    else
      fun i => if i.val = 0 then 1.0 else 0.0
  | _ => fun _ => 0.0

/-- Vector part extraction (grade-1 vector from algebra element).

For algebra 'H' (quaternions), returns components 1..3.
For algebra 'C' (complex), returns components 0..1 as a Fin 3
where index 0 = real part, index 1 = imag part, index 2 = 0. -/
def vectorPart (element : Fin 4 → ℝ) (algebra : String) : Fin 3 → ℝ :=
  match algebra with
  | "H" => fun i => element ⟨i.val + 1, by
      have h := i.is_lt
      omega⟩
  | "C" => fun i =>
    match i with
    | ⟨0, _⟩ => element 0
    | ⟨1, _⟩ => element 1
    | ⟨2, _⟩ => 0.0
  | _ => fun _ => 0.0

/-- Wedge product dispatch. Returns Fin 3 → ℝ for all algebras.
For 'H', cross product; for 'C', complex product (zero in imag/component 1);
for others, zero. -/
def wedge {n : ℕ} (u v : Fin n → ℝ) (algebra : String) : Fin 3 → ℝ :=
  match algebra with
  | "H" =>
    fun i =>
      if hi : i.val < 3 then
        let u3 : Fin 3 → ℝ := fun k =>
          if hk : (k : ℕ) < n then u ⟨k.val, hk⟩ else 0.0
        let v3 : Fin 3 → ℝ := fun k =>
          if hk : (k : ℕ) < n then v ⟨k.val, hk⟩ else 0.0
        let cp := wedge3 u3 v3
        cp i
      else 0.0
  | "C" =>
    fun i =>
      if i.val = 0 then
        let u' : Fin 2 → ℝ := fun k =>
          if hk : (k : ℕ) < n then u ⟨k.val, hk⟩ else 0.0
        let v' : Fin 2 → ℝ := fun k =>
          if hk : (k : ℕ) < n then v ⟨k.val, hk⟩ else 0.0
        wedge2 u' v'
      else 0.0
  | _ => fun _ => 0.0

/-- Identity rotor. -/
def identityRotor (algebra : String) : Fin 4 → ℝ :=
  match algebra with
  | "H" => fun i => if i.val = 0 then 1.0 else 0.0
  | "C" => fun i => if i.val = 0 then 1.0 else 0.0
  | "R" => fun i => if i.val = 0 then 1.0 else 0.0
  | _ => fun _ => 0.0

end VDIS.Algebra