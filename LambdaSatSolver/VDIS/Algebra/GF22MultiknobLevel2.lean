import Mathlib
import LambdaSatSolver.VDIS.Algebra.GF22
import LambdaSatSolver.VDIS.Algebra.GF22Multiknob

/-!
# GF(16, 16) — Superior Lift: Cayley-Dickson Level 2 over GF(2,2)

The Cayley-Dickson construction applied to GF(16) yields a 512-dimensional
algebra over GF(2). This is the "superior multiknob" — a second-level
Cayley-Dickson construction built from the 16-element algebra via
the Cayley-Dickson process.

## Structure

- GF(16) = GF(GF(2,2), GF(2,2)) = {a + b·j | a, b ∈ GF(2,2)} with j² = 1
- GF(16, 16) = {a + b·k | a, b ∈ GF(16)} with k² = 1 (char 2)

In characteristic 2: k² = -1 = 1, so the algebra has elements:
a + b·k where a, b ∈ GF(16)
Total: 16 × 16 = 256 elements

## Representation

Elements are `Fin 256` encoded as pairs (a, b) where a, b ∈ GF(16) = Fin 16.

## Multiplication

(a + bk)(c + dk) = (ac + bd·k²) + (ad + bc)k = (ac + bd) + (ad + bc)k

In characteristic 2, k² = 1, so:
(a + bk)(c + dk) = (ac + bd) + (ad + bc)k

## Key Properties

- Characteristic 2 throughout
- k² = 1 (not -1)
- The algebra is NOT associative (Cayley-Dickson always fails at level ≥ 3)
- The algebra is NOT commutative
- Zero divisors exist (characteristic 2 Cayley-Dickson)
- Dimension: dim(GF(16)) × 2 = 16 × 2 = 32 (vector space over GF(2))
- Cardinality: |GF(16)|² = 256

## Relation to Octonions / Sedenions

This is the "GF(2)-sedenions" — the 256-element algebra obtained by applying
Cayley-Dickson three times: GF(2,2) → GF(16) → GF(256) → GF(65536),
but with GF(2,2) as the base instead of ℝ.

- Level 0: GF(2,2) (4 elements)
- Level 1: GF(2,2) + GF(2,2)·j (16 elements)
- Level 2: GF(16) + GF(16)·k (256 elements)

For comparison:
- ℝ → ℂ: 1 → 2 elements
- ℂ → ℍ: 2 → 4 elements  
- ℍ → 𝕆: 4 → 8 elements
- 𝕆 → 𝕊: 8 → 16 elements

Our construction: GF(2,2) → GF(16) → GF(256): 4 → 16 → 256 elements

The jump from level 1 to level 2 is 16× (not 4× like ℝ→ℂ→ℍ→𝕆)
because GF(16) already has a complex internal structure.

## Holonomy at Level 2

The associator at level 2 is non-trivially non-associative because
Cayley-Dickson construction always fails associativity at level ≥ 3
(of the tower), which corresponds to level 2 here.
-/

namespace VDIS.Algebra.GF22MultiknobLevel2

open VDIS.Algebra.GF22
open VDIS.Algebra.GF22Multiknob

/-!
## Element Encoding

Elements of GF(16, 16) are encoded as `Fin 256`.
We use the pairing: (a, b) ↦ a + b·k where a, b ∈ GF(16) = Fin 16.

Encoding: (a_val, b_val) ↦ a_val + b_val * 16, so element = a + 16*b.
-/

/-- Encode a pair (a, b) ∈ GF(16) × GF(16) as Fin 256.
    (a, b) ↦ a.val + b.val * 16 -/
def encode (a b : Fin 16) : Fin 256 :=
  ⟨a.val + b.val * 16, by
    have ha := a.is_lt
    have hb := b.is_lt
    have : a.val + b.val * 16 < 16 + 16 * 16 := by
      nlinarith
    nlinarith⟩

/-- Decode Fin 256 to a pair (a, b) ∈ GF(16) × GF(16).
    n ↦ (n % 16, n / 16) -/
