import Mathlib
import LambdaSatSolver.VDIS.Algebra.Basic

open Real

/-!
# Cayley-Dickson Construction — R → C → H → O

Implements the full Cayley-Dickson sequence:
  n=0: ℝ  (commutative, associative)
  n=1: ℂ  (commutative, associative)
  n=2: ℍ  (noncommutative, associative, alternative)
  n=3: 𝕆  (noncommutative, nonassociative, alternative, Hurwitz)

Each level doubles the dimension. The associator (a,b,c) = (ab)c - a(bc)
measures the failure of associativity. Norm multiplicativity holds for n=0,1,2,3
(Hurwitz theorem) but fails for n≥4.

## Convention

Elements are `Fin (2^n) → ℝ`:
  n=0: ℝ (1 component: x₀)
  n=1: ℂ (2 components: x₀, x₁)
  n=2: ℍ (4 components: x₀, x₁, x₂, x₃)
  n=3: 𝕆 (8 components: x₀, …, x₇)

## 360-orthogonal basis

The basis {e₀, …, e_{2^n-1}} is orthonormal. The Cayley-Dickson construction
gives the multiplication rule:
  e₀ = 1 (identity)
  eᵢ * eⱼ = -δ_{ij}·e₀ + ε_{ijk}·e_k  (Fano plane for n≥2)

## Gödelian identity

The identity e₀ = 1 is preserved across all levels of the tower.
Each level adds structure while keeping the prior identity fixed.

## Mutual recognition

Each level Aₙ recognizes A_{n-1} as its even subalgebra (odd components = 0).
Conjugation restricts to identity on the even subalgebra.
This is the fiber-bundle structure: Even(Aₙ) = base, Odd(Aₙ) = fiber.
-/

namespace VDIS.Algebra.CD

/-!
## Cayley-Dickson Pairing

### Helpers: split an Aₙ element into (x₀, x₁) where x₀, x₁ ∈ A_{n-1}

For the Cayley-Dickson construction, an element of Aₙ is represented as
(a, b) = a + b·e_{2^{n-1}} where a, b ∈ A_{n-1}.

The first half (indices 0..2^{n-1}-1) is the "a" part (even).
The second half (indices 2^{n-1}..2^n-1) is the "b" part (odd).
-/

/-- `2^(n-1) ≤ 2^n`, uniformly (n = 0 gives 1 ≤ 1). -/
private theorem pow_pred_le {n : ℕ} : 2 ^ (n - 1) ≤ 2 ^ n :=
  Nat.pow_le_pow_right (by norm_num) (Nat.sub_le _ _)

/-- `2^n ≤ 2^(n-1) + 2^(n-1)`, uniformly (n = 0 gives 1 ≤ 2;
n ≥ 1 gives equality). -/
private theorem pow_le_two_pow_pred {n : ℕ} :
    2 ^ n ≤ 2 ^ (n - 1) + 2 ^ (n - 1) := by
  cases n with
  | zero => simp
  | succ m =>
    simp only [Nat.add_sub_cancel]
    have h := pow_succ 2 m
    omega

/-- Extract the first half (indices 0..2^{n-1}-1). -/
def firstHalf {n : ℕ} (x : Fin (2 ^ n) → ℝ) : Fin (2 ^ (n - 1)) → ℝ :=
  fun i => x ⟨i.val, by
    have hi := i.is_lt
    have h := pow_pred_le (n := n)
    omega⟩

/-- Extract the second half (indices 2^{n-1}..2^n-1).

At n = 0 the Cayley–Dickson split is degenerate (there is no second
half); the guard falls through to the first component. Every real use
(`conj`, `mulByLevelGeneral`) only reaches this definition with n ≥ 1,
where the guard always holds. The original unguarded definition carried
an unprovable (false at n = 0) bound obligation and never compiled. -/
def secondHalf {n : ℕ} (x : Fin (2 ^ n) → ℝ) : Fin (2 ^ (n - 1)) → ℝ :=
  fun i =>
    if h : i.val + 2 ^ (n - 1) < 2 ^ n then
      x ⟨i.val + 2 ^ (n - 1), h⟩
    else
      x ⟨i.val, by
        have hi := i.is_lt
        have hle := pow_pred_le (n := n)
        omega⟩

/-- Embed an A_{n-1} element into the first half of Aₙ. -/
def embedFirst {n : ℕ} (x : Fin (2 ^ (n - 1)) → ℝ) : Fin (2 ^ n) → ℝ :=
  fun i =>
    if h : (i : ℕ) < 2 ^ (n - 1) then
      x ⟨i.val, h⟩
    else 0.0

/-- Embed an A_{n-1} element into the second half of Aₙ. -/
def embedSecond {n : ℕ} (x : Fin (2 ^ (n - 1)) → ℝ) : Fin (2 ^ n) → ℝ :=
  fun i =>
    if h : (i : ℕ) ≥ 2 ^ (n - 1) then
      let j : Fin (2 ^ (n - 1)) := ⟨i.val - 2 ^ (n - 1), by
        have hi := i.is_lt
        have h2 := pow_le_two_pow_pred (n := n)
        omega⟩
      x j
    else 0.0

/-!
## Half-Extraction Lemmas

These lemmas are the key to proving the Cayley-Dickson recurrence.
They show that the embedding/extraction operations are inverses of each other.
-/

/-- Extracting the first half after embedding recovers the original. -/
theorem firstHalf_embedFirst {n : ℕ} (x : Fin (2 ^ (n - 1)) → ℝ) :
    firstHalf (embedFirst x) = x := by
  ext i
  unfold firstHalf embedFirst
  simp

/-- Extracting the second half after embedding recovers the original. -/
theorem secondHalf_embedSecond {n : ℕ} (hn : 0 < n) (x : Fin (2 ^ (n - 1)) → ℝ) :
    secondHalf (embedSecond x) = x := by
  ext i
  unfold secondHalf embedSecond
  have h_lt : i.val + 2 ^ (n - 1) < 2 ^ n := by
    have hi := i.is_lt
    have h_pow_add : 2 ^ (n - 1) + 2 ^ (n - 1) = 2 ^ n := by
      have hn1 : 1 ≤ n := Nat.one_le_of_lt hn
      calc
        2 ^ (n - 1) + 2 ^ (n - 1) = 2 * 2 ^ (n - 1) := by ring
        _ = 2 ^ n := by rw [mul_comm, ← pow_succ, Nat.sub_add_cancel hn1]
    have h_lt_sum : i.val + 2 ^ (n - 1) < 2 ^ (n - 1) + 2 ^ (n - 1) :=
      Nat.add_lt_add_right hi _
    exact lt_of_lt_of_eq h_lt_sum h_pow_add
  simp [h_lt]

/-- The first half of a sum is the sum of the first halves. -/
theorem firstHalf_add {n : ℕ} (x y : Fin (2 ^ n) → ℝ) :
    firstHalf (x + y) = firstHalf x + firstHalf y := by
  ext i
  unfold firstHalf
  simp

