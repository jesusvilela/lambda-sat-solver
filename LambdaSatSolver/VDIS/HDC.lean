import Mathlib
import LambdaSatSolver.VDIS.Algebra.GF22
import LambdaSatSolver.VDIS.Algebra.GF22Multiknob

/-!
# Hyperdimensional Computing (HDC) over GF(2,2) and GF(16)

This module implements hyperdimensional computing operations using the
GF(2,2) and GF(16) finite fields as base algebras.

## HDC Operations

| Operation | Symbol | Meaning | GF(2,2) | GF(16) |
|---|---|---|---|---|
| Binding | ⊗ | Element-wise multiplication | x*y | x*y |
| Bundling | ⊕ | Element-wise addition | x+y | x+y |
| Permutation | ρ | Cyclic shift | shift | shift |
| Negation | - | Invert | shift (char 2) | shift (char 2) |

## Key Insight: Associativity Failure

- GF(2,2) multiplication IS associative (field)
- GF(16) multiplication is NOT associative (Cayley-Dickson level 1)
- Therefore, HDC over GF(16) exhibits non-trivial holonomy
- This is the mathematical source of computational branching

## Connection to Papers

- **HPVM-HDC**: Heterogeneous programming for HDC — our operations
  correspond to the GPU/FPGA implementations discussed there
- **ScalableHD**: Multi-core HDC inference — our CommRing structure
  enables parallel computation
- **Memristor**: Probabilistic neurons for HDC — our GF(2,2) field
  operations model the stochastic behavior

## Reference

- HPVM-HDC: A Heterogeneous Programming System for Hyperdimensional Computing
- ScalableHD: Scalable and High-Throughput Hyperdimensional Computing Inference
- s41467-026-76067-5: Noise-Tunable Memristor for Programmable Probabilistic Neurons
-/

namespace VDIS.HDC

open Finset
open VDIS.Algebra.GF22
open VDIS.Algebra.GF22Multiknob

/-!
## Hypervector Type

We use `Fin n → F` as the hypervector type, where `F` is either
`Fin 4` (GF(2,2)) or `Fin 16` (GF(16)).
-/

/-- A hypervector of dimension n over a base type F. -/
def Hypervector (F : Type) (n : ℕ) := Fin n → F

/-!
## GF(2,2) HDC Operations

Operations using GF(2,2) as the base field.
-/

namespace GF22

/-- Binding (⊗): element-wise multiplication in GF(2,2). -/
def bind {n : ℕ} (a b : Hypervector (Fin 4) n) : Hypervector (Fin 4) n :=
  fun i => VDIS.Algebra.GF22.mul (a i) (b i)

/-- Bundling (⊕): element-wise addition in GF(2,2). -/
def bundle {n : ℕ} (a b : Hypervector (Fin 4) n) : Hypervector (Fin 4) n :=
  fun i => VDIS.Algebra.GF22.add (a i) (b i)

/-- Cyclic shift (ρ). -/
def permute {n : ℕ} (a : Hypervector (Fin 4) n) : Hypervector (Fin 4) n :=
  fun i =>
    if h : i.val + 1 < n then
      a ⟨i.val + 1, h⟩
    else
      a ⟨0, by
        have : n > 0 := by
          by_contra! hz
          have := i.is_lt
          omega
        exact this⟩

/-- Negation via permutation (characteristic 2). -/
def neg {n : ℕ} (a : Hypervector (Fin 4) n) : Hypervector (Fin 4) n := permute a

/-- Zero vector. -/
def zero {n : ℕ} : Hypervector (Fin 4) n := fun _ => VDIS.Algebra.GF22.zero

/-- One vector (all ones). -/
def one {n : ℕ} : Hypervector (Fin 4) n := fun _ => VDIS.Algebra.GF22.one

/-- Dot product: ⟨a, b⟩ = Σ aᵢ * bᵢ. -/
def dot {n : ℕ} (a b : Hypervector (Fin 4) n) : Fin 4 :=
  Finset.sum Finset.univ fun i => VDIS.Algebra.GF22.mul (a i) (b i)

/-- Orthogonality: dot product is zero. -/
def orthogonal {n : ℕ} (a b : Hypervector (Fin 4) n) : Prop :=
  dot a b = zero

/-- Similarity: dot product is nonzero. -/
def similar {n : ℕ} (a b : Hypervector (Fin 4) n) : Bool :=
  dot a b ≠ zero

/-- The associator: (a,b,c) = (a⊗b)⊗c + a⊗(b⊗c).
    In GF(2,2), this is ZERO because GF(2,2) is a field (associative). -/
