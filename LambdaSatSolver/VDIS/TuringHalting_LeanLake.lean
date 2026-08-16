import Mathlib
import LambdaSatSolver.VDIS.Algebra.CD
import LambdaSatSolver.VDIS.GyroOps.Basic

open Real

set_option maxHeartbeats 800000

noncomputable section

namespace VDIS.TuringHalting

private lemma mulQuat_zero_of_second_zero (a b : Fin 4 → ℝ) (hb : ∀ k, b k = 0) : 
    VDIS.Algebra.CD.mulQuat a b = 0 := by
  ext i : 1
  fin_cases i <;> simp [VDIS.Algebra.CD.mulQuat, hb]

def isHalting (T s : Fin 8 → ℝ) : Prop :=
  VDIS.Algebra.CD.mulByLevel 3 T s = s

def haltingSet (T : Fin 8 → ℝ) : Set (Fin 8 → ℝ) :=
  {s | isHalting T s}

def computationalHolonomy (T s : Fin 8 → ℝ) : Fin 8 → ℝ :=
  let s1 := VDIS.Algebra.CD.mulByLevel 3 T s
  let s2 := VDIS.Algebra.CD.mulByLevel 3 T s1
  let s2' := VDIS.Algebra.CD.mulByLevel 3 (VDIS.Algebra.CD.mulByLevel 3 T T) s
  fun i => s2 i - s2' i

def payorGate (T s : Fin 8 → ℝ) (tolerance : ℝ) : Prop :=
  VDIS.Algebra.CD.normByLevel 3 (computationalHolonomy T s) ≤ tolerance

def isEven (x : Fin 8 → ℝ) : Prop :=
  ∀ i : Fin 8, x i ≠ 0 → i.val < 4

def basisVec (k : Fin 8) : Fin 8 → ℝ :=
  fun i => if i.val = k.val then 1.0 else 0.0

theorem evenSubalgebra_mul_closed (x y : Fin 8 → ℝ) (hx : isEven x) (hy : isEven y) :
    isEven (VDIS.Algebra.CD.mulByLevel 3 x y) := by
  intro i h_nonzero
  by_contra hi_not_lt
  have hi_ge4 : i.val ≥ 4 := by omega
  have hx_odd : ∀ i' : Fin 8, i'.val ≥ 4 → x i' = 0 := by
    intro i' hi'
    by_contra hne
    have := hx i' hne
    have : i'.val < 4 := this
    omega
  have hy_odd : ∀ i' : Fin 8, i'.val ≥ 4 → y i' = 0 := by
    intro i' hi'
    by_contra hne
    have := hy i' hne
    have : i'.val < 4 := this
    omega
  have h_mul : VDIS.Algebra.CD.mulByLevel 3 x y = VDIS.Algebra.CD.mulOct x y := rfl
  rw [h_mul] at h_nonzero
  have h_zero : VDIS.Algebra.CD.mulOct x y i = 0 := by
    have hx_high : ∀ j : Fin 4, x ⟨j.val + 4, by
      have hj := j.2
      omega⟩ = 0 := by
      intro j; apply hx_odd; have hj := j.2
      simpa [add_comm] using Nat.le_add_left 4 j.val
    have hy_high : ∀ j : Fin 4, y ⟨j.val + 4, by
      have hj := j.2
      omega⟩ = 0 := by
      intro j; apply hy_odd; have hj := j.2
      simpa [add_comm] using Nat.le_add_left 4 j.val
    dsimp [VDIS.Algebra.CD.mulOct]
    split
    · exfalso; omega
    · have hq1 : (fun (k : Fin 4) => x ⟨k.val + 4, by
        have hk := k.2; omega⟩) = fun _ => 0 := by
        ext k; simp [hx_high k]
      have hr1 : (fun (k : Fin 4) => y ⟨k.val + 4, by
        have hk := k.2; omega⟩) = fun _ => 0 := by
        ext k; simp [hy_high k]
      simp [hq1, hr1, VDIS.Algebra.CD.mulQuat]
  exact h_nonzero h_zero

private lemma mulOct_basisVec1_s_eq (s : Fin 8 → ℝ) (i : Fin 8) :
    (VDIS.Algebra.CD.mulOct (basisVec ⟨1, by decide⟩) s) i = 
    match i with
    | 0 => - s 1
    | 1 => s 0
    | 2 => - s 3
    | 3 => s 2
    | 4 => s 5
    | 5 => - s 4
    | 6 => s 7
    | 7 => - s 6 := by
  fin_cases i <;> unfold VDIS.Algebra.CD.mulOct VDIS.Algebra.CD.mulQuat <;> simp [basisVec] <;> norm_num