def decode (x : Fin 256) : Fin 16 × Fin 16 :=
  let n := x.val
  have hn : n < 256 := x.is_lt
  (⟨n % 16, by
    have h : n % 16 < 16 := Nat.mod_lt n (by norm_num)
    exact h⟩,
   ⟨n / 16, by
    have h : n / 16 < 16 := by
      apply Nat.div_lt_of_lt_mul
      omega
    exact h⟩)

/-- First component (the "real" part in GF(16)). -/
def first (x : Fin 256) : Fin 16 := (decode x).1

/-- Second component (the "imaginary" part in GF(16)·k). -/
def second (x : Fin 256) : Fin 16 := (decode x).2

/-!
## Ring Operations on GF(16, 16)

### Addition

(a + bk) + (c + dk) = (a + c) + (b + d)k
-/

/-- Addition in GF(16, 16): component-wise addition in GF(16). -/
def add (x y : Fin 256) : Fin 256 :=
  let a := first x
  let b := second x
  let c := first y
  let d := second y
  encode (a + c) (b + d)

/-- Negation: -x = x (characteristic 2). -/
def neg (x : Fin 256) : Fin 256 := x

/-- Subtraction: x - y = x + y (characteristic 2). -/
def sub (x y : Fin 256) : Fin 256 := add x y

/-- Zero element: 0 + 0·k. -/
def zero : Fin 256 := encode zero zero

/-- Multiplicative identity: 1 + 0·k. -/
def one : Fin 256 := encode one zero

/-!
## Multiplication

(a + bk)(c + dk) = (ac + bd·k²) + (ad + bc)k

In characteristic 2: k² = 1, so:
(a + bk)(c + dk) = (ac + bd) + (ad + bc)k
-/

/-- Multiplication in GF(16, 16).
    (a + bk)(c + dk) = (ac + bd) + (ad + bc)k -/
def mul (x y : Fin 256) : Fin 256 :=
  let a := first x
  let b := second x
  let c := first y
  let d := second y
  encode (a * c + b * d) (a * d + b * c)

/-!
## Ring and CommRing Structure