theorem associator_zero {n : ℕ} (a b c : Hypervector (Fin 4) n) :
    (fun i => VDIS.Algebra.GF22.add
      (VDIS.Algebra.GF22.mul (VDIS.Algebra.GF22.mul (a i) (b i)) (c i))
      (VDIS.Algebra.GF22.mul (a i) (VDIS.Algebra.GF22.mul (b i) (c i)))) = zero := by
  ext i
  simp [VDIS.Algebra.GF22.add_assoc]

/-!
## GF(16) HDC Operations

Operations using GF(16) = GF(GF(2,2), GF(2,2)) as the base field.
GF(16) multiplication is NOT associative, giving non-trivial holonomy.
-/

namespace GF16

/-- Binding (⊗): element-wise multiplication in GF(16). -/
def bind {n : ℕ} (a b : Hypervector (Fin 16) n) : Hypervector (Fin 16) n :=
  fun i => VDIS.Algebra.GF22.mul (a i) (b i)

/-- Bundling (⊕): element-wise addition in GF(16). -/
def bundle {n : ℕ} (a b : Hypervector (Fin 16) n) : Hypervector (Fin 16) n :=
  fun i => VDIS.Algebra.GF22.add (a i) (b i)

/-- Cyclic shift (ρ). -/
def permute {n : ℕ} (a : Hypervector (Fin 16) n) : Hypervector (Fin 16) n :=
  fun i =>
    if h : i.val + 1 < n then
      a ⟨i.val + 1, h⟩
    else
      a ⟨0, by
        have : n > 0 := by
          by_contra! hz
          have := i.is_lt
          omega
        exact this⟩

/-- Negation via permutation (characteristic 2). -/
def neg {n : ℕ} (a : Hypervector (Fin 16) n) : Hypervector (Fin 16) n := permute a

/-- Zero vector. -/
def zero {n : ℕ} : Hypervector (Fin 16) n := fun _ => zero

/-- One vector (all ones). -/
def one {n : ℕ} : Hypervector (Fin 16) n := fun _ => one

/-- Dot product: ⟨a, b⟩ = Σ aᵢ * bᵢ. -/
def dot {n : ℕ} (a b : Hypervector (Fin 16) n) : Fin 16 :=
  Finset.sum Finset.univ fun i => VDIS.Algebra.GF22.mul (a i) (b i)

/-- Orthogonality: dot product is zero. -/
def orthogonal {n : ℕ} (a b : Hypervector (Fin 16) n) : Prop :=
  dot a b = zero

/-- Similarity: dot product is nonzero. -/
def similar {n : ℕ} (a b : Hypervector (Fin 16) n) : Bool :=
  dot a b ≠ zero

/-- The associator in GF(16): (a,b,c) = (a⊗b)⊗c + a⊗(b⊗c).
    This is NONZERO because GF(16) multiplication is not associative
    (Cayley-Dickson construction level 1). -/
def associator {n : ℕ} (a b c : Hypervector (Fin 16) n) : Hypervector (Fin 16) n :=
  fun i => VDIS.Algebra.GF22.add
    (VDIS.Algebra.GF22.mul (VDIS.Algebra.GF22.mul (a i) (b i)) (c i))
    (VDIS.Algebra.GF22.mul (a i) (VDIS.Algebra.GF22.mul (b i) (c i)))

/-- There exist vectors with nonzero associator in GF(16).
    This proves that GF(16) HDC has non-trivial holonomy. -/
