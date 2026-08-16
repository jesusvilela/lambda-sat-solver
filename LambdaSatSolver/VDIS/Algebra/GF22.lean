import Mathlib
import LambdaSatSolver.VDIS.Algebra.Basic

/-!
# GF(2,2) — The Field with 4 Elements

GF(2,2) is the finite field with 4 elements: {0, 1, ω, ω+1} where ω² = ω+1.
In characteristic 2, addition and subtraction coincide (x = -x for all x).

## Representation

Elements are `Fin 4` with the following encoding:
  0 = (0,0) = 0 + 0·ω
  1 = (1,0) = 1 + 0·ω
  ω = (0,1) = 0 + 1·ω
  ω+1 = (1,1) = 1 + 1·ω

Encoding: (a,b) ↦ b*2 + a, so element = a + b·ω.

## Multiplication Table

  * | 0  1  ω  ω+1
  -----------------
  0 | 0  0  0  0
  1 | 0  1  ω  ω+1
  ω | 0  ω ω+1  1
  ω+1| 0 ω+1  1  ω

## Addition Table (XOR)

  + | 0  1  ω  ω+1
  -----------------
  0 | 0  1  ω  ω+1
  1 | 1  0  ω+1 ω
  ω | ω ω+1 0  1
  ω+1| ω+1 ω 1  0

## Key Properties

- Characteristic 2: x + x = 0 for all x
- Multiplicative group is cyclic of order 3: ω³ = 1
- Frobenius automorphism: (a+b)² = a² + b²
- Norm: N(a+bω) = (a+bω)(a+bω²) = a² + ab + b²
- Trace: Tr(a+bω) = a + b

## Relation to Cayley-Dickson

GF(2,2) is the even subalgebra of the quaternion algebra over GF(2).
It provides the base field for the hypercomplex tower extension.
-/

namespace VDIS.Algebra.GF22

open Finset

/-!
## Element Encoding and Decoding

We encode GF(2,2) elements as `Fin 4` with the mapping:
  0 ↦ 0, 1 ↦ 1, ω ↦ 2, ω+1 ↦ 3

This matches the standard representation where the last bit
is the "imaginary" part.
-/

/-- Encode an element: 0, 1, ω, ω+1 as Fin 4 values 0, 1, 2, 3.
    Encoding: (a,b) ↦ b*2 + a where element = a + b·ω.
    So: (0,0)↦0, (1,0)↦1, (0,1)↦2, (1,1)↦3. -/
def encode (a : ZMod 2) (b : ZMod 2) : Fin 4 :=
  match a, b with
  | 0, 0 => ⟨0, by decide⟩
  | 1, 0 => ⟨1, by decide⟩
  | 0, 1 => ⟨2, by decide⟩
  | 1, 1 => ⟨3, by decide⟩

/-- Decode an element: Fin 4 value 0,1,2,3 to (a, b) where element = a + b·ω.
    Decoding: n ↦ (n%2, n/2). -/
def decode (x : Fin 4) : ZMod 2 × ZMod 2 :=
  let n := x.val
  have hn : n < 4 := x.is_lt
  (⟨n % 2, by
    have h : n % 2 < 2 := Nat.mod_lt n (by norm_num)
    exact h⟩,
   ⟨n / 2, by
    have h : n / 2 < 2 := by
      apply Nat.div_lt_of_lt_mul
      omega
    exact h⟩)

/-- Convert to ZMod 2 × ZMod 2 representation. -/
def toPair (x : Fin 4) : ZMod 2 × ZMod 2 := decode x

/-- Convert from ZMod 2 × ZMod 2 representation. -/
def fromPair (a b : ZMod 2) : Fin 4 := encode a b

/-!
## Field Operations

### Addition (XOR)

In characteristic 2, addition is XOR: (a,b) + (c,d) = (a+c, b+d).
-/

/-- Addition in GF(2,2): component-wise XOR. -/
def add (x y : Fin 4) : Fin 4 :=
  let (a, b) := decode x
  let (c, d) := decode y
  fromPair (a + c) (b + d)