theorem haltingSet_e1_eq_zero : haltingSet (basisVec ⟨1, by decide⟩) = {0} := by
  ext s
  constructor
  · intro h
    have h_eq : VDIS.Algebra.CD.mulByLevel 3 (basisVec ⟨1, by decide⟩) s = s := h
    have h_mul : VDIS.Algebra.CD.mulByLevel 3 (basisVec ⟨1, by decide⟩) s = VDIS.Algebra.CD.mulOct (basisVec ⟨1, by decide⟩) s := rfl
    have h_eq0 := congrFun h_eq 0
    have h_eq1 := congrFun h_eq 1
    have h_eq2 := congrFun h_eq 2
    have h_eq3 := congrFun h_eq 3
    have h_eq4 := congrFun h_eq 4
    have h_eq5 := congrFun h_eq 5
    have h_eq6 := congrFun h_eq 6
    have h_eq7 := congrFun h_eq 7
    rw [h_mul] at h_eq0 h_eq1 h_eq2 h_eq3 h_eq4 h_eq5 h_eq6 h_eq7
    rw [mulOct_basisVec1_s_eq s 0] at h_eq0
    rw [mulOct_basisVec1_s_eq s 1] at h_eq1
    rw [mulOct_basisVec1_s_eq s 2] at h_eq2
    rw [mulOct_basisVec1_s_eq s 3] at h_eq3
    rw [mulOct_basisVec1_s_eq s 4] at h_eq4
    rw [mulOct_basisVec1_s_eq s 5] at h_eq5
    rw [mulOct_basisVec1_s_eq s 6] at h_eq6
    rw [mulOct_basisVec1_s_eq s 7] at h_eq7
    -- h_eq0: -s1 = s0, h_eq1: s0 = s1
    -- h_eq2: -s3 = s2, h_eq3: s2 = s3
    -- h_eq4: s5 = s4, h_eq5: -s4 = s5
    -- h_eq6: s7 = s6, h_eq7: -s6 = s7
    have hs0 : s 0 = 0 := by linarith
    have hs1 : s 1 = 0 := by linarith
    have hs2 : s 2 = 0 := by linarith
    have hs3 : s 3 = 0 := by linarith
    have hs4 : s 4 = 0 := by linarith
    have hs5 : s 5 = 0 := by linarith
    have hs6 : s 6 = 0 := by linarith
    have hs7 : s 7 = 0 := by linarith
    ext i
    fin_cases i <;> simp [hs0, hs1, hs2, hs3, hs4, hs5, hs6, hs7]
  · intro h
    have hs : s = 0 := by simpa using h
    subst hs
    ext i
    fin_cases i <;> simp [haltingSet, isHalting, VDIS.Algebra.CD.mulByLevel, VDIS.Algebra.CD.mulOct, VDIS.Algebra.CD.mulQuat, basisVec]

theorem holonomy_eq_neg_associator (T s : Fin 8 → ℝ) :
    computationalHolonomy T s = fun i => -((VDIS.Algebra.CD.associator 3 T T s) i) := by
  ext i; dsimp [computationalHolonomy, VDIS.Algebra.CD.associator]; ring

theorem exists_counterexample_associator_equiv_idempotent :
    ∃ (T : Fin 8 → ℝ), ¬ (VDIS.Algebra.CD.associator 3 T T T = 0 ↔ VDIS.Algebra.CD.mulByLevel 3 T T = T) := by
  let e1 : Fin 8 → ℝ := fun i => if i.val = 1 then 1.0 else 0.0
  have h_mul_e1_e1 : VDIS.Algebra.CD.mulByLevel 3 e1 e1 = fun i => if i.val = 0 then -1.0 else 0.0 := by
    ext i
    fin_cases i <;>
    dsimp [VDIS.Algebra.CD.mulByLevel, VDIS.Algebra.CD.mulOct, VDIS.Algebra.CD.mulQuat] <;>
    simp [e1] <;>
    norm_num
  have h_assoc_zero : VDIS.Algebra.CD.associator 3 e1 e1 e1 = 0 := by
    calc
      VDIS.Algebra.CD.associator 3 e1 e1 e1
          = fun i => (VDIS.Algebra.CD.mulByLevel 3 (VDIS.Algebra.CD.mulByLevel 3 e1 e1) e1) i -
            (VDIS.Algebra.CD.mulByLevel 3 e1 (VDIS.Algebra.CD.mulByLevel 3 e1 e1)) i := rfl
      _ = fun i => (VDIS.Algebra.CD.mulByLevel 3 (fun i => if i.val = 0 then -1.0 else 0.0) e1) i -
            (VDIS.Algebra.CD.mulByLevel 3 e1 (fun i => if i.val = 0 then -1.0 else 0.0)) i := by rw [h_mul_e1_e1]
      _ = 0 := by
        ext i
        fin_cases i <;>
        dsimp [VDIS.Algebra.CD.mulByLevel, VDIS.Algebra.CD.mulOct, VDIS.Algebra.CD.mulQuat] <;>
        simp [e1] <;>
        norm_num
  have h_mul_not_idem : VDIS.Algebra.CD.mulByLevel 3 e1 e1 ≠ e1 := by
    have h_comp0 : (VDIS.Algebra.CD.mulByLevel 3 e1 e1) 0 = -1.0 := by
      dsimp [VDIS.Algebra.CD.mulByLevel, VDIS.Algebra.CD.mulOct, VDIS.Algebra.CD.mulQuat]
      simp [e1]
      norm_num
    have h_e1_comp0 : e1 0 = 0.0 := by simp [e1]
    intro h_eq
    have h_eq0 := congrFun h_eq 0
    rw [h_comp0, h_e1_comp0] at h_eq0
    norm_num at h_eq0
  refine ⟨e1, ?_⟩
  intro h_iff; apply h_mul_not_idem; exact h_iff.mp h_assoc_zero