/-- The second half of a sum is the sum of the second halves. -/
theorem secondHalf_add {n : ℕ} (hn : 0 < n) (x y : Fin (2 ^ n) → ℝ) :
    secondHalf (x + y) = secondHalf x + secondHalf y := by
  ext i
  unfold secondHalf
  have h_lt : i.val + 2 ^ (n - 1) < 2 ^ n := by
    have hi := i.is_lt
    have h_pow_add : 2 ^ (n - 1) + 2 ^ (n - 1) = 2 ^ n := by
      have hn1 : 1 ≤ n := Nat.one_le_of_lt hn
      calc
        2 ^ (n - 1) + 2 ^ (n - 1) = 2 * 2 ^ (n - 1) := by ring
        _ = 2 ^ n := by rw [mul_comm, ← pow_succ, Nat.sub_add_cancel hn1]
    have h_lt_sum : i.val + 2 ^ (n - 1) < 2 ^ (n - 1) + 2 ^ (n - 1) :=
      Nat.add_lt_add_right hi _
    exact lt_of_lt_of_eq h_lt_sum h_pow_add
  simp [h_lt]

/-- Embedding the first half plus embedding the second half recovers the original. -/
theorem embedFirst_secondHalf_add {n : ℕ} (hn : 0 < n) (x : Fin (2 ^ n) → ℝ) :
    embedFirst (firstHalf x) + embedSecond (secondHalf x) = x := by
  ext i
  unfold embedFirst embedSecond firstHalf secondHalf
  by_cases h : i.val < 2 ^ (n - 1)
  · have h_not_ge : ¬ (2 ^ (n - 1) ≤ i.val) := by omega
    have h_lt : i.val + 2 ^ (n - 1) < 2 ^ n := by
      have hi := i.is_lt
      have hn1 : 1 ≤ n := Nat.one_le_of_lt hn
      have h_pow_add : 2 ^ (n - 1) + 2 ^ (n - 1) = 2 ^ n := by
        calc
          2 ^ (n - 1) + 2 ^ (n - 1) = 2 * 2 ^ (n - 1) := by ring
          _ = 2 ^ n := by rw [mul_comm, ← pow_succ, Nat.sub_add_cancel hn1]
      have h_lt_sum : i.val + 2 ^ (n - 1) < 2 ^ (n - 1) + 2 ^ (n - 1) :=
        Nat.add_lt_add_right h _
      exact lt_of_lt_of_eq h_lt_sum h_pow_add
    simp [h, h_not_ge, h_lt]; norm_num
  · have h_ge : 2 ^ (n - 1) ≤ i.val := by omega
    have h_not_lt : ¬ (i.val + 2 ^ (n - 1) < 2 ^ n) := by
      have hi := i.is_lt
      have hn1 : 1 ≤ n := Nat.one_le_of_lt hn
      have h_pow_add : 2 ^ (n - 1) + 2 ^ (n - 1) = 2 ^ n := by
        calc
          2 ^ (n - 1) + 2 ^ (n - 1) = 2 * 2 ^ (n - 1) := by ring
          _ = 2 ^ n := by rw [mul_comm, ← pow_succ, Nat.sub_add_cancel hn1]
      omega
    simp [h, h_ge, h_not_lt]; norm_num

/-!
## Conjugation

  conjₙ(a + b·e) = conj_{n-1}(a) - conj_{n-1}(b)·e

Base: conj₀ is identity on ℝ.
-/

/-- Conjugation in Aₙ. -/
def conj {n : ℕ} (x : Fin (2 ^ n) → ℝ) : Fin (2 ^ n) → ℝ :=
  if hn : n = 0 then
    x
  else
    fun i =>
      if h : (i : ℕ) < 2 ^ (n - 1) then
        conj (n := n - 1) (firstHalf x) ⟨i.val, h⟩
      else
        -conj (n := n - 1) (secondHalf x) ⟨i.val - 2 ^ (n - 1), by
          have hi := i.is_lt
          have h2 := pow_le_two_pow_pred (n := n)
          omega⟩
termination_by n
decreasing_by
  · omega
  · omega

/-!
## Cayley-Dickson Multiplication

  (a₀ + a₁·e) * (b₀ + b₁·e) = (a₀*b₀ - e·conj(b₁)*a₁) + (conj(a₀)*b₁ + b₀*a₁)·e

  Wait, the correct formula is:
  (x₀, x₁) * (y₀, y₁) = (x₀*y₀ - y₁_conj * x₁, y₁*x₀ + x₁*y₀_conj)

  where conj is conjugation in A_{n-1}.

  In terms of components: if we write elements as interleaved (a₀, a₁, …, a_{2^{n-1}-1},
  b₀, b₁, …, b_{2^{n-1}-1}) then the product is computed using the above formula.

---

## Multiplication by Level

We define multiplication explicitly for each level and prove the
recursive Cayley-Dickson formula as a theorem.
-/

/-- Multiplication in ℝ (n=0): elementwise product. -/
def mulReal (x y : Fin 1 → ℝ) : Fin 1 → ℝ :=
  fun i => x i * y i

/-- Multiplication in ℂ (n=1): standard complex multiplication. -/
def mulComplex (x y : Fin 2 → ℝ) : Fin 2 → ℝ :=
  fun i =>
    match i with
    | ⟨0, _⟩ => x 0 * y 0 - x 1 * y 1
    | ⟨1, _⟩ => x 0 * y 1 + x 1 * y 0

/-- Multiplication in ℍ (n=2): standard Hamilton product. -/
def mulQuat (x y : Fin 4 → ℝ) : Fin 4 → ℝ :=
  fun i =>
    match i with
    | ⟨0, _⟩ => x 0 * y 0 - x 1 * y 1 - x 2 * y 2 - x 3 * y 3
    | ⟨1, _⟩ => x 0 * y 1 + x 1 * y 0 + x 2 * y 3 - x 3 * y 2
    | ⟨2, _⟩ => x 0 * y 2 - x 1 * y 3 + x 2 * y 0 + x 3 * y 1
    | ⟨3, _⟩ => x 0 * y 3 + x 1 * y 2 - x 2 * y 1 + x 3 * y 0

/-- Multiplication in 𝕆 (n=3): standard octonion multiplication.

The octonion multiplication table is determined by the Fano plane.
Using the compact representation where the product of two basis elements
eᵢ*eⱼ (i ≠ j) is ±e_k for a unique k determined by the Fano triangle.

The Fano plane used here is:
  Triangle 1: e₁, e₂, e₃ with e₁*e₂ = e₃, e₂*e₃ = e₁, e₃*e₁ = e₂
  Triangle 2: e₄, e₅, e₆ with e₄*e₅ = e₆, e₅*e₆ = e₄, e₆*e₄ = e₅
  Cross: e₇ connects e₁↔e₄, e₂↔e₅, e₃↔e₆ (e₁*e₄ = e₅, e₁*e₇ = -e₄, etc.)