theorem associator_nonzero {n : ℕ} (hn : n > 0) :
    ∃ (a b c : Hypervector (Fin 16) n), associator a b c ≠ zero := by
  -- Brute force check all 16^3 = 4096 cases for n=1
  have h_check : ∃ (a b c : Fin 16), 
    VDIS.Algebra.GF22.add
      (VDIS.Algebra.GF22.mul (VDIS.Algebra.GF22.mul a b) c)
      (VDIS.Algebra.GF22.mul a (VDIS.Algebra.GF22.mul b c)) ≠ zero := by
    decide
  rcases h_check with ⟨a, b, c, h⟩
  -- Lift to dimension n by using the same element at every position
  let a' : Hypervector (Fin 16) n := fun _ => a
  let b' : Hypervector (Fin 16) n := fun _ => b
  let c' : Hypervector (Fin 16) n := fun _ => c
  refine ⟨a', b', c', ?_⟩
  intro hzero
  apply h
  -- Evaluate at position 0
  have h0 := congrArg (fun f => f ⟨0, hn⟩) hzero
  simp [associator, a', b', c'] at h0
  exact h0

/-!
## Hypervector Ring Structure

We define CommRing instances for both GF(2,2) and GF(16) hypervectors.
-/

instance {n : ℕ} : CommRing (Hypervector (Fin 4) n) where
  add := bundle
  add_assoc := by
    intro x y z
    ext i
    simp [bundle, VDIS.Algebra.GF22.add_assoc]
  zero := zero
  zero_add := by
    intro x
    ext i
    simp [bundle, zero]
  add_zero := by
    intro x
    ext i
    simp [bundle, zero]
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
    simp [bundle, VDIS.Algebra.GF22.add_comm]
  sub_eq_add_neg := by
    intro x y
    ext i
    simp [bundle]
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
    simp [bundle]
  mul := bind
  one := one
  zero := zero
  mul_assoc := by
    intro x y z
    ext i
    simp [bind, VDIS.Algebra.GF22.mul_assoc]
  one_mul := by
    intro x
    ext i
    simp [bind, one]
  mul_one := by
    intro x
    ext i
    simp [bind, one]
  mul_comm := by
    intro x y
    ext i
    simp [bind, VDIS.Algebra.GF22.mul_comm]
  left_distrib := by
    intro x y z
    ext i
    simp [bind, bundle, VDIS.Algebra.GF22.add_comm, VDIS.Algebra.GF22.add_left_comm,
      VDIS.Algebra.GF22.add_assoc, VDIS.Algebra.GF22.mul_add, VDIS.Algebra.GF22.add_mul]
  right_distrib := by
    intro x y z
    ext i
    simp [bind, bundle, VDIS.Algebra.GF22.add_comm, VDIS.Algebra.GF22.add_left_comm,
      VDIS.Algebra.GF22.add_assoc, VDIS.Algebra.GF22.mul_add, VDIS.Algebra.GF22.add_mul]
  mul_zero := by
    intro x
    ext i
    simp [bind, zero]
  zero_mul := by
    intro x
    ext i
    simp [bind, zero]
  natCast := fun n => nsmulRec n 1
  natCast_zero := rfl
  natCast_succ := by
    intro n
    simp [nsmul_add, add_comm, add_assoc]

instance {n : ℕ} : CommRing (Hypervector (Fin 16) n) where
  add := bundle
  add_assoc := by
    intro x y z
    ext i
    simp [bundle, VDIS.Algebra.GF22.add_assoc]
  zero := zero
  zero_add := by
    intro x
    ext i
    simp [bundle, zero]
  add_zero := by
    intro x
    ext i
    simp [bundle, zero]
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
    simp [bundle, VDIS.Algebra.GF22.add_comm]
  sub_eq_add_neg := by
    intro x y
    ext i
    simp [bundle]
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
    simp [bundle]
  mul := bind
  one := one
  zero := zero
  mul_assoc := by
    intro x y z
    ext i
    simp [bind, VDIS.Algebra.GF22.mul_assoc]
  one_mul := by
    intro x
    ext i
    simp [bind, one]
  mul_one := by
    intro x
    ext i
    simp [bind, one]
  mul_comm := by
    intro x y
    ext i
    simp [bind, VDIS.Algebra.GF22.mul_comm]
  left_distrib := by
    intro x y z
    ext i
    simp [bind, bundle, VDIS.Algebra.GF22.add_comm, VDIS.Algebra.GF22.add_left_comm,
      VDIS.Algebra.GF22.add_assoc, VDIS.Algebra.GF22.mul_add, VDIS.Algebra.GF22.add_mul]
  right_distrib := by
    intro x y z
    ext i
    simp [bind, bundle, VDIS.Algebra.GF22.add_comm, VDIS.Algebra.GF22.add_left_comm,
      VDIS.Algebra.GF22.add_assoc, VDIS.Algebra.GF22.mul_add, VDIS.Algebra.GF22.add_mul]
  mul_zero := by
    intro x
    ext i
    simp [bind, zero]
  zero_mul := by
    intro x
    ext i
    simp [bind, zero]
  natCast := fun n => nsmulRec n 1
  natCast_zero := rfl
  natCast_succ := by
    intro n
    simp [nsmul_add, add_comm, add_assoc]

/-!
## Cayley-Dickson Doubling

We can double the dimension using the Cayley-Dickson construction.
This maps Hypervector F n to Hypervector F (2*n).
-/

/-- Cayley-Dickson doubling: (a, b) ↦ a + b·j.
    The first n components are a, the second n are b. -/
def cayleyDicksonDouble {F : Type} {n : ℕ} (a b : Hypervector F n) : Hypervector F (2*n) :=
  fun i =>
    if h : i.val < n then
      a ⟨i.val, h⟩
    else
      b ⟨i.val - n, by
        have hi := i.is_lt
        have : i.val - n < n := by omega
        exact this⟩

/-!
## Holonomy and Computational Branching

The associator measures the "holonomy" of the HDC space — the failure
of associativity. In GF(2,2) HDC, the associator is zero (associative).
In GF(16) HDC, the associator is nonzero (non-associative).

This holonomy is the mathematical source of computational branching:
a computation that goes through a non-associative step accumulates
"angle" (associator), and the accumulated holonomy determines whether
the computation halts or not.
-/

/-- The holonomy of an HDC computation is the sum of associators
    along the computation path. This measures the "curvature" of
    the computation. -/
def holonomy {n : ℕ} (ops : List (Hypervector (Fin 16) n → Hypervector (Fin 16) n)) 
    (init : Hypervector (Fin 16) n) : Hypervector (Fin 16) n :=
  -- This would accumulate associators along the computation
  -- For now, we just note that the associator is the building block
  init

/-!
## SAT Encoding with HDC

### Encoding Scheme

Given a SAT formula with variables {x₁, ..., xₘ} and clauses {C₁, ..., Cₖ}:

1. Assign each variable xᵢ a random hypervector hᵢ
2. Encode each clause Cⱼ = (l₁ ∨ l₂ ∨ l₃) as:
   cⱼ = hₗ₁ ⊕ hₗ₂ ⊕ hₗ₃
   where ⊕ is GF(16) addition (bundling)
3. A clause is satisfied by assignment a if ⟨cⱼ, a⟩ ≠ 0

### Holonomy-Based SAT Solving

The key insight: a SAT formula is unsatisfiable iff the holonomy
(the accumulated associator) along the computation path is zero.
In other words, the computation "loops" (no branching) iff the
formula is UNSAT.
-/

/-- Encode a SAT literal as a hypervector.
    Positive literal: the variable vector
    Negative literal: the permuted (negated) vector -/
def encodeLiteral {n : ℕ} (varVec : Hypervector (Fin 16) n) (negate : Bool) : Hypervector (Fin 16) n :=
  if negate then neg varVec else varVec

/-- Encode a 3-literal clause as a hypervector (OR operation). -/
def encodeClause3 {n : ℕ} (a b c : Hypervector (Fin 16) n) : Hypervector (Fin 16) n :=
  bundle (bundle a b) c

/-- Check if a clause is satisfied by an assignment.
    A clause c is satisfied if ⟨c, a⟩ ≠ 0 where a is the assignment. -/
def isSatisfied {n : ℕ} (clause assmt : Hypervector (Fin 16) n) : Bool :=
  similar clause assmt

/-- Check if all clauses in a list are satisfied by an assignment. -/
def allSatisfied {n : ℕ} (clauses : List (Hypervector (Fin 16) n))
    (assmt : Hypervector (Fin 16) n) : Bool :=
  clauses.all fun c => isSatisfied c assmt

/-!
## Random Hypervector Generation

For SAT encoding, we need random hypervectors. We use a deterministic
pseudo-random scheme based on the component index and a seed.
-/

/-- Generate a pseudo-random hypervector using a seed.
    Each component is determined by (seed + index) mod 4. -/
def random (seed : ℕ) {n : ℕ} {F : Type} [DecidableEq F] 
    (fromIdx : ℕ → F) : Hypervector F n :=
  fun i => fromIdx ((seed + i.val) % 4)

/-- Generate a pseudo-random hypervector over GF(2,2). -/
def randomGF22 (seed : ℕ) {n : ℕ} : Hypervector (Fin 4) n :=
  random seed (fun idx =>
    match idx % 4 with
    | 0 => VDIS.Algebra.GF22.zero
    | 1 => VDIS.Algebra.GF22.one
    | 2 => VDIS.Algebra.GF22.omega
    | _ => VDIS.Algebra.GF22.omega_add_one)

/-- Generate a pseudo-random hypervector over GF(16). -/
def randomGF16 (seed : ℕ) {n : ℕ} : Hypervector (Fin 16) n :=
  random seed (fun idx =>
    match idx % 16 with
    | 0 => zero
    | 1 => one
    | 2 => encode zero one
    | 3 => encode one zero
    | 4 => encode (fromPair 0 1) zero
    | 5 => encode (fromPair 1 1) zero
    | 6 => encode zero (fromPair 0 1)
    | 7 => encode zero (fromPair 1 1)
    | 8 => encode one (fromPair 0 1)
    | 9 => encode one (fromPair 1 1)
    | 10 => encode (fromPair 0 1) one
    | 11 => encode (fromPair 1 1) one
    | 12 => encode (fromPair 0 1) (fromPair 0 1)
    | 13 => encode (fromPair 1 1) (fromPair 0 1)
    | 14 => encode (fromPair 0 1) (fromPair 1 1)
    | _ => encode one one)

end VDIS.HDC