/-- Negation in GF(2,2): x = -x (characteristic 2). -/
def neg (x : Fin 4) : Fin 4 := x

/-- Subtraction in GF(2,2): x - y = x + y (characteristic 2). -/
def sub (x y : Fin 4) : Fin 4 := add x y

/-!
## Multiplication

Multiplication in GF(2,2) follows the table:
  (a + bω)(c + dω) = (ac + bd) + (ad + bc + bd)ω

This comes from ω² = ω + 1.
-/

/-- Multiplication in GF(2,2): (a+bω)(c+dω) = (ac+bd) + (ad+bc+bd)ω.
    Derivation from ω² = ω+1:
    (a+bω)(c+dω) = ac + ad·ω + bc·ω + bd·ω²
                  = ac + (ad+bc)·ω + bd·(ω+1)
                  = ac + bd + (ad+bc+bd)·ω
                  = (ac+bd) + (ad+bc+bd)·ω

def mul (x y : Fin 4) : Fin 4 :=
  let (a, b) := decode x
  let (c, d) := decode y
  fromPair (a * c + b * d) (a * d + b * c + b * d)

/-- Multiplicative identity: 1 = 0 + 1·ω. -/
def one : Fin 4 := ⟨1, by decide⟩

/-- Additive identity: 0 = 0 + 0·ω. -/
def zero : Fin 4 := ⟨0, by decide⟩

/-!
## Ring Structure

We define the ring structure on Fin 4.
-/

instance : AddCommGroup (Fin 4) where
  add := add
  add_assoc := by
    intro x y z
    ext i
    fin_cases i <;> decide
  zero := zero
  zero_add := by
    intro x
    ext i
    fin_cases i <;> decide
  add_zero := by
    intro x
    ext i
    fin_cases i <;> decide
  nsmul := nsmulRec
  nsmul_zero := by intro x; rfl
  nsmul_succ := by
    intro n x
    induction n with
    | zero => rfl
    | succ n ih =>
      simp [add_comm, add_assoc, ih]
  add_comm := by
    intro x y
    ext i
    fin_cases i <;> decide
  sub_eq_add_neg := by
    intro x y
    ext i
    fin_cases i <;> decide
  zsmul := zsmulRec
  zsmul_zero' := by intro x; rfl
  zsmul_succ' := by
    intro n x
    induction n with
    | zero => rfl
    | succ n ih =>
      simp [add_comm, add_assoc, ih]
  zsmul_neg' := by
    intro n x
    simp [sub_eq_add_neg, add_comm, add_assoc]

instance : CommRing (Fin 4) where
  __ := (inferInstance : AddCommGroup (Fin 4))
  mul := mul
  one := one
  zero := zero
  mul_assoc := by
    intro x y z
    ext i
    fin_cases i <;> decide
  one_mul := by
    intro x
    ext i
    fin_cases i <;> decide
  mul_one := by
    intro x
    ext i
    fin_cases i <;> decide
  mul_comm := by
    intro x y
    ext i
    fin_cases i <;> decide
  left_distrib := by
    intro x y z
    ext i
    fin_cases i <;> decide
  right_distrib := by
    intro x y z
    ext i
    fin_cases i <;> decide
  mul_zero := by
    intro x
    ext i
    fin_cases i <;> decide
  zero_mul := by
    intro x
    ext i
    fin_cases i <;> decide
  natCast := fun n => nsmulRec n 1
  natCast_zero := rfl
  natCast_succ := by
    intro n
    simp [nsmul_add, add_comm, add_assoc]

/-!
## Field Structure

We prove that Fin 4 with these operations is a field.
-/

/-- The nonzero elements of GF(2,2) form a multiplicative group of order 3. -/
lemma mul_invariant (x : Fin 4) (hx : x ≠ zero) : ∃ y, mul x y = one := by
  -- Check all 3 nonzero elements
  have : Fintype (Fin 4) := inferInstance
  fin_cases x <;> decide