theorem local_halting_implies_zero (s : Fin 8 → ℝ) 
    (h : VDIS.Algebra.CD.mulByLevel 3 (basisVec ⟨1, by decide⟩) s = s) : s = 0 := by
  have h_mul : VDIS.Algebra.CD.mulByLevel 3 (basisVec ⟨1, by decide⟩) s = VDIS.Algebra.CD.mulOct (basisVec ⟨1, by decide⟩) s := rfl
  have h_eq0 := congrFun h 0
  have h_eq1 := congrFun h 1
  have h_eq2 := congrFun h 2
  have h_eq3 := congrFun h 3
  have h_eq4 := congrFun h 4
  have h_eq5 := congrFun h 5
  have h_eq6 := congrFun h 6
  have h_eq7 := congrFun h 7
  rw [h_mul] at h_eq0 h_eq1 h_eq2 h_eq3 h_eq4 h_eq5 h_eq6 h_eq7
  rw [mulOct_basisVec1_s_eq s 0] at h_eq0
  rw [mulOct_basisVec1_s_eq s 1] at h_eq1
  rw [mulOct_basisVec1_s_eq s 2] at h_eq2
  rw [mulOct_basisVec1_s_eq s 3] at h_eq3
  rw [mulOct_basisVec1_s_eq s 4] at h_eq4
  rw [mulOct_basisVec1_s_eq s 5] at h_eq5
  rw [mulOct_basisVec1_s_eq s 6] at h_eq6
  rw [mulOct_basisVec1_s_eq s 7] at h_eq7
  -- h_eq0: -s1 = s0, h_eq1: s0 = s1
  -- h_eq2: -s3 = s2, h_eq3: s2 = s3
  -- h_eq4: s5 = s4, h_eq5: -s4 = s5
  -- h_eq6: s7 = s6, h_eq7: -s6 = s7
  have hs0 : s 0 = 0 := by linarith
  have hs1 : s 1 = 0 := by linarith
  have hs2 : s 2 = 0 := by linarith
  have hs3 : s 3 = 0 := by linarith
  have hs4 : s 4 = 0 := by linarith
  have hs5 : s 5 = 0 := by linarith
  have hs6 : s 6 = 0 := by linarith
  have hs7 : s 7 = 0 := by linarith
  ext i
  fin_cases i <;> simp [hs0, hs1, hs2, hs3, hs4, hs5, hs6, hs7]

theorem basisVec_orthonormal (k l : Fin 8) :
    (∑ i : Fin 8, (basisVec k i) * (basisVec l i)) = if k.val = l.val then 1.0 else 0.0 := by
  fin_cases k <;> fin_cases l <;> dsimp [basisVec] <;> norm_num

theorem basisVec_norm (k : Fin 8) :
    VDIS.Algebra.CD.normByLevel 3 (basisVec k) = 1.0 := by
  fin_cases k <;> simp [VDIS.Algebra.CD.normByLevel, basisVec] <;> norm_num

theorem basisVec_orthogonal (k l : Fin 8) (h : k.val ≠ l.val) :
    (∑ i : Fin 8, (basisVec k i) * (basisVec l i)) = 0.0 := by
  rw [basisVec_orthonormal k l]; simp [h]

end VDIS.TuringHalting