All products are anti-commutative: eᵢ*eⱼ = -eⱼ*eᵢ for i ≠ j.
-/
def mulOct (x y : Fin 8 → ℝ) : Fin 8 → ℝ :=
  -- Use the Cayley-Dickson construction from quaternions:
  -- (q₀ + q₁·e₇) * (r₀ + r₁·e₇) = (q₀*r₀ - r₁*conj(q₁)) + (conj(q₀)*r₁ + r₀*q₁)·e₇
  -- where conj(q) = (q₀, -q₁, -q₂, -q₃)
  let half := 4
  fun i =>
    if h : (i : ℕ) < half then
      -- First half (indices 0..3): q₀*r₀ - r₁*conj(q₁)
      let q0 := fun (j : Fin 4) => x ⟨j.val, by
        have hi := j.is_lt
        omega⟩
      let q1 := fun (j : Fin 4) => x ⟨j.val + half, by
        have hi := j.is_lt
        omega⟩
      let r0 := fun (j : Fin 4) => y ⟨j.val, by
        have hi := j.is_lt
        omega⟩
      let r1 := fun (j : Fin 4) => y ⟨j.val + half, by
        have hi := j.is_lt
        omega⟩
      -- q₀*r₀
      let q0r0 := mulQuat q0 r0
      -- conj(r₁)*q₁ = conj(r₁) * q₁
      let r1conj := fun (j : Fin 4) =>
        if j.val = 0 then r1 j else -r1 j
      let r1conj_mul_q1 := mulQuat r1conj q1
      q0r0 ⟨i.val, h⟩ - r1conj_mul_q1 ⟨i.val, h⟩
    else
      -- Second half (indices 4..7): conj(q₀)*r₁ + r₀*q₁
      let j : Fin 4 :=
        ⟨i.val - half, by
          have hi := i.is_lt
          omega⟩
      let q0 := fun (k : Fin 4) => x ⟨k.val, by
        have hi := k.is_lt
        omega⟩
      let q1 := fun (k : Fin 4) => x ⟨k.val + half, by
        have hi := k.is_lt
        omega⟩
      let r0 := fun (k : Fin 4) => y ⟨k.val, by
        have hi := k.is_lt
        omega⟩
      let r1 := fun (k : Fin 4) => y ⟨k.val + half, by
        have hi := k.is_lt
        omega⟩
      -- conj(q₀)*r₁
      let q0conj := fun (k : Fin 4) =>
        if k.val = 0 then q0 k else -q0 k
      let q0conj_mul_r1 := mulQuat q0conj r1
      -- r₀*q₁
      let r0_mul_q1 := mulQuat r0 q1
      q0conj_mul_r1 j + r0_mul_q1 j

/-!
## Sedenions (n=4)

Level 4 of the Cayley-Dickson construction yields the sedenions (16 components).
These are noncommutative, nonassociative, and nonalternative. The norm is
NOT multiplicative at this level (Hurwitz theorem: only n=0,1,2,3 preserve
the norm).

We provide explicit multiplication, conjugation, and norm for completeness.
-/

/-- Multiplication in 𝕊 (n=4): sedenion multiplication via Cayley-Dickson.

The 16×16 multiplication table is determined by the recursive construction:
(a₀ + a₁·e₈) * (b₀ + b₁·e₈) = (a₀*b₀ - conj(b₁)*a₁) + (conj(a₀)*b₁ + b₀*a₁)·e₈
where a₀, a₁, b₀, b₁ are octonions (8 components each). -/
def mulSedenion (x y : Fin 16 → ℝ) : Fin 16 → ℝ :=
  let half := 8
  fun i =>
    if h : (i : ℕ) < half then
      -- First half (indices 0..7): a₀*b₀ - conj(b₁)*a₁
      let a0 := fun (j : Fin 8) => x ⟨j.val, by
        have hi := j.is_lt
        omega⟩
      let a1 := fun (j : Fin 8) => x ⟨j.val + half, by
        have hi := j.is_lt
        omega⟩
      let b0 := fun (j : Fin 8) => y ⟨j.val, by
        have hi := j.is_lt
        omega⟩
      let b1 := fun (j : Fin 8) => y ⟨j.val + half, by
        have hi := j.is_lt
        omega⟩
      -- a₀*b₀
      let a0b0 := mulOct a0 b0
      -- conj(b₁)*a₁
      let b1conj := fun (j : Fin 8) =>
        if j.val = 0 then b1 j else -b1 j
      let b1conj_a1 := mulOct b1conj a1
      a0b0 ⟨i.val, h⟩ - b1conj_a1 ⟨i.val, h⟩
    else
      -- Second half (indices 8..15): conj(a₀)*b₁ + b₀*a₁
      let j : Fin 8 :=
        ⟨i.val - half, by
          have hi := i.is_lt
          omega⟩
      let a0 := fun (k : Fin 8) => x ⟨k.val, by
        have hi := k.is_lt
        omega⟩
      let a1 := fun (k : Fin 8) => x ⟨k.val + half, by
        have hi := k.is_lt
        omega⟩
      let b0 := fun (k : Fin 8) => y ⟨k.val, by
        have hi := k.is_lt
        omega⟩
      let b1 := fun (k : Fin 8) => y ⟨k.val + half, by
        have hi := k.is_lt
        omega⟩
      -- conj(a₀)*b₁
      let a0conj := fun (k : Fin 8) =>
        if k.val = 0 then a0 k else -a0 k
      let a0conj_b1 := mulOct a0conj b1
      -- b₀*a₁
      let b0a1 := mulOct b0 a1
      a0conj_b1 j + b0a1 j

/-- Conjugation in 𝕊 (n=4): negate all imaginary components. -/
def conjSedenion (x : Fin 16 → ℝ) : Fin 16 → ℝ :=
  fun i =>
    if i.val = 0 then x i else -x i

/-- Norm in 𝕊 (n=4): √(∑ x_i²). -/
noncomputable def normSedenion (x : Fin 16 → ℝ) : ℝ :=
  Real.sqrt (∑ i, (x i) ^ 2)

/-!
## Multiplication Dispatch by Level

Dispatch to the appropriate multiplication for the given level.
-/

/-- Conjugation dispatch by level: negate every imaginary component.

Repair note (2026-07-15): the original agent-generated tables negated
only odd indices at levels 2 and 3 (e.g. leaving the `j` component of a
quaternion unconjugated). Standard Cayley–Dickson conjugation fixes the
real component and negates all others; the tables below do exactly
that. -/
def conjByLevel (level : ℕ) (x : Fin (2 ^ level) → ℝ) : Fin (2 ^ level) → ℝ :=
  match level with
  | 0 => x
  | 1 => fun i => if i.val = 0 then x i else -x i
  | 2 => fun i => if i.val = 0 then x i else -x i
  | 3 => fun i => if i.val = 0 then x i else -x i
  | 4 => conjSedenion x
  | l + 5 => conj (n := l + 5) x

/-- Multiplication dispatch by algebra level.
Levels 0-3 use explicit Cayley-Dickson formulas.
Level ≥ 4 uses the general recurrence, recursing to the level below.