/-- Every nonzero element has a multiplicative inverse.
    Since GF(4)ˣ is cyclic of order 3 generated by ω, we have:
    ω⁻¹ = ω² = ω+1, (ω+1)⁻¹ = ω, 1⁻¹ = 1.
    This gives a computable inverse. -/
def inv (x : Fin 4) : Fin 4 :=
  if h : x = zero then zero
  else
    -- The three nonzero elements are 1, ω, ω+1
    -- 1⁻¹ = 1, ω⁻¹ = ω² = ω+1, (ω+1)⁻¹ = ω
    if x = one then one
    else if x = omega then omega_add_one
    else omega  -- must be ω+1

instance : Field (Fin 4) where
  __ := (inferInstance : CommRing (Fin 4))
  inv := inv
  mul_inv_cancel := by
    intro x hx
    dsimp [inv]
    -- Case analysis on the three nonzero elements
    fin_cases x <;> simp [omega, omega_add_one, mul, one, zero] at *
  inv_zero := by
    dsimp [inv]
    simp

/-!
## Characteristic 2 Properties
-/

/-- In characteristic 2, x + x = 0. -/
theorem add_self_eq_zero (x : Fin 4) : x + x = zero := by
  ext i
  fin_cases i <;> decide

/-- In characteristic 2, x - y = x + y. -/
theorem sub_eq_add (x y : Fin 4) : x - y = x + y := by
  simp [sub_eq_add_neg, add_comm, add_self_eq_zero]

/-!
## Frobenius Automorphism

In characteristic 2, (x + y)² = x² + y².
-/

/-- Frobenius endomorphism: (x + y)² = x² + y². -/
theorem frobenius_add (x y : Fin 4) : (x + y) ^ 2 = x ^ 2 + y ^ 2 := by
  calc
    (x + y) ^ 2 = (x + y) * (x + y) := by ring
    _ = x * x + x * y + y * x + y * y := by ring
    _ = x * x + (x * y + y * x) + y * y := by ring
    _ = x * x + (x * y + x * y) + y * y := by
      rw [mul_comm x y]
    _ = x * x + 0 + y * y := by rw [add_self_eq_zero (x * y)]
    _ = x * x + y * y := by simp
    _ = x ^ 2 + y ^ 2 := by ring

/-- Frobenius endomorphism on sum of three terms. -/
theorem frobenius_add_three (x y z : Fin 4) : (x + y + z) ^ 2 = x ^ 2 + y ^ 2 + z ^ 2 := by
  calc
    (x + y + z) ^ 2 = ((x + y) + z) ^ 2 := rfl
    _ = (x + y) ^ 2 + z ^ 2 := frobenius_add _ _
    _ = (x ^ 2 + y ^ 2) + z ^ 2 := by rw [frobenius_add]
    _ = x ^ 2 + y ^ 2 + z ^ 2 := by ring

/-!
## Norm and Trace

For an element a + bω ∈ GF(4):
  Norm(a + bω) = (a + bω)(a + bω²) = a² + ab + b²
  Trace(a + bω) = a + b (in GF(2))
-/

/-- Norm of an element in GF(2,2): N(a + bω) = a² + ab + b². -/
def norm (x : Fin 4) : Fin 4 :=
  let (a, b) := decode x
  -- a² + ab + b² (in GF(2), a² = a, b² = b)
  fromPair (a + a * b + b) 0

/-- Trace of an element in GF(2,2): Tr(a + bω) = a + b (in GF(2)). -/
def trace (x : Fin 4) : ZMod 2 :=
  let (a, b) := decode x
  a + b

/-!
## Multiplicative Group

The multiplicative group GF(4)ˣ is cyclic of order 3, generated by ω.
-/

/-- ω = 2 in our encoding. -/
def omega : Fin 4 := ⟨2, by decide⟩

/-- ω + 1 = 3 in our encoding. -/
def omega_add_one : Fin 4 := ⟨3, by decide⟩

/-- ω² = ω + 1. -/
theorem omega_sq : omega ^ 2 = omega_add_one := by
  ext i
  fin_cases i <;> decide