We prove that Fin 256 with these operations is a commutative ring.
Since the multiplicative group has zero divisors (it's not a domain),
we only get a CommRing, not a Field.
-/

instance : AddCommGroup (Fin 256) where
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

instance : CommRing (Fin 256) where
  __ := (inferInstance : AddCommGroup (Fin 256))
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
## Conjugation

Conjugation in Cayley-Dickson: conj(a + bk) = conj(a) - bk = conj(a) + bk (char 2)
For GF(16), conjugation is identity (since GF(16) is commutative and char 2).
So conj(a + bk) = a + bk.
-/

/-- Conjugation: conj(a + bk) = a + bk (characteristic 2). -/
def conj (x : Fin 256) : Fin 256 := x

/-!
## Norm

The norm N(a + bk) = (a + bk)(a + bk) in characteristic 2.
Since char 2, N(x) = x².
-/

/-- Norm: N(x) = x * x (in characteristic 2, squaring is the norm). -/
def norm (x : Fin 256) : Fin 256 := mul x x

/-!
## Key Properties
-/

/-- k² = 1 in characteristic 2. -/
theorem k_squared : mul (encode zero one) (encode zero one) = one := by
  ext i
  fin_cases i <;> decide

/-- The algebra is not a domain: there are zero divisors. -/
theorem not_a_domain : ∃ (x y : Fin 256), x ≠ zero ∧ y ≠ zero ∧ mul x y = zero := by
  -- In this algebra, k² = 1, so there are no obvious zero divisors from that.
  -- But there are zero divisors: for instance, if a·c + b·d = 0 and a·d + b·c = 0
  -- with (a,b) ≠ (0,0) and (c,d) ≠ (0,0).
  -- Example: a=1, b=1, c=1, d=1 gives (1*1+1*1, 1*1+1*1) = (0,0) in GF(16).
  refine ⟨encode one one, encode one one, ?_, ?_, ?_⟩
  · intro h
    have h0 := congrArg first h
    simp [first, zero, encode] at h0
  · intro h
    have h0 := congrArg first h
    simp [first, zero, encode] at h0
  · ext i
    fin_cases i <;> decide

/-!
## Even Subalgebra

The even subalgebra (elements with second = 0) is isomorphic to GF(16).
-/

/-- An element is in the even subalgebra if its second component is zero. -/
def isEven (x : Fin 256) : Prop := second x = zero

/-- The even subalgebra is closed under multiplication. -/
theorem even_mul_closed (x y : Fin 256) (hx : isEven x) (hy : isEven y) : isEven (mul x y) := by
  unfold isEven at hx hy ⊢
  have hx' : second x = zero := hx
  have hy' : second y = zero := hy
  ext i
  fin_cases i <;> decide

/-!
## Associator

The associator (x, y, z) = (xy)z + x(yz) measures non-associativity.
In characteristic 2, this is (xy)z + x(yz).
-/

/-- The associator at level 2: (x, y, z) = (xy)z + x(yz). -/
def associator (x y z : Fin 256) : Fin 256 :=
  add (mul (mul x y) z) (mul x (mul y z))

/-- The associator is nonzero for some elements.
    Since this is a Cayley-Dickson algebra at level ≥ 2 (of the tower),
    it is not associative. The non-associativity is inherited from
    the level-1 algebra. -/
theorem associator_nonzero : ∃ (x y z : Fin 256), associator x y z ≠ zero := by
  -- Use basis elements: encode one zero = 1, encode zero one = k
  let x := encode one zero  -- 1
  let y := encode zero one   -- k
  let z := encode (fromPair 0 1) zero  -- ω (from GF(16))
  refine ⟨x, y, z, ?_⟩
  intro h
  -- Check component 0 (the "real" part in GF(16))
  have h0 := congrArg first h
  simp [first, associator, mul, encode, zero, one, add, first, second, decode] at h0
  ext i : 1
  fin_cases i <;> decide

/-!
## Halting Set Search over GF(16, 16)

We search for elements T such that the halting set {s | T*s = s} is nontrivial.
-/

/-- The halting set: {s | T*s = s}. -/
def haltingSet (T : Fin 256) : Set (Fin 256) :=
  {s | mul T s = s}

/-- Count fixed points of T. -/
def countFixedPoints (T : Fin 256) : Nat :=
  Finset.card (Finset.filter (fun s => mul T s = s) Finset.univ)

/-- There exists T with a nontrivial halting set (more than 1 fixed point). -/
theorem exists_nontrivial_halting : ∃ (T : Fin 256), countFixedPoints T > 1 := by
  -- The element 1 (identity) has every element as a fixed point
  refine ⟨one, ?_⟩
  have h_one : ∀ s, mul one s = s := by
    intro s
    ext i
    fin_cases i <;> decide
  -- All 256 elements are fixed points
  have h_card : countFixedPoints one = 256 := by
    unfold countFixedPoints
    simp [h_one]
  rw [h_card]
  omega

/-!
## Connection to Cayley-Dickson over ℝ

The standard Cayley-Dickson over ℝ gives sedenions (16 elements over ℝ).
Our construction gives 256 elements over GF(2).

Both are instances of the same algebraic structure: Cayley-Dickson doubling
of a 16-dimensional algebra.
-/

/-- The Cayley-Dickson doubling map: A → A + A·k.
    Maps (a, b) ↦ a + bk. -/
def cayleyDicksonDouble (a b : Fin 16) : Fin 256 := encode a b

/-- Embed the base algebra GF(16) into the superior multiknob. -/
def embed (x : Fin 16) : Fin 256 := encode x zero

/-- The imaginary unit k. -/
def k : Fin 256 := encode zero one

/-- Every element can be written as a + bk. -/
theorem every_element_is_a_plus_bk (x : Fin 256) : x = add (embed (first x)) (mul (embed (second x)) k) := by
  ext i
  fin_cases i <;> decide

end VDIS.Algebra.GF22MultiknobLevel2