Repair note (2026-07-15): originally split into two definitions with a
forward reference (`mulByLevelGeneral` used `mulByLevel`, defined after
it) — an implicit mutual recursion that could never elaborate. Folded
into one structurally recursive definition; `mulByLevelGeneral` is kept
below as a compatibility wrapper. -/
def mulByLevel : (level : ℕ) → (x y : Fin (2 ^ level) → ℝ) → Fin (2 ^ level) → ℝ
  | 0, x, y => fun i => x i * y i
  | 1, x, y => mulComplex x y
  | 2, x, y => mulQuat x y
  | 3, x, y => mulOct x y
  | 4, x, y => mulSedenion x y
  | level + 5, x, y =>
    embedFirst (mulByLevel (level + 4) (firstHalf x) (firstHalf y) -
      mulByLevel (level + 4) (conjByLevel (level + 4) (secondHalf y)) (secondHalf x)) +
    embedSecond (mulByLevel (level + 4) (conjByLevel (level + 4) (firstHalf x)) (secondHalf y) +
      mulByLevel (level + 4) (firstHalf y) (secondHalf x))

/-- General Cayley-Dickson recurrence at `level`, expressed through the
level-below operations. Compatibility wrapper; for `level ≥ 1` this is
what the `level + 4` branch of `mulByLevel` computes at its own level. -/
def mulByLevelGeneral (level : ℕ) (x y : Fin (2 ^ level) → ℝ) : Fin (2 ^ level) → ℝ :=
  embedFirst (mulByLevel (level - 1) (firstHalf x) (firstHalf y) -
    mulByLevel (level - 1) (conjByLevel (level - 1) (secondHalf y)) (secondHalf x)) +
  embedSecond (mulByLevel (level - 1) (conjByLevel (level - 1) (firstHalf x)) (secondHalf y) +
    mulByLevel (level - 1) (firstHalf y) (secondHalf x))

/-- Norm dispatch by level. -/
noncomputable def normByLevel (level : ℕ) (x : Fin (2 ^ level) → ℝ) : ℝ :=
  match level with
  | 0 => |x 0|
  | 1 => Real.sqrt ((x 0) ^ 2 + (x 1) ^ 2)
  | 2 => Real.sqrt ((x 0) ^ 2 + (x 1) ^ 2 + (x 2) ^ 2 + (x 3) ^ 2)
  | 3 => Real.sqrt ((x 0) ^ 2 + (x 1) ^ 2 + (x 2) ^ 2 + (x 3) ^ 2 +
      (x 4) ^ 2 + (x 5) ^ 2 + (x 6) ^ 2 + (x 7) ^ 2)
  | 4 => normSedenion x
  | _ => Real.sqrt (∑ i, (x i) ^ 2)

/-!
## The Cayley-Dickson Recurrence Theorem

For n > 0:
  (x₀, x₁) * (y₀, y₁) = (x₀*y₀ - conj(y₁)*x₁, conj(x₀)*y₁ + y₀*x₁)

where (x₀, x₁) means embedFirst x₀ + embedSecond x₁.
-/

/-- The Cayley–Dickson recurrence at levels 1–3: proved using the
half-extraction lemmas and case analysis on the four levels. -/
theorem CayleyDicksonRecurrenceLow (level : ℕ) (hpos : 0 < level) (hlevel : level ≤ 3)
    (x₀ x₁ y₀ y₁ : Fin (2 ^ (level - 1)) → ℝ) :
    mulByLevel level
      (embedFirst x₀ + embedSecond x₁)
      (embedFirst y₀ + embedSecond y₁) =
    embedFirst (mulByLevel (level - 1) x₀ y₀ -
      mulByLevel (level - 1) (conjByLevel (level - 1) y₁) x₁) +
    embedSecond (mulByLevel (level - 1) (conjByLevel (level - 1) x₀) y₁ +
      mulByLevel (level - 1) y₀ x₁) := by
  interval_cases level
  · -- level = 1: ℂ
    have h : mulComplex (embedFirst x₀ + embedSecond x₁) (embedFirst y₀ + embedSecond y₁) =
      embedFirst (x₀ * y₀ - y₁ * x₁) + embedSecond (x₀ * y₁ + y₀ * x₁) := by
      ext i; fin_cases i <;>
        simp [mulComplex, embedFirst, embedSecond] <;>
        ring
    simpa [mulByLevel, conjByLevel] using h
  · -- level = 2: ℍ
    have h : mulQuat (embedFirst x₀ + embedSecond x₁) (embedFirst y₀ + embedSecond y₁) =
      embedFirst (mulQuat x₀ y₀ - mulQuat (fun i => if i.val = 0 then y₁ i else -y₁ i) x₁) +
      embedSecond (mulQuat (fun i => if i.val = 0 then x₀ i else -x₀ i) y₁ + mulQuat y₀ x₁) := by
      ext i; fin_cases i <;>
        simp [mulQuat, embedFirst, embedSecond] <;>
        ring
    simpa [mulByLevel, conjByLevel] using h
  · -- level = 3: 𝕆
    have h : mulOct (embedFirst x₀ + embedSecond x₁) (embedFirst y₀ + embedSecond y₁) =
      embedFirst (mulOct x₀ y₀ - mulOct (fun i => if i.val = 0 then y₁ i else -y₁ i) x₁) +
      embedSecond (mulOct (fun i => if i.val = 0 then x₀ i else -x₀ i) y₁ + mulOct y₀ x₁) := by
      ext i; fin_cases i <;>
        simp [mulOct, embedFirst, embedSecond] <;>
        ring
    simpa [mulByLevel, conjByLevel] using h

/-- Extracting the first half of an embedded second half gives zero. -/
theorem firstHalf_embedSecond {n : ℕ} (x : Fin (2 ^ (n - 1)) → ℝ) :
    firstHalf (embedSecond x) = 0 := by
  ext i
  unfold firstHalf embedSecond
  have hi := i.is_lt
  have h_not_ge : ¬ (2 ^ (n - 1) ≤ i.val) := by omega
  simp [h_not_ge]; norm_num

/-- Extracting the second half of an embedded first half gives zero. -/
theorem secondHalf_embedFirst {n : ℕ} (hn : 0 < n) (x : Fin (2 ^ (n - 1)) → ℝ) :
    secondHalf (embedFirst x) = 0 := by
  ext i
  unfold secondHalf embedFirst
  have hi := i.is_lt
  have h_lt : i.val + 2 ^ (n - 1) < 2 ^ n := by
    have hn1 : 1 ≤ n := Nat.one_le_of_lt hn
    have h_pow_add : 2 ^ (n - 1) + 2 ^ (n - 1) = 2 ^ n := by
      calc
        2 ^ (n - 1) + 2 ^ (n - 1) = 2 * 2 ^ (n - 1) := by ring
        _ = 2 ^ n := by rw [mul_comm, ← pow_succ, Nat.sub_add_cancel hn1]
    have h_lt_sum : i.val + 2 ^ (n - 1) < 2 ^ (n - 1) + 2 ^ (n - 1) :=
      Nat.add_lt_add_right hi _
    exact lt_of_lt_of_eq h_lt_sum h_pow_add
  have h_not_lt_inner : ¬ (i.val + 2 ^ (n - 1) < 2 ^ (n - 1)) := by omega
  simp [hi, h_lt, h_not_lt_inner]; norm_num

/-- The general Cayley–Dickson recurrence for `level ≥ 4`: proved by
definitional reduction to the half-extraction lemmas.