/-- ω³ = 1. -/
theorem omega_cube : omega ^ 3 = one := by
  calc
    omega ^ 3 = omega ^ 2 * omega := by ring
    _ = omega_add_one * omega := by rw [omega_sq]
    _ = one := by
      ext i
      fin_cases i <;> decide

/-- Every nonzero element is a power of ω. -/
theorem mul_cyclic (x : Fin 4) (hx : x ≠ zero) :
    x = one ∨ x = omega ∨ x = omega_add_one := by
  fin_cases x <;> simp [omega, omega_add_one] at *

/-!
## Basis Vectors

The standard basis {e₀, e₁, e₂, e₃} of GF(2,2) as a vector space over GF(2).
-/

/-- Standard basis vector e₀ = 1. -/
def e0 : Fin 4 → Fin 4 := fun i => if i.val = 0 then one else zero

/-- Standard basis vector e₁ = ω. -/
def e1 : Fin 4 → Fin 4 := fun i => if i.val = 1 then omega else zero

/-- Standard basis vector e₂ = ω+1. -/
def e2 : Fin 4 → Fin 4 := fun i => if i.val = 2 then omega_add_one else zero

/-- Standard basis vector e₃ = 0 (zero vector). -/
def e3 : Fin 4 → Fin 4 := fun i => if i.val = 3 then one else zero

/-!
## Conversion to/from ZMod 2 Components

We provide conversions between Fin 4 (GF(2,2)) and ZMod 2 × ZMod 2.
-/

/-- Convert GF(2,2) element to ZMod 2 × ZMod 2. -/
def toZMod2x2 (x : Fin 4) : ZMod 2 × ZMod 2 := decode x

/-- Convert ZMod 2 × ZMod 2 to GF(2,2) element. -/
def fromZMod2x2 (p : ZMod 2 × ZMod 2) : Fin 4 := fromPair p.1 p.2

/-!
## GF(GF(2,2),GF(2,2)) — The Field with 16 Elements

GF(GF(2,2),GF(2,2)) = GF(4²) = GF(16), the field with 16 elements.

### Representation

Elements are pairs (a, b) where a, b ∈ GF(2,2), representing a + b·j
with j² = j + ω (and ω² = ω + 1 in GF(2,2)).

### Multiplication

  (a + bj)(c + dj) = (ac + bd·ω) + (ad + bc + bd)j

Derivation: (a + bj)(c + dj) = ac + adj + bcj + bdj²
           = ac + (ad+bc)j + bd(j+ω)
           = (ac + bd·ω) + (ad + bc + bd)j

### Addition

Component-wise: (a + bj) + (c + dj) = (a+c) + (b+d)j.
-/

/-- GF(16) represented as pairs (a, b) with a, b ∈ GF(2,2). -/
def GF16 := Fin 4 × Fin 4

namespace GF16

/-- The element ω ∈ GF(2,2) used in the extension: ω² = ω + 1. -/
def omega : Fin 4 := VDIS.Algebra.GF22.omega

/-- Addition in GF(16): component-wise XOR. -/
def add (x y : GF16) : GF16 := (GF22.add x.1 y.1, GF22.add x.2 y.2)

/-- Negation in GF(16): identity in characteristic 2. -/
def neg (x : GF16) : GF16 := x

/-- Subtraction in GF(16): same as addition in characteristic 2. -/
def sub (x y : GF16) : GF16 := add x y

/-- Multiplication in GF(16):
    (a + bj)(c + dj) = (ac + bd·ω) + (ad + bc + bd)j
    where j² = j + ω. -/
def mul (x y : GF16) : GF16 :=
  let a := x.1; let b := x.2
  let c := y.1; let d := y.2
  (GF22.add (GF22.mul a c) (GF22.mul (GF22.mul b d) omega),
   GF22.add (GF22.add (GF22.mul a d) (GF22.mul b c)) (GF22.mul b d))

/-- Additive identity: (0, 0). -/
def zero : GF16 := (GF22.zero, GF22.zero)

