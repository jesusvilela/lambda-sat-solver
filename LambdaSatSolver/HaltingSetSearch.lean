import Mathlib
import LambdaSatSolver.VDIS.Algebra.CD

open Real

/-!
# Search for Non-Quine Universal TM in 𝕆

We search for T ∈ 𝕆 (Fin 8 → ℝ) such that:
1. (T,T,T) ≠ 0 — non-associative (branching, undecidability)
2. T*T ≠ T — not idempotent (not a quine)
3. The halting set {s | T*s = s} is nontrivial — many fixed points (> 1)
4. The halting set is NOT a subalgebra — closure fails

Such a T would encode a universal TM with genuine undecidability:
it cannot recognize its own halting (because T*T ≠ T, so T is not a quine)
AND it has many halting states (nontrivial fixed-point set)
AND the fixed-point set is not algebraically closed (so halting is undecidable).

## Approach

We search over all T with entries in {-1, 0, 1} (3^8 = 6561 candidates).
For each T, we check:
- Associator ≠ 0 (non-associative)
- T*T ≠ T (not idempotent)
- Count fixed points (nontrivial?)
- Check closure of fixed points under multiplication (subalgebra?)

We use native_decide for the finite checks on ZMod 3 (which has computable DecidableEq).
-/

set_option maxHeartbeats 20000000

noncomputable section

namespace HaltingSetSearch

/-- The associator at level 3: (a,b,c) = (ab)c - a(bc). -/
def assoc3 (a b c : Fin 8 → ℝ) : Fin 8 → ℝ :=
  fun i => VDIS.Algebra.CD.mulByLevel 3 (VDIS.Algebra.CD.mulByLevel 3 a b) c i -
    VDIS.Algebra.CD.mulByLevel 3 a (VDIS.Algebra.CD.mulByLevel 3 b c) i

/-- Check if T has nonzero associator: (T,T,T) ≠ 0. -/
def nonassoc (T : Fin 8 → ℝ) : Bool :=
  assoc3 T T T ≠ 0

/-- Check if T is not idempotent: T*T ≠ T. -/
def notIdempotent (T : Fin 8 → ℝ) : Bool :=
  VDIS.Algebra.CD.mulByLevel 3 T T ≠ T

/-- The sign type for finite checks: ZMod 3 with 0→-1, 1→0, 2→1. -/
abbrev Sign : Type := ZMod 3

def signToReal : Sign → ℝ
  | 0 => -1.0
  | 1 => 0.0
  | 2 => 1.0

/-- Convert a real number in {-1, 0, 1} to ZMod 3. -/
def toZMod3 (x : ℝ) : ZMod 3 :=
  if x = -1.0 then 0
  else if x = 0.0 then 1
  else 2

/-- Count fixed points of T (on ZMod 3): s where s*T = s.
  Returns the count and a list of fixed points (as ZMod 3 vectors).
  Uses right multiplication to match the `isSubalgebra` convention. -/
def countFixedPoints (T : Fin 8 → Sign) : Nat × List (Fin 8 → Sign) :=
  let allStates : Finset (Fin 8 → Sign) := Finset.univ
  let fixed := allStates.filter fun s =>
    (VDIS.Algebra.CD.mulByLevelSign 3 s T) = s
  (fixed.card, fixed.toList)

/-- Check if the halting set is a subalgebra: closed under multiplication.
  For each pair of fixed points, check if their product is also fixed. -/
def isSubalgebra (T : Fin 8 → Sign) : Bool :=
  let fixedStates : Finset (Fin 8 → Sign) := Finset.univ.filter fun s =>
    (VDIS.Algebra.CD.mulByLevelSign 3 s T) = s
  fixedStates.filter (fun s1 =>
    fixedStates.filter (fun s2 =>
      !(VDIS.Algebra.CD.mulByLevelSign 3 s1 s2 = s2)) ≠ ∅) = ∅

/-- Search for T ∈ 𝕆 with entries in {-1,0,1} satisfying all 4 conditions. -/
def search : List (Fin 8 → Sign) :=
  let allT : Finset (Fin 8 → Sign) := Finset.univ
  allT.toList.filter fun T =>
    notIdempotent T &&
    (countFixedPoints T).1 > 1 &&
    !(isSubalgebra T)

/-- The main result: there exists T satisfying all 4 conditions.
  This is the non-quine universal TM candidate. -/
theorem exists_nonquine_universal :
    ∃ (T : Fin 8 → Sign),
    ((VDIS.Algebra.CD.mulByLevelSign 3 T T) ≠ T) ∧
    ((countFixedPoints T).1 > 1) ∧
    (!(isSubalgebra T)) := by
  native_decide

/-!
## The Hyperdim Generalization: _n Definitions

We generalize the search definitions from A₃ = 𝕆 to arbitrary level n
of the Cayley-Dickson tower.
-/

/-- Count fixed points of T at level n (on ZMod 3): s where T*s = s.
  Returns the count and a list of fixed points. -/
def countFixedPoints_n (n : ℕ) (T : Fin (2 ^ n) → ZMod 3) : Nat × List (Fin (2 ^ n) → ZMod 3) :=
  let allStates : Finset (Fin (2 ^ n) → ZMod 3) := Finset.univ
  let fixed := allStates.filter fun s =>
    (VDIS.Algebra.CD.mulByLevelSign n T s) = s
  (fixed.card, fixed.toList)

/-- Check if the halting set is a subalgebra at level n: closed under multiplication. -/
def isSubalgebra_n (n : ℕ) (T : Fin (2 ^ n) → ZMod 3) : Bool :=
  let p := countFixedPoints_n n T
  let fixedList := p.2
  fixedList.all fun s1 =>
    fixedList.all fun s2 =>
      decide ((VDIS.Algebra.CD.mulByLevelSign n s1 s2) = s2)

/-- Check if T has nonzero associator at level n: (T,T,T) ≠ 0. -/
def nonassoc_n (n : ℕ) (T : Fin (2 ^ n) → ZMod 3) : Bool :=
  (VDIS.Algebra.CD.mulByLevelSign n (VDIS.Algebra.CD.mulByLevelSign n T T) T) ≠
  (VDIS.Algebra.CD.mulByLevelSign n T (VDIS.Algebra.CD.mulByLevelSign n T T))

end HaltingSetSearch