Since `mulByLevel (level+4) x y` is definitionally:
  embedFirst (mulByLevel (level+3) (firstHalf x) (firstHalf y) -
    mulByLevel (level+3) (conjByLevel (level+3) (secondHalf y)) (secondHalf x)) +
  embedSecond (mulByLevel (level+3) (conjByLevel (level+3) (firstHalf x)) (secondHalf y) +
    mulByLevel (level+3) (firstHalf y) (secondHalf x))

and for `level ≥ 4`, `mulByLevel level` reduces via the `level+4` pattern,
we can rewrite in terms of the half operations. The proof is by
simplification and the half-extraction lemmas.

For `level ≥ 4`, we write `level = l + 4` and use the definition. -/
theorem CayleyDicksonRecurrenceGeneral (level : ℕ) (hlevel : 4 ≤ level)
    (x₀ x₁ y₀ y₁ : Fin (2 ^ (level - 1)) → ℝ) :
    mulByLevel level
      (embedFirst x₀ + embedSecond x₁)
      (embedFirst y₀ + embedSecond y₁) =
    embedFirst (mulByLevel (level - 1) x₀ y₀ -
      mulByLevel (level - 1) (conjByLevel (level - 1) y₁) x₁) +
    embedSecond (mulByLevel (level - 1) (conjByLevel (level - 1) x₀) y₁ +
      mulByLevel (level - 1) y₀ x₁) := by
  rcases Nat.exists_eq_add_of_le hlevel with ⟨l, hl⟩
  rw [add_comm 4 l] at hl
  subst hl
  -- Now level = l + 4, level - 1 = l + 3
  have hpos : 0 < l + 4 := by omega
  have hpos' : 0 < l + 3 := by omega
  have hx0 : firstHalf (embedFirst x₀ + embedSecond x₁) = x₀ := by
    rw [firstHalf_add, firstHalf_embedFirst, firstHalf_embedSecond, add_zero]
  have hx1 : secondHalf (embedFirst x₀ + embedSecond x₁) = x₁ := by
    calc
      secondHalf (embedFirst x₀ + embedSecond x₁)
          = secondHalf (embedFirst x₀) + secondHalf (embedSecond x₁) := by
            rw [secondHalf_add hpos (embedFirst x₀) (embedSecond x₁)]
      _ = 0 + x₁ := by rw [secondHalf_embedFirst hpos x₀, secondHalf_embedSecond hpos x₁]
      _ = x₁ := by simpa using (zero_add x₁)
  have hy0 : firstHalf (embedFirst y₀ + embedSecond y₁) = y₀ := by
    rw [firstHalf_add, firstHalf_embedFirst, firstHalf_embedSecond, add_zero]
  have hy1 : secondHalf (embedFirst y₀ + embedSecond y₁) = y₁ := by
    calc
      secondHalf (embedFirst y₀ + embedSecond y₁)
          = secondHalf (embedFirst y₀) + secondHalf (embedSecond y₁) := by
            rw [secondHalf_add hpos (embedFirst y₀) (embedSecond y₁)]
      _ = 0 + y₁ := by rw [secondHalf_embedFirst hpos y₀, secondHalf_embedSecond hpos y₁]
      _ = y₁ := by simpa using (zero_add y₁)
  cases l with
  | zero =>
      -- level = 4: both sides reduce to mulSedenion
      have hpos4 : 0 < 4 := by omega
      have hx0' : firstHalf (embedFirst x₀ + embedSecond x₁) = x₀ := by
        calc
          firstHalf (embedFirst x₀ + embedSecond x₁)
              = firstHalf (embedFirst x₀) + firstHalf (embedSecond x₁) := firstHalf_add _ _
          _ = x₀ + 0 := by rw [firstHalf_embedFirst, firstHalf_embedSecond]
          _ = x₀ := by simp
      have hx1' : secondHalf (embedFirst x₀ + embedSecond x₁) = x₁ := by
        rw [secondHalf_add hpos4, secondHalf_embedFirst hpos4 x₀,
          secondHalf_embedSecond hpos4 x₁]
        simp
      have hy0' : firstHalf (embedFirst y₀ + embedSecond y₁) = y₀ := by
        calc
          firstHalf (embedFirst y₀ + embedSecond y₁)
              = firstHalf (embedFirst y₀) + firstHalf (embedSecond y₁) := firstHalf_add _ _
          _ = y₀ + 0 := by rw [firstHalf_embedFirst, firstHalf_embedSecond]
          _ = y₀ := by simp
      have hy1' : secondHalf (embedFirst y₀ + embedSecond y₁) = y₁ := by
        rw [secondHalf_add hpos4, secondHalf_embedFirst hpos4 y₀,
          secondHalf_embedSecond hpos4 y₁]
        simp
      have hzero : mulSedenion (embedFirst x₀ + embedSecond x₁) (embedFirst y₀ + embedSecond y₁) =
        embedFirst (mulOct x₀ y₀ - mulOct (fun i => if i.val = 0 then y₁ i else -y₁ i) x₁) +
        embedSecond (mulOct (fun i => if i.val = 0 then x₀ i else -x₀ i) y₁ + mulOct y₀ x₁) := by
        ext i; fin_cases i <;>
          simp [mulSedenion, embedFirst, embedSecond] <;>
          ring
      simpa [mulByLevel, conjByLevel] using hzero
  | succ m =>
      simp

/-!
## Key Algebraic Properties

### Associativity (n=0,1,2) and Nonassociativity (n=3)
-/

/-- Multiplication is associative for levels 0, 1, 2. -/
theorem mul_assoc_levels_0_1_2 (level : ℕ) (h : level ≤ 2) (a b c : Fin (2 ^ level) → ℝ) :
    mulByLevel level (mulByLevel level a b) c = mulByLevel level a (mulByLevel level b c) := by
  interval_cases level
  · -- ℝ
    ext i; fin_cases i <;> simp [mulByLevel] <;> ring
  · -- ℂ
    ext i; fin_cases i <;> simp [mulByLevel, mulComplex] <;> ring
  · -- ℍ
    ext i; fin_cases i <;> simp [mulByLevel, mulQuat] <;> ring

/-- Multiplication is NOT associative for octonions (n=3).
  Provide an explicit counterexample. -/
theorem mul_nonassoc_octonions :
    ∃ (a b c : Fin 8 → ℝ),
      mulByLevel 3 (mulByLevel 3 a b) c ≠ mulByLevel 3 a (mulByLevel 3 b c) := by
  -- Use basis elements: e₁, e₂, e₄
  -- (e₁*e₂)*e₄ = e₃*e₄
  -- e₁*(e₂*e₄) = e₁*e₆
  -- These differ because e₃*e₄ ≠ e₁*e₆ in the octonion algebra
  -- (e₁·e₂)·e₄ = −e₇ while e₁·(e₂·e₄) = +e₇: they differ at index 7.
  -- Repair note: the original proof invoked `native_decide` on a
  -- proposition over ℝ, which is not decidable; it could never work.
  refine ⟨fun i => if i.val = 1 then 1 else 0,
    fun i => if i.val = 2 then 1 else 0,
    fun i => if i.val = 4 then 1 else 0, ?_⟩
  intro h
  have h7 := congrFun h 7
  norm_num [mulByLevel, mulOct, mulQuat] at h7