/-- Multiplicative identity: (1, 0). -/
def one : GF16 := (GF22.one, GF22.zero)

/-- Additive group structure on GF(16). -/
instance : AddCommGroup GF16 where
  add := add
  add_assoc := by
    intro x y z
    ext <;> dsimp [add] <;> apply add_assoc
  zero := zero
  zero_add := by
    intro x
    ext <;> dsimp [add, zero] <;> apply zero_add
  add_zero := by
    intro x
    ext <;> dsimp [add, zero] <;> apply add_zero
  nsmul := nsmulRec
  nsmul_zero := by intro x; rfl
  nsmul_succ := by
    intro n x
    induction n with
    | zero => rfl
    | succ n ih =>
      simp [add_comm, add_assoc, ih]
  add_comm := by
    intro x y
    ext <;> dsimp [add] <;> apply add_comm
  sub_eq_add_neg := by
    intro x y
    ext <;> dsimp [sub, neg, add] <;> apply sub_eq_add_neg
  zsmul := zsmulRec
  zsmul_zero' := by intro x; rfl
  zsmul_succ' := by
    intro n x
    induction n with
    | zero => rfl
    | succ n ih =>
      simp [add_comm, add_assoc, ih]
  zsmul_neg' := by
    intro n x
    simp [sub_eq_add_neg, add_comm, add_assoc]

/-- GF(16) is a commutative ring with the custom multiplication. -/
instance : CommRing GF16 where
  __ := (inferInstance : AddCommGroup GF16)
  mul := mul
  one := one
  zero := zero
  mul_assoc := by
    decide
  one_mul := by
    intro x
    ext <;> dsimp [mul, one] <;> simp
  mul_one := by
    intro x
    ext <;> dsimp [mul, one] <;> simp
  mul_comm := by
    decide
  left_distrib := by
    decide
  right_distrib := by
    decide
  mul_zero := by
    intro x
    ext <;> dsimp [mul, zero] <;> simp
  zero_mul := by
    intro x
    ext <;> dsimp [mul, zero] <;> simp
  natCast := fun n => nsmulRec n 1
  natCast_zero := rfl
  natCast_succ := by
    intro n
    simp [nsmul_add, add_comm, add_assoc]

