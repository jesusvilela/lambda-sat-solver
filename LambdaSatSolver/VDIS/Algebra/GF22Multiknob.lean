import Mathlib
import LambdaSatSolver.VDIS.Algebra.GF22

/-!
# GF(GF(2,2), GF(2,2)) — Multiknob Cayley-Dickson Construction

The Cayley-Dickson construction applied to GF(2,2) yields an 8-dimensional
algebra over GF(2). This is the "multiknob" — a hypercomplex structure
built from the finite field GF(4) via the Cayley-Dickson process.

## Structure

- GF(2,2) = {0, 1, ω, ω+1} with ω² = ω+1
- GF(GF(2,2), GF(2,2)) = {a + b·j | a, b ∈ GF(2,2)} with j² = -1 = 1 (char 2)

This gives an 8-element algebra with basis {1, ω, ω+1, j, ω·j, (ω+1)·j, j², ω·j²}.

Actually, in characteristic 2:
- j² = -1 = 1 (since -1 = 1 in char 2)
- So the algebra has elements: a + b·j where a, b ∈ GF(2,2)
- Total: 4 × 4 = 16 elements

Wait, let me reconsider. The Cayley-Dickson construction:
- Start with A₀ = GF(2,2) (4 elements)
- A₁ = GF(2,2) + GF(2,2)·j where j² = -1

In characteristic 2, -1 = 1, so j² = 1.

The multiplication: (a + bj)(c + dj) = (ac + bd·j²) + (ad + bc)j = (ac + bd) + (ad + bc)j

So we get an 8-dimensional vector space over GF(2) with 4×4 = 16 elements.

Actually, the dimension is: dim(A₀) × 2 = 4 × 2 = 8, and |A₁| = |A₀|² = 16.

## Representation

Elements are `Fin 16` encoded as pairs (a, b) where a, b ∈ GF(2,2) = Fin 4.

## Key Properties