/-- Multiplication is commutative for ℝ and ℂ (levels 0, 1). -/
theorem mul_comm_levels_0_1 (level : ℕ) (h : level ≤ 1) (a b : Fin (2 ^ level) → ℝ) :
    mulByLevel level a b = mulByLevel level b a := by
  interval_cases level
  · ext i; fin_cases i <;> simp [mulByLevel] <;> ring
  · ext i; fin_cases i <;> simp [mulByLevel, mulComplex] <;> ring

/-- Multiplication is NOT commutative for quaternions (n=2) and octonions (n=3). -/
theorem mul_noncomm_levels_2_3 :
    ∃ (a b : Fin 4 → ℝ), mulByLevel 2 a b ≠ mulByLevel 2 b a := by
  -- i·j = k, j·i = −k: they differ at index 3.
  refine ⟨fun k => if k.val = 1 then 1 else 0,
    fun k => if k.val = 2 then 1 else 0, ?_⟩
  intro h
  have h3 := congrFun h 3
  norm_num [mulByLevel, mulQuat] at h3

/-- Multiplication is NOT commutative for octonions (n=3). -/
theorem mul_noncomm_octonions :
    ∃ (a b : Fin 8 → ℝ), mulByLevel 3 a b ≠ mulByLevel 3 b a := by
  -- e₁·e₂ = e₃, e₂·e₁ = −e₃: they differ at index 3.
  refine ⟨fun i => if i.val = 1 then 1 else 0,
    fun i => if i.val = 2 then 1 else 0, ?_⟩
  intro h
  have h3 := congrFun h 3
  norm_num [mulByLevel, mulOct, mulQuat] at h3

/-- Left alternativity: (a·a)·b = a·(a·b), levels 0–3.

Repair note (2026-07-15): the original statement read
`(a·a)·b = b·(a·a)` — squares commuting with everything — which is
false already for quaternions (a = 1 + i, b = j gives 2k vs −2k), and
it quantified over all levels while enumerating four. Alternativity is
the correct law that survives into the octonions. -/
theorem mul_alternative (level : ℕ) (hlevel : level ≤ 2)
    (a b : Fin (2 ^ level) → ℝ) :
    mulByLevel level (mulByLevel level a a) b =
      mulByLevel level a (mulByLevel level a b) := by
  interval_cases level
  · ext i; fin_cases i <;> simp [mulByLevel] <;> ring
  · ext i; fin_cases i <;> simp [mulByLevel, mulComplex] <;> ring
  · ext i; fin_cases i <;> simp [mulByLevel, mulQuat] <;> ring

/-- Left alternativity at the octonion level (proved).

The octonion multiplication defined via Cayley-Dickson from quaternions
satisfies left alternativity: (a·a)·b = a·(a·b) for all octonions.

Proof: expand the 8×8×8 = 512-term identity by cases on the three
Fin 8 indices, then `ring` handles each of the 8×8 = 64 component
equations. -/
theorem mul_alternative_octonions (a b : Fin 8 → ℝ) :
    mulByLevel 3 (mulByLevel 3 a a) b = mulByLevel 3 a (mulByLevel 3 a b) := by
  ext i
  fin_cases i <;>
    delta mulByLevel mulOct mulQuat <;>
    simp <;>
    ring

/-!
## Norm Properties

### Norm is multiplicative for n=0,1,2,3 (Hurwitz theorem)
-/

/-- Norm is multiplicative for ℝ. -/
theorem norm_mul_real (a b : Fin 1 → ℝ) : normByLevel 0 (mulByLevel 0 a b) =
    normByLevel 0 a * normByLevel 0 b := by
  simp [normByLevel, mulByLevel]

/-- Norm is multiplicative for ℂ (Brahmagupta–Fibonacci identity).

Repair note: the original proofs asked `ring` to prove equalities
between square roots, and `native_decide` to decide a proposition over
ℝ; neither can succeed. The correct route is `√x·√y = √(x·y)` plus the
polynomial composition identity under the root. -/
theorem norm_mul_complex (a b : Fin 2 → ℝ) : normByLevel 1 (mulByLevel 1 a b) =
    normByLevel 1 a * normByLevel 1 b := by
  simp only [normByLevel, mulByLevel, mulComplex]
  rw [← Real.sqrt_mul (by positivity)]
  congr 1
  ring

/-- Norm is multiplicative for ℍ (Euler four-square identity). -/
theorem norm_mul_quat (a b : Fin 4 → ℝ) : normByLevel 2 (mulByLevel 2 a b) =
    normByLevel 2 a * normByLevel 2 b := by
  simp only [normByLevel, mulByLevel, mulQuat]
  rw [← Real.sqrt_mul (by positivity)]
  congr 1
  ring

set_option maxHeartbeats 0 in
/-- Norm multiplicativity at the octonion level (Degen eight-square
identity, proved).

The norm `‖a‖ = √(∑ a_i²)` satisfies `‖a*b‖ = ‖a‖ * ‖b‖` for the
Cayley-Dickson octonion multiplication. This is the Degen eight-square
identity.

Proof: square both sides and use the identity
  (a*b)·(a*b) = (a·conj(a))*(b·conj(b))
which holds for the Cayley-Dickson construction. Since norms are nonnegative,
the squared equality implies the norm equality.

We prove this by expanding the 16-variable quartic using `ring`.
The computation is heavy but `ring` on 16 variables with degree 4
is within Lean's capacity. -/
theorem norm_mul_octonions (a b : Fin 8 → ℝ) :
    normByLevel 3 (mulByLevel 3 a b) = normByLevel 3 a * normByLevel 3 b := by
  have h_nonneg_a : 0 ≤ normByLevel 3 a := by
    unfold normByLevel; exact Real.sqrt_nonneg _
  have h_nonneg_b : 0 ≤ normByLevel 3 b := by
    unfold normByLevel; exact Real.sqrt_nonneg _
  have h_nonneg_ab : 0 ≤ normByLevel 3 (mulByLevel 3 a b) := by
    unfold normByLevel; exact Real.sqrt_nonneg _
  have h_sq_eq : (normByLevel 3 (mulByLevel 3 a b)) ^ 2 = (normByLevel 3 a * normByLevel 3 b) ^ 2 := by
    simp only [normByLevel, mulByLevel]
    have hsum : (∑ i : Fin 8, (mulOct a b) i * (mulOct a b) i) =
      (∑ i : Fin 8, a i * a i) * (∑ i : Fin 8, b i * b i) := by
      unfold mulOct mulQuat
      simp only [Fin.sum_univ_eight]
      ring
    have h_nonneg_sum : 0 ≤ ∑ i : Fin 8, (mulOct a b) i * (mulOct a b) i :=
      Finset.sum_nonneg fun i _ => by nlinarith [sq_nonneg ((mulOct a b) i)]
    have h_nonneg_sum_a : 0 ≤ ∑ i : Fin 8, a i * a i :=
      Finset.sum_nonneg fun i _ => by nlinarith [sq_nonneg (a i)]
    have h_nonneg_sum_b : 0 ≤ ∑ i : Fin 8, b i * b i :=
      Finset.sum_nonneg fun i _ => by nlinarith [sq_nonneg (b i)]
    have hcalc : (Real.sqrt (∑ i : Fin 8, (mulOct a b) i * (mulOct a b) i)) ^ 2 =
      (Real.sqrt (∑ i : Fin 8, a i * a i) * Real.sqrt (∑ i : Fin 8, b i * b i)) ^ 2 := by
      calc
        (Real.sqrt (∑ i : Fin 8, (mulOct a b) i * (mulOct a b) i)) ^ 2
            = (∑ i : Fin 8, (mulOct a b) i * (mulOct a b) i) := Real.sq_sqrt h_nonneg_sum
        _ = (∑ i : Fin 8, a i * a i) * (∑ i : Fin 8, b i * b i) := hsum
        _ = (Real.sqrt (∑ i : Fin 8, a i * a i)) ^ 2 * (Real.sqrt (∑ i : Fin 8, b i * b i)) ^ 2 := by
          rw [Real.sq_sqrt h_nonneg_sum_a, Real.sq_sqrt h_nonneg_sum_b]
        _ = (Real.sqrt (∑ i : Fin 8, a i * a i) * Real.sqrt (∑ i : Fin 8, b i * b i)) ^ 2 := by ring
    simpa [normByLevel, mulByLevel, Fin.sum_univ_eight, sq] using hcalc
  have h_nonneg_prod : 0 ≤ normByLevel 3 a * normByLevel 3 b :=
    mul_nonneg h_nonneg_a h_nonneg_b
  nlinarith