/-- Multiplicative inverse in GF(16).
    For (a,b) ≠ (0,0): (a,b)⁻¹ = ((a+b)/N, b/N)
    where N = a² + ab + b²·ω is the norm.
    
    Derivation: In the quadratic extension F[α]/F with α² = α + ω,
    the conjugate is α' = 1 + α, and:
    N(a+bα) = (a+bα)(a+bα') = a² + ab + b²ω
    (a+bα)⁻¹ = (a+bα')/N = ((a+b) + bα)/N
    So (a,b)⁻¹ = ((a+b)/N, b/N) where division by N means
    multiplying each component by N⁻¹ ∈ GF(2,2). -/
def inv (x : GF16) : GF16 :=
  let a := x.1; let b := x.2
  let N := GF22.add (GF22.add (GF22.mul a a) (GF22.mul a b)) (GF22.mul (GF22.mul b b) omega)
  if h : x = zero then
    zero
  else
    (GF22.mul (inv N) (GF22.add a b),
     GF22.mul (inv N) b)

/-- GF(16) is a field. -/
instance : Field GF16 where
  __ := (inferInstance : CommRing GF16)
  inv := inv
  mul_inv_cancel := by
    decide
  inv_zero := by
    dsimp [inv]
    simp [zero]

end GF16

/-!
## 3 XOR Orthogonality for GF(16)-Valued Vectors

We generalize 3 XOR orthogonality to vectors over GF(16).
-/

/-- 3 XOR orthogonality for three vectors over GF(16).
    u, v, w are pairwise orthogonal under the GF(16)-valued dot product. -/
def threeXorOrthogonalGF16 (u v w : Fin 4 → GF16) : Prop :=
  (∑ i : Fin 4, GF16.mul (u i) (v i)) = GF16.zero ∧
  (∑ i : Fin 4, GF16.mul (u i) (w i)) = GF16.zero ∧
  (∑ i : Fin 4, GF16.mul (v i) (w i)) = GF16.zero

/-!
## Spin Group Lifting for GF(16)

We generalize the spin lift to GF(16). The rotor construction uses
the first 3 basis vectors of GF(16) as a 4-dimensional vector space over GF(2).
-/

/-- Frame lifting to Spin(3, GF(16)) via the Clifford algebra construction.
    Given a 3-XOR-orthogonal frame {e₀, e₁, e₂} over GF(16),
    we construct a rotor R = (1 + e₀)(1 + e₁)(1 + e₂).
    In characteristic 2, R⁻¹ = R. -/
def spinLiftGF16 (frame : Fin 3 → Fin 4 → GF16) : Fin 4 → GF16 :=
  fun i =>
    let r0 := GF16.add GF16.one (frame 0 i)
    let r1 := GF16.add GF16.one (frame 1 i)
    let r2 := GF16.add GF16.one (frame 2 i)
    GF16.mul (GF16.mul r0 r1) r2

/-- The spin lift preserves 3 XOR orthogonality over GF(16). -/
theorem spinLiftGF16_preserves_orthogonality (frame : Fin 3 → Fin 4 → GF16)
    (h : threeXorOrthogonalGF16 (frame 0) (frame 1) (frame 2)) :
    threeXorOrthogonalGF16
      (fun i => spinLiftGF16 frame i)
      (fun i => spinLiftGF16 (fun j => frame ((j+1)%3)) i)
      (fun i => spinLiftGF16 (fun j => frame ((j+2)%3)) i) := by
  unfold threeXorOrthogonalGF16 spinLiftGF16
  decide

/-- Generalized spin lift preserves 3 XOR orthogonality over GF(16). -/
theorem spinLiftGF16_preserves_orthogonality_general (u v w : Fin 4 → GF16)
    (h : threeXorOrthogonalGF16 u v w) :
    threeXorOrthogonalGF16 (spinLiftGF16 (fun i => match i with | 0 => u | 1 => v | 2 => w))
      (spinLiftGF16 (fun i => match i with | 0 => v | 1 => w | 2 => u))
      (spinLiftGF16 (fun i => match i with | 0 => w | 1 => u | 2 => v)) := by
  unfold threeXorOrthogonalGF16 spinLiftGF16
  decide

end VDIS.Algebra.GF22/-!
## 3 XOR Orthogonality for Hypercomplex Vectors

We define 3 XOR orthogonality as a predicate on three vectors in GF(2,2)^n.
Three vectors u, v, w are 3-XOR-orthogonal if they are pairwise orthogonal
under the standard dot product with values in GF(2,2).

In characteristic 2, the dot product is:
  ⟨u, v⟩ = Σ u_i * v_i  (where * and + are in GF(2,2))

For "XOR orthogonality" in the hypercomplex setting, we consider the
dot product summed over all components, giving a result in GF(2,2).
If the result is 0, the vectors are orthogonal.

-/

/-- 3 XOR orthogonality for three vectors over GF(2,2).
    u, v, w are pairwise orthogonal under the GF(2,2)-valued dot product. -/
def threeXorOrthogonalHyper (u v w : Fin 4 → Fin 4) : Prop :=
  (∑ i : Fin 4, mul (u i) (v i)) = zero ∧
  (∑ i : Fin 4, mul (u i) (w i)) = zero ∧
  (∑ i : Fin 4, mul (v i) (w i)) = zero

/-- The standard basis frame {e₀, e₁, e₂, e₃} where:
    e₀ = (1,0,0,0), e₁ = (0,1,0,0), e₂ = (0,0,1,0), e₃ = (0,0,0,1). -/
def standardFrame (i : Fin 4) : Fin 4 → Fin 4 :=
  fun j => if j.val = i.val then one else zero

/-- The standard basis frame is NOT 3-XOR-orthogonal (they are orthonormal, not orthogonal).
    A proper 3-XOR-orthogonal frame requires vectors that sum to zero pairwise. -/
theorem standardFrame_not_threeXorOrthogonal :
    ¬ threeXorOrthogonalHyper (standardFrame 0) (standardFrame 1) (standardFrame 2) := by
  unfold threeXorOrthogonalHyper standardFrame
  simp [Finset.sum_finset, Finset.card_fin]
  decide

/-!
## Frame Lifting to Spin Group

Given a 3-XOR-orthogonal frame over GF(2,2), we can lift it to the
spin group Spin(3, GF(2,2)) via the Clifford algebra construction.

### Clifford Algebra Construction

The Clifford algebra Cl(3, GF(2,2)) is generated by e₁, e₂, e₃ with
the relation e_i * e_j + e_j * e_i = 0 for i ≠ j (characteristic 2).

For a 3-XOR-orthogonal frame, we have:
  e_i · e_j + e_j · e_i = 0 for i ≠ j

### Rotor Construction

Given a 3-XOR-orthogonal frame {e₁, e₂, e₃}, we construct a rotor:
  R = (1 + e₁)(1 + e₂)(1 + e₃)

This rotor lies in Spin(3) and implements rotations via the sandwich
R · v · R⁻¹ = R · v · R (since R⁻¹ = R in characteristic 2).

### Simultaneous Carriers

Given three 3-XOR-orthogonal frames with carriers c₀, c₁, c₂,
we construct a simultaneous spin lift that acts on all three frames.
-/



/-- Frame lifting to spin group: given a 3-XOR-orthogonal frame {e₀, e₁, e₂},
    we construct a rotor R = (1 + e₀)(1 + e₁)(1 + e₂) that lies in Spin(3).
    
    The rotor implements rotations via the sandwich R · v · R⁻¹.
    
    In characteristic 2, 1 + e = 1 - e, so the rotor formula simplifies. -/
def spinLift (frame : Fin 3 → Fin 4 → Fin 4) : Fin 4 → Fin 4 :=
  -- R = (1 + e₀)(1 + e₁)(1 + e₂)
  fun i =>
    let r0 := add one (frame 0 i)
    let r1 := add one (frame 1 i)
    let r2 := add one (frame 2 i)
    -- Product: r0 * r1 * r2 (component-wise)
    mul (mul r0 r1) r2

/-- Verify that the spin lift preserves 3 XOR orthogonality.
    If the frame is 3-XOR-orthogonal, the lifted rotor preserves the
    pairwise orthogonality under the extended multiplication. -/
theorem spinLift_preserves_orthogonality (frame : Fin 3 → Fin 4 → Fin 4)
    (h : threeXorOrthogonalHyper (frame 0) (frame 1) (frame 2)) :
    threeXorOrthogonalHyper
      (fun i => spinLift frame i)
      (fun i => spinLift (fun j => frame ((j+1)%3)) i)
      (fun i => spinLift (fun j => frame ((j+2)%3)) i) := by
  unfold threeXorOrthogonalHyper spinLift
  -- This is a finite computation: we can check all 4^4 = 256 cases
  decide

/-!
## Generalized Orthogonality Verification

The previous theorem only checks cyclic permutations of the frame.
We now prove that the spin lift preserves orthogonality for any three
3-XOR-orthogonal vectors.
-/

/-- Generalized spin lift preserves 3 XOR orthogonality.
    Given any three vectors u, v, w that are 3-XOR-orthogonal,
    their images under the spin lift are also 3-XOR-orthogonal. -/
theorem spinLift_preserves_orthogonality_general (u v w : Fin 4 → Fin 4)
    (h : threeXorOrthogonalHyper u v w) :
    threeXorOrthogonalHyper (spinLift (fun i => match i with | 0 => u | 1 => v | 2 => w))
      (spinLift (fun i => match i with | 0 => v | 1 => w | 2 => u))
      (spinLift (fun i => match i with | 0 => w | 1 => u | 2 => v)) := by
  unfold threeXorOrthogonalHyper spinLift
  decide



end VDIS.Algebra.GF22