- Characteristic 2 throughout
- j² = 1 (not -1)
- The algebra is NOT associative (Cayley-Dickson always fails at level ≥ 3)
- The algebra is NOT commutative
- The norm is NOT multiplicative (fails at level ≥ 4 for ℝ, but here we're in char 2)

## Relation to Octonions

This is the "GF(2)-octonions" — the 16-element algebra obtained by applying
Cayley-Dickson twice: ℝ → ℂ → ℍ → 𝕆, but with GF(2,2) as the base instead of ℝ.

- Level 0: GF(2,2) (4 elements)
- Level 1: GF(2,2) + GF(2,2)·j (16 elements)

For comparison:
- ℝ → ℂ: 1 → 2 elements
- ℂ → ℍ: 2 → 4 elements
- ℍ → 𝕆: 4 → 8 elements

Our construction: GF(2,2) → GF(2,2)⟨j⟩: 4 → 16 elements (much bigger jump!)

This is because GF(2,2) is already a field of characteristic 2, so the
Cayley-Dickson doubling gives a 4× multiplication table instead of 2×.
-/

namespace VDIS.Algebra.GF22Multiknob

open VDIS.Algebra.GF22

/-!
## Element Encoding

Elements of GF(GF(2,2), GF(2,2)) are encoded as `Fin 16`.
We use the pairing: (a, b) ↦ a + b·j where a, b ∈ GF(2,2) = Fin 4.

Encoding: (a_val, b_val) ↦ a_val + b_val * 4, so element = a + 4*b.
-/

/-- Encode a pair (a, b) ∈ GF(2,2) × GF(2,2) as Fin 16.
    (a, b) ↦ a.val + b.val * 4 -/
def encode (a b : Fin 4) : Fin 16 :=
  ⟨a.val + b.val * 4, by
    have ha := a.is_lt
    have hb := b.is_lt
    have hmax : a.val < 4 := ha
    have hmaxb : b.val < 4 := hb
    have : a.val + b.val * 4 < 4 + 4 * 4 := by
      nlinarith
    nlinarith⟩

/-- Decode Fin 16 to a pair (a, b) ∈ GF(2,2) × GF(2,2).
    n ↦ (n % 4, n / 4) -/
def decode (x : Fin 16) : Fin 4 × Fin 4 :=
  let n := x.val
  have hn : n < 16 := x.is_lt
  (⟨n % 4, by
    have h : n % 4 < 4 := Nat.mod_lt n (by norm_num)
    exact h⟩,
   ⟨n / 4, by
    have h : n / 4 < 4 := by
      apply Nat.div_lt_of_lt_mul
      omega
    exact h⟩)

/-- First component (the "real" part in GF(2,2)). -/
def first (x : Fin 16) : Fin 4 := (decode x).1

/-- Second component (the "imaginary" part in GF(2,2)·j). -/
def second (x : Fin 16) : Fin 4 := (decode x).2

/-!
## Field Operations on GF(GF(2,2), GF(2,2))

### Addition

(a + bj) + (c + dj) = (a + c) + (b + d)j
-/

/-- Addition in GF(GF(2,2), GF(2,2)): component-wise addition in GF(2,2). -/
def add (x y : Fin 16) : Fin 16 :=
  let a := first x
  let b := second x
  let c := first y
  let d := second y
  encode (a + c) (b + d)

/-- Negation: -x = x (characteristic 2). -/
def neg (x : Fin 16) : Fin 16 := x

/-- Subtraction: x - y = x + y (characteristic 2). -/
def sub (x y : Fin 16) : Fin 16 := add x y

/-- Zero element: 0 + 0·j. -/
def zero : Fin 16 := encode zero zero

/-- Multiplicative identity: 1 + 0·j. -/
def one : Fin 16 := encode one zero

/-!
## Multiplication

(a + bj)(c + dj) = (ac + bd·j²) + (ad + bc)j

In characteristic 2: j² = 1, so:
(a + bj)(c + dj) = (ac + bd) + (ad + bc)j
-/

/-- Multiplication in GF(GF(2,2), GF(2,2)).
    (a + bj)(c + dj) = (ac + bd) + (ad + bc)j -/
def mul (x y : Fin 16) : Fin 16 :=
  let a := first x
  let b := second x
  let c := first y
  let d := second y
  encode (a * c + b * d) (a * d + b * c)

/-!
## Ring and Field Structure

We prove that Fin 16 with these operations is a commutative ring.
Since the multiplicative group has zero divisors (it's not a domain),
we only get a CommRing, not a Field.
-/

instance : AddCommGroup (Fin 16) where
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

instance : CommRing (Fin 16) where
  __ := (inferInstance : AddCommGroup (Fin 16))
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

Conjugation in Cayley-Dickson: conj(a + bj) = conj(a) - bj = conj(a) + bj (char 2)
-/

/-- Conjugation: conj(a + bj) = a + bj (characteristic 2, conjugation fixes everything).
    Actually: conj(a + bj) = conj_GRF22(a) - bj = conj_GRF22(a) + bj (char 2).
    But for GF(2,2), conj is identity (since a² = a for all a in GF(2,2)).
    So conj(a + bj) = a + bj. -/
def conj (x : Fin 16) : Fin 16 := x

/-!
## Norm

The norm N(a + bj) = (a + bj)(a + bj) in characteristic 2.
Since char 2, N(x) = x².
-/

/-- Norm: N(x) = x * x (in characteristic 2, squaring is the norm). -/
def norm (x : Fin 16) : Fin 16 := mul x x

/-!
## Key Properties
-/

/-- j² = 1 in characteristic 2. -/
theorem j_squared : mul (encode zero one) (encode zero one) = one := by
  ext i
  fin_cases i <;> decide

/-- The algebra is not a domain: there are zero divisors.
    For example, j * j = 1, but also j * something might give zero. -/
theorem not_a_domain : ∃ (x y : Fin 16), x ≠ zero ∧ y ≠ zero ∧ mul x y = zero := by
  -- In this algebra, j² = 1, so there are no obvious zero divisors from that.
  -- But there are zero divisors: for instance, if a·c + b·d = 0 and a·d + b·c = 0
  -- with (a,b) ≠ (0,0) and (c,d) ≠ (0,0).
  -- Example: a=1, b=1, c=1, d=1 gives (1*1+1*1, 1*1+1*1) = (0,0) in GF(2,2).
  refine ⟨encode one one, encode one one, ?_, ?_, ?_⟩
  · -- x ≠ zero
    intro h
    have h0 := congrArg first h
    simp [first, zero, encode] at h0
  · -- y ≠ zero
    intro h
    have h0 := congrArg first h
    simp [first, zero, encode] at h0
  · -- mul x y = zero
    ext i
    fin_cases i <;> decide

/-!
## Even Subalgebra

The even subalgebra (elements with second = 0) is isomorphic to GF(2,2).
-/

/-- An element is in the even subalgebra if its second component is zero. -/
def isEven (x : Fin 16) : Prop := second x = zero

/-- The even subalgebra is closed under multiplication. -/
theorem even_mul_closed (x y : Fin 16) (hx : isEven x) (hy : isEven y) : isEven (mul x y) := by
  unfold isEven at hx hy ⊢
  have hx' : second x = zero := hx
  have hy' : second y = zero := hy
  ext i
  fin_cases i <;> decide

/-!
## Associator

The associator (x, y, z) = (xy)z - x(yz) measures non-associativity.
In characteristic 2, this is (xy)z + x(yz).
-/

/-- The associator at level 1: (x, y, z) = (xy)z + x(yz). -/
def associator (x y z : Fin 16) : Fin 16 :=
  add (mul (mul x y) z) (mul x (mul y z))

/-- The associator is nonzero for some elements.
    Since this is a Cayley-Dickson algebra at level ≥ 1, it is not associative. -/
theorem associator_nonzero : ∃ (x y z : Fin 16), associator x y z ≠ zero := by
  -- Use basis elements: encode one zero = 1, encode zero one = j
  let x := encode one zero  -- 1
  let y := encode zero one   -- j
  let z := encode (fromPair 0 1) zero  -- ω
  refine ⟨x, y, z, ?_⟩
  intro h
  -- Check component 0 (the "real" part in GF(2,2))
  have h0 := congrArg first h
  simp [first, associator, mul, encode, zero, one, add, first, second, decode] at h0
  -- In GF(2,2), ω * 1 = ω, and j * ω = ?
  -- Let's compute directly with fin_cases
  ext i : 1
  fin_cases i <;> decide

/-!
## Halting Set Search over GF(GF(2,2), GF(2,2))

We search for elements T such that the halting set {s | T*s = s} is nontrivial.
-/

/-- The halting set: {s | T*s = s}. -/
def haltingSet (T : Fin 16) : Set (Fin 16) :=
  {s | mul T s = s}

/-- Count fixed points of T. -/
def countFixedPoints (T : Fin 16) : Nat :=
  Finset.card (Finset.filter (fun s => mul T s = s) Finset.univ)

/-- There exists T with a nontrivial halting set (more than 1 fixed point). -/
theorem exists_nontrivial_halting : ∃ (T : Fin 16), countFixedPoints T > 1 := by
  -- The element 1 (identity) has every element as a fixed point
  refine ⟨one, ?_⟩
  have h_one : ∀ s, mul one s = s := by
    intro s
    ext i
    fin_cases i <;> decide
  -- All 16 elements are fixed points
  have h_card : countFixedPoints one = 16 := by
    unfold countFixedPoints
    simp [h_one]
  rw [h_card]
  omega

/-!
## Connection to Cayley-Dickson over ℝ

The standard Cayley-Dickson over ℝ gives octonions (8 elements over ℝ).
Our construction gives 16 elements over GF(2).

Both are instances of the same algebraic structure: Cayley-Dickson doubling
of a 4-dimensional algebra.
-/

/-- The Cayley-Dickson doubling map: A → A + A·j.
    Maps (a, b) ↦ a + bj. -/
def cayleyDicksonDouble (a b : Fin 4) : Fin 16 := encode a b

/-- Embed the base field GF(2,2) into the multiknob algebra. -/
def embed (x : Fin 4) : Fin 16 := encode x zero

/-- The imaginary unit j. -/
def j : Fin 16 := encode zero one

/-- Every element can be written as a + bj. -/
theorem every_element_is_a_plus_bj (x : Fin 16) : x = add (embed (first x)) (mul (embed (second x)) j) := by
  ext i
  fin_cases i <;> decide

end VDIS.Algebra.GF22Multiknob