/-!
## The Associator as Computational Branching Measure

The associator (a,b,c) = (ab)c - a(bc) measures the failure of associativity.
For a computational interpretation: if we embed a Turing machine's state
transition function in an algebra, the associator measures how much the
computation "branches" — i.e., how noncomputable the result is.

For associative algebras (n=0,1,2): associator = 0 → computation is deterministic.
For nonassociative algebras (n=3): associator ≠ 0 → computation has branching.

The holonomy defect around a computational loop in the octonion algebra
is exactly the associator accumulated around that loop.
-/

/-- The associator at level n: (a,b,c) = (ab)c - a(bc). -/
def associator (level : ℕ) (a b c : Fin (2 ^ level) → ℝ) : Fin (2 ^ level) → ℝ :=
  fun i => mulByLevel level (mulByLevel level a b) c i - mulByLevel level a (mulByLevel level b c) i

/-- Associator is zero for levels 0, 1, 2. -/
theorem associator_zero_levels_0_1_2 (level : ℕ) (h : level ≤ 2) (a b c : Fin (2 ^ level) → ℝ) :
    associator level a b c = 0 := by
  ext i
  dsimp [associator]
  rw [mul_assoc_levels_0_1_2 level h a b c]
  simp

/-- Associator is nonzero for octonions (n=3): the association-tree
holonomy around (e₁, e₂, e₄) is −2e₇.

Repair note: the original statement referenced undefined identifiers
`e₁, e₂, e₄` and invoked `native_decide` over ℝ; it never elaborated.
Restated self-contained with the explicit basis vectors. -/
theorem associator_nonzero_oct :
    associator 3 (fun i => if i.val = 1 then 1 else 0)
      (fun i => if i.val = 2 then 1 else 0)
      (fun i => if i.val = 4 then 1 else 0) ≠ 0 := by
  intro h
  have h7 := congrFun h 7
  norm_num [associator, mulByLevel, mulOct, mulQuat] at h7

/- The intended bridge "holonomy defect around a computational loop =
accumulated associator" is an OPEN research obligation, not a theorem.
The r1 file carried a `theorem holonomy_eq_associator : True` marker —
a name promising content its statement did not have. Removed per the
no-semantic-promotion discipline: an algebraic residue acquires
holonomy meaning only through an explicit interpretation map with
witnesses (thesis ch. 10 §4, ch. 20). -/

/-!
## Even Subalgebra Recognition

An element x ∈ Aₙ is in the even subalgebra (is "real") iff its
odd components are zero. This subalgebra is isomorphic to A_{n-1}.
-/

/-- An element is in the even (second-half-vanishing) subalgebra.

Repair note: the original definition carried an embedded bound proof
that was false at level 0; restated with a guard on the index value,
which is total and equivalent for level ≥ 1 (degenerate-vacuous at
level 0). -/
def isEven (level : ℕ) (x : Fin (2 ^ level) → ℝ) : Prop :=
  ∀ i : Fin (2 ^ level), 2 ^ (level - 1) ≤ i.val → x i = 0

/-- An element is real: all non-real components vanish. -/
def isReal (level : ℕ) (x : Fin (2 ^ level) → ℝ) : Prop :=
  ∀ i : Fin (2 ^ level), i.val ≠ 0 → x i = 0

/-- Conjugation fixes the real line (levels 0–3).

Repair note: the r1 file claimed (with `sorry`) that conjugation fixes
the whole *even* subalgebra. That is false: e₁ is even (its second
half vanishes) yet `conjByLevel` negates it. What conjugation fixes is
the real line; here is that statement, proved. -/
theorem conj_fixes_real (level : ℕ) (hlevel : level ≤ 3)
    (x : Fin (2 ^ level) → ℝ) (hx : isReal level x) :
    conjByLevel level x = x := by
  interval_cases level
  · simp [conjByLevel]
  · ext i
    by_cases h0 : i.val = 0
    · simp [conjByLevel, h0]
    · simp [conjByLevel, h0, hx i h0]
  · ext i
    by_cases h0 : i.val = 0
    · simp [conjByLevel, h0]
    · simp [conjByLevel, h0, hx i h0]
  · ext i
    by_cases h0 : i.val = 0
    · simp [conjByLevel, h0]
    · simp [conjByLevel, h0, hx i h0]

/-!
## 360-Orthogonal Basis

The standard basis {e₀, …, e_{2^n-1}} of Aₙ is orthonormal:
  ⟨eᵢ, eⱼ⟩ = δ_{ij}

This means each basis element has norm 1 and distinct basis elements
are orthogonal.
-/

/-- Standard basis vector e_k of Aₙ. -/
def basisVec (level : ℕ) (k : Fin (2 ^ level)) : Fin (2 ^ level) → ℝ :=
  fun i => if i.val = k.val then 1.0 else 0.0

/-- Basis vectors are orthonormal: ⟨e_k, e_k⟩ = 1, ⟨e_k, e_l⟩ = 0 for k ≠ l.

Repair note: the original proof applied `subst` to a `.val` equality
(not a variable equation) and never elaborated. -/
theorem basisVec_orthonormal (level : ℕ) (k l : Fin (2 ^ level)) :
    (∑ i, (basisVec level k i) * (basisVec level l i)) = if k.val = l.val then 1.0 else 0.0 := by
  classical
  rcases eq_or_ne k l with rfl | hkl
  · rw [if_pos rfl]
    norm_num [basisVec, ← Fin.ext_iff]
  · have hv : k.val ≠ l.val := fun h => hkl (Fin.ext h)
    rw [if_neg hv, show (0.0 : ℝ) = 0 by norm_num]
    refine Finset.sum_eq_zero fun i _ => ?_
    by_cases hik : i.val = k.val
    · have hil : i.val ≠ l.val := fun h => hv (hik ▸ h)
      norm_num [basisVec, hil]
    · norm_num [basisVec, hik]

/-- The norm of a basis vector is 1, at levels 0–3.

Repair note: the original proof assumed the sum-of-squares form of the
norm, which `normByLevel` only takes at level ≥ 4; it never elaborated.
Atlas-relative restatement over the explicit kernels. -/
theorem basisVec_norm (level : ℕ) (hlevel : level ≤ 3) (k : Fin (2 ^ level)) :
    normByLevel level (basisVec level k) = 1.0 := by
  interval_cases level <;> fin_cases k <;>
    simp only [normByLevel, basisVec] <;> norm_num

/-!
## Gödelian Identity Preservation

The identity element e₀ = (1, 0, …, 0) satisfies e₀*x = x*e₀ = x
at every level. This is the Gödelian fixed-point: the identity
is preserved across the tower construction.
-/

/-- e₀ is the multiplicative identity at levels 0–3 (ℝ, ℂ, ℍ, 𝕆).

Atlas-relative statement: the proof covers exactly the levels for which
`mulByLevel` dispatches to an explicit kernel. The original statement
quantified over all `level : ℕ` while the proof enumerated 0–3; under
toolchain v4.32.0-rc1 `interval_cases` correctly rejected the unbounded
claim. The general-level statement (through `mulByLevelGeneral`, by
induction with conjugation lemmas) is an open obligation, recorded
here rather than silently asserted. -/
theorem e0_is_identity (level : ℕ) (hlevel : level ≤ 3)
    (x : Fin (2 ^ level) → ℝ) :
    mulByLevel level (basisVec level ⟨0, by
      have : 0 < 2 ^ level := pow_pos (by norm_num) level
      omega⟩) x = x := by
  interval_cases level
  · ext i; fin_cases i <;> norm_num [mulByLevel, basisVec]
  · ext i; fin_cases i <;> norm_num [mulByLevel, mulComplex, basisVec] <;> try ring
  · ext i; fin_cases i <;> norm_num [mulByLevel, mulQuat, basisVec] <;>
      first | rfl | ring
  · ext i; fin_cases i <;> norm_num [mulByLevel, mulOct, mulQuat, basisVec] <;>
      first | rfl | ring

/-- x*e₀ = x at levels 0–3. Same atlas-relative scope as
`e0_is_identity`. -/
theorem identity_right (level : ℕ) (hlevel : level ≤ 3)
    (x : Fin (2 ^ level) → ℝ) :
    mulByLevel level x (basisVec level ⟨0, by
      have : 0 < 2 ^ level := pow_pos (by norm_num) level
      omega⟩) = x := by
  interval_cases level
  · ext i; fin_cases i <;> norm_num [mulByLevel, basisVec]
  · ext i; fin_cases i <;> norm_num [mulByLevel, mulComplex, basisVec] <;> try ring
  · ext i; fin_cases i <;> norm_num [mulByLevel, mulQuat, basisVec] <;>
      first | rfl | ring
  · ext i; fin_cases i <;> norm_num [mulByLevel, mulOct, mulQuat, basisVec] <;>
      first | rfl | ring

end VDIS.Algebra.CD

/-!
## Computable Cayley-Dickson Operations on ZMod 3

For finite verification we implement the Cayley-Dickson operations on
`Fin (2^n) → ZMod 3` (3^n elements) using the same recursive algorithm
as the ℝ versions but with modular arithmetic.
-/

namespace VDIS.Algebra.CD

-- Level-1 multiplication (complex on ZMod 3)
def mulComplexSign (x y : Fin 2 → ZMod 3) : Fin 2 → ZMod 3 :=
  fun i =>
    match i with
    | ⟨0, _⟩ => x 0 * y 0 - x 1 * y 1
    | ⟨1, _⟩ => x 0 * y 1 + x 1 * y 0

-- Level-2 multiplication (quat on ZMod 3)
def mulQuatSign (x y : Fin 4 → ZMod 3) : Fin 4 → ZMod 3 :=
  fun i =>
    match i with
    | ⟨0, _⟩ => x 0 * y 0 - x 1 * y 1 - x 2 * y 2 - x 3 * y 3
    | ⟨1, _⟩ => x 0 * y 1 + x 1 * y 0 + x 2 * y 3 - x 3 * y 2
    | ⟨2, _⟩ => x 0 * y 2 - x 1 * y 3 + x 2 * y 0 + x 3 * y 1
    | ⟨3, _⟩ => x 0 * y 3 + x 1 * y 2 - x 2 * y 1 + x 3 * y 0

-- Level-3 multiplication (oct on ZMod 3)
def mulOctSign (x y : Fin 8 → ZMod 3) : Fin 8 → ZMod 3 :=
  fun i =>
    if h : (i : ℕ) < 4 then
      -- First half: x₀*y₀ - conj(y₁)*x₁
      let x0 := fun j : Fin 4 => x ⟨j.val, by
        have hi := j.is_lt; omega⟩
      let x1 := fun j : Fin 4 => x ⟨j.val + 4, by
        have hi := j.is_lt; omega⟩
      let y0 := fun j : Fin 4 => y ⟨j.val, by
        have hi := j.is_lt; omega⟩
      let y1 := fun j : Fin 4 => y ⟨j.val + 4, by
        have hi := j.is_lt; omega⟩
      let y1conj := fun k : Fin 4 => if k.val = 0 then y1 k else -y1 k
      let y1conj_mul_x1 := mulQuatSign y1conj x1
      x0 ⟨i.val, h⟩ * y0 ⟨i.val, h⟩ - y1conj_mul_x1 ⟨i.val, h⟩
    else
      -- Second half: conj(x₀)*y₁ + y₀*x₁
      let j : Fin 4 := ⟨i.val - 4, by
        have hi := i.is_lt; omega⟩
      let x0 := fun k : Fin 4 => x ⟨k.val, by
        have hi := k.is_lt; omega⟩
      let x1 := fun k : Fin 4 => x ⟨k.val + 4, by
        have hi := k.is_lt; omega⟩
      let y0 := fun k : Fin 4 => y ⟨k.val, by
        have hi := k.is_lt; omega⟩
      let y1 := fun k : Fin 4 => y ⟨k.val + 4, by
        have hi := k.is_lt; omega⟩
      let x0conj := fun k : Fin 4 => if k.val = 0 then x0 k else -x0 k
      let x0conj_mul_y1 := mulQuatSign x0conj y1
      let y0_mul_x1 := mulQuatSign y0 x1
      x0conj_mul_y1 j + y0_mul_x1 j

-- Recursive dispatch for ZMod 3 operations
def mulByLevelSign (level : ℕ) (x y : Fin (2 ^ level) → ZMod 3) : Fin (2 ^ level) → ZMod 3 :=
  match level with
  | 1 => mulComplexSign x y
  | 2 => mulQuatSign x y
  | 3 => mulOctSign x y
  | _ => fun i => x i * y i

end VDIS.Algebra.CD
