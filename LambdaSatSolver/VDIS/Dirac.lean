import Mathlib

open Real

/-!
# Dirac Operator on Finite Graphs

Formalizes the finite Dirac operator as a block operator
`D = [0 B†; B 0]` on the direct sum `H_V ⊕ H_E` of vertex and edge
Hilbert spaces.

## Key Theorems

1. **Self-adjointness**: D† = D
2. **Square identity**: D² = [B B† 0; 0 B† B]
-/

noncomputable section

namespace VDIS.Dirac

/-! ## Preliminaries -/

def inner {n : ℕ} (x y : Fin n → ℝ) : ℝ := ∑ i, x i * y i

lemma inner_symm {n : ℕ} (x y : Fin n → ℝ) : inner x y = inner y x := by
  unfold inner
  refine Finset.sum_congr rfl fun i _ => ?_
  ring

/-! ## Graph Structure -/

/-- Get the target vertex of the e-th edge. -/
def target {V E : ℕ} (edgeList : Fin E → Fin V × Fin V) (e : Fin E) : Fin V :=
  (edgeList e).2

/-- Get the source vertex of the e-th edge. -/
def source {V E : ℕ} (edgeList : Fin E → Fin V × Fin V) (e : Fin E) : Fin V :=
  (edgeList e).1

/-! ## Incidence Operator B -/

def incidenceOperator {V E : ℕ} (edgeList : Fin E → Fin V × Fin V) :
    (Fin V → ℝ) → (Fin E → ℝ) :=
  fun f e => f (target edgeList e) - f (source edgeList e)

/-! ## Adjoint B† -/

def incidenceAdjoint {V E : ℕ} (edgeList : Fin E → Fin V × Fin V) :
    (Fin E → ℝ) → (Fin V → ℝ) :=
  fun g v =>
    (∑ e : Fin E, if target edgeList e = v then g e else 0) -
    (∑ e : Fin E, if source edgeList e = v then g e else 0)

/-! ## Adjoint Lemma: inner(Bf, g) = inner(f, B†g) -/

theorem inner_incidenceOperator_eq_inner_incidenceAdjoint {V E : ℕ}
    (edgeList : Fin E → Fin V × Fin V) (f : Fin V → ℝ) (g : Fin E → ℝ) :
    inner (incidenceOperator edgeList f) g = inner f (incidenceAdjoint edgeList g) := by
  unfold inner incidenceOperator incidenceAdjoint
  calc
    ∑ e : Fin E, (f (target edgeList e) - f (source edgeList e)) * g e
        = ∑ e : Fin E, (f (target edgeList e) * g e - f (source edgeList e) * g e) := by
      refine Finset.sum_congr rfl fun e _ => ?_
      ring
    _ = (∑ e : Fin E, f (target edgeList e) * g e) - (∑ e : Fin E, f (source edgeList e) * g e) := by
      rw [Finset.sum_sub_distrib]
    _ = (∑ v : Fin V, f v * (∑ e : Fin E, if target edgeList e = v then g e else 0)) -
        (∑ v : Fin V, f v * (∑ e : Fin E, if source edgeList e = v then g e else 0)) := by
      have h_target : (∑ e : Fin E, f (target edgeList e) * g e) =
          (∑ v : Fin V, f v * (∑ e : Fin E, if target edgeList e = v then g e else 0)) := by
        calc
          (∑ e : Fin E, f (target edgeList e) * g e)
              = (∑ e : Fin E, ∑ v : Fin V, if target edgeList e = v then f v * g e else 0) := by
            refine Finset.sum_congr rfl fun e _ => ?_
            calc
              f (target edgeList e) * g e
                  = (∑ v : Fin V, if v = target edgeList e then f v * g e else 0) := by
                rw [Finset.sum_eq_single (target edgeList e)]
                · simp
                · intro v _ hv
                  simp [hv]
                · simp
              _ = (∑ v : Fin V, if target edgeList e = v then f v * g e else 0) := by
                refine Finset.sum_congr rfl fun v _ => ?_
                by_cases h : target edgeList e = v
                · simp [h]
                · have h' : v ≠ target edgeList e := mt Eq.symm h
                  simp [h, h']
          _ = (∑ v : Fin V, ∑ e : Fin E, if target edgeList e = v then f v * g e else 0) :=
            Finset.sum_comm
          _ = (∑ v : Fin V, f v * (∑ e : Fin E, if target edgeList e = v then g e else 0)) := by
            refine Finset.sum_congr rfl fun v _ => ?_
            rw [Finset.mul_sum]
            refine Finset.sum_congr rfl fun e _ => ?_
            by_cases h : target edgeList e = v
            · simp [h]
            · simp [h]
      have h_source : (∑ e : Fin E, f (source edgeList e) * g e) =
          (∑ v : Fin V, f v * (∑ e : Fin E, if source edgeList e = v then g e else 0)) := by
        calc
          (∑ e : Fin E, f (source edgeList e) * g e)
              = (∑ e : Fin E, ∑ v : Fin V, if source edgeList e = v then f v * g e else 0) := by
            refine Finset.sum_congr rfl fun e _ => ?_
            calc
              f (source edgeList e) * g e
                  = (∑ v : Fin V, if v = source edgeList e then f v * g e else 0) := by
                rw [Finset.sum_eq_single (source edgeList e)]
                · simp
                · intro v _ hv
                  simp [hv]
                · simp
              _ = (∑ v : Fin V, if source edgeList e = v then f v * g e else 0) := by
                refine Finset.sum_congr rfl fun v _ => ?_
                by_cases h : source edgeList e = v
                · simp [h]
                · have h' : v ≠ source edgeList e := mt Eq.symm h
                  simp [h, h']
          _ = (∑ v : Fin V, ∑ e : Fin E, if source edgeList e = v then f v * g e else 0) :=
            Finset.sum_comm
          _ = (∑ v : Fin V, f v * (∑ e : Fin E, if source edgeList e = v then g e else 0)) := by
            refine Finset.sum_congr rfl fun v _ => ?_
            rw [Finset.mul_sum]
            refine Finset.sum_congr rfl fun e _ => ?_
            by_cases h : source edgeList e = v
            · simp [h]
            · simp [h]
      rw [h_target, h_source]
    _ = (∑ v : Fin V, f v * ((∑ e : Fin E, if target edgeList e = v then g e else 0) -
                            (∑ e : Fin E, if source edgeList e = v then g e else 0))) := by
      simp_rw [mul_sub]
      rw [← Finset.sum_sub_distrib]

/-! ## Dirac Operator D = [0 B; B† 0] -/

def diracOperator {V E : ℕ} (edgeList : Fin E → Fin V × Fin V) :
    (Fin (E + V) → ℝ) → (Fin (E + V) → ℝ) :=
  fun ψ i =>
    if h : (i : ℕ) < E then
      incidenceOperator edgeList (fun v => ψ (Fin.natAdd E v)) ⟨i.val, h⟩
    else
      have hge : E ≤ (i : ℕ) := Nat.le_of_not_lt h
      incidenceAdjoint edgeList (fun e => ψ (Fin.castAdd V e)) ⟨(i : ℕ) - E, by
        have hi := i.is_lt
        omega⟩

/-! ## Self-Adjointness: inner(Dψ, φ) = inner(ψ, Dφ) -/

theorem dirac_self_adjoint {V E : ℕ} (edgeList : Fin E → Fin V × Fin V)
    (ψ φ : Fin (E + V) → ℝ) :
    (∑ i, (diracOperator edgeList ψ i) * φ i) =
    (∑ i, ψ i * (diracOperator edgeList φ i)) := by
  -- Expand diracOperator
  have hDψ : ∀ i, (diracOperator edgeList ψ i) * φ i =
      (if h : (i : ℕ) < E then
        (incidenceOperator edgeList (fun v => ψ (Fin.natAdd E v)) ⟨i.val, h⟩) * φ i
      else
        (incidenceAdjoint edgeList (fun e => ψ (Fin.castAdd V e)) ⟨(i : ℕ) - E, by
          have hi := i.is_lt
          have hge : E ≤ (i : ℕ) := Nat.le_of_not_lt h
          omega⟩) * φ i) := by
    intro i; simp [diracOperator]
  have hDφ : ∀ i, ψ i * (diracOperator edgeList φ i) =
      (if h : (i : ℕ) < E then
        ψ i * (incidenceOperator edgeList (fun v => φ (Fin.natAdd E v)) ⟨i.val, h⟩)
      else
        ψ i * (incidenceAdjoint edgeList (fun e => φ (Fin.castAdd V e)) ⟨(i : ℕ) - E, by
          have hi := i.is_lt
          have hge : E ≤ (i : ℕ) := Nat.le_of_not_lt h
          omega⟩)) := by
    intro i; simp [diracOperator]
  simp_rw [hDψ, hDφ]
  -- Split the sum into Fin E and Fin V parts using the natural bijection
  -- We use the equivalence between Fin (E+V) and Fin E ⊕ Fin V
  -- The sum over Fin (E+V) can be decomposed using Fin.castAdd and Fin.natAdd
  have h_split : ∀ (f : Fin (E + V) → ℝ),
      (∑ i, f i) = (∑ e : Fin E, f (Fin.castAdd V e)) + (∑ v : Fin V, f (Fin.natAdd E v)) := by
    intro f
    -- This is a standard identity: Fin (E+V) ≃ Fin E ⊕ Fin V
    -- We can prove it using Finset.sum_finset_product or similar
    -- For now, use the existing lemma if available, otherwise prove directly
    rw [Fin.sum_univ_add]
  rw [h_split (fun i => (if h : (i : ℕ) < E then
        (incidenceOperator edgeList (fun v => ψ (Fin.natAdd E v)) ⟨i.val, h⟩) * φ i
      else
        (incidenceAdjoint edgeList (fun e => ψ (Fin.castAdd V e)) ⟨(i : ℕ) - E, by
          have hi := i.is_lt
          have hge : E ≤ (i : ℕ) := Nat.le_of_not_lt h
          omega⟩) * φ i)),
    h_split (fun i => (if h : (i : ℕ) < E then
        ψ i * (incidenceOperator edgeList (fun v => φ (Fin.natAdd E v)) ⟨i.val, h⟩)
      else
        ψ i * (incidenceAdjoint edgeList (fun e => φ (Fin.castAdd V e)) ⟨(i : ℕ) - E, by
          have hi := i.is_lt
          have hge : E ≤ (i : ℕ) := Nat.le_of_not_lt h
          omega⟩)))]
  -- Now simplify the conditionals
  simp
  -- Now we have:
  -- (∑ e : Fin E, (B ψ_V) e * φ(castAdd e)) + (∑ v : Fin V, (B† ψ_E) v * φ(natAdd v))
  -- = (∑ e : Fin E, ψ(castAdd e) * (B φ_V) e) + (∑ v : Fin V, ψ(natAdd v) * (B† φ_E) v)
  -- where ψ_V v = ψ(natAdd v), ψ_E e = ψ(castAdd e)
  set ψV : Fin V → ℝ := fun v => ψ (Fin.natAdd E v) with hψV
  set ψE : Fin E → ℝ := fun e => ψ (Fin.castAdd V e) with hψE
  set φV : Fin V → ℝ := fun v => φ (Fin.natAdd E v) with hφV
  set φE : Fin E → ℝ := fun e => φ (Fin.castAdd V e) with hφE
  simp [hψV, hψE, hφV, hφE]
  -- Now the goal is:
  -- (∑ e, (B ψV) e * φE e) + (∑ v, (B† ψE) v * φV v)
  -- = (∑ e, ψE e * (B φV) e) + (∑ v, ψV v * (B† φE) v)
  -- Use the adjoint lemma
  have h_edge : (∑ e : Fin E, (incidenceOperator edgeList ψV e) * φE e) =
      (∑ v : Fin V, ψV v * (incidenceAdjoint edgeList φE v)) := by
    calc
      (∑ e : Fin E, (incidenceOperator edgeList ψV e) * φE e)
          = inner (incidenceOperator edgeList ψV) φE := by
        unfold inner; simp
      _ = inner ψV (incidenceAdjoint edgeList φE) :=
        inner_incidenceOperator_eq_inner_incidenceAdjoint edgeList ψV φE
      _ = (∑ v : Fin V, ψV v * (incidenceAdjoint edgeList φE v)) := by
        unfold inner; simp
  have h_vertex : (∑ v : Fin V, (incidenceAdjoint edgeList ψE v) * φV v) =
      (∑ e : Fin E, ψE e * (incidenceOperator edgeList φV e)) := by
    calc
      (∑ v : Fin V, (incidenceAdjoint edgeList ψE v) * φV v)
          = inner (incidenceAdjoint edgeList ψE) φV := by
        unfold inner; simp
      _ = inner φV (incidenceAdjoint edgeList ψE) := inner_symm _ _
      _ = inner (incidenceOperator edgeList φV) ψE := by
        rw [inner_incidenceOperator_eq_inner_incidenceAdjoint edgeList φV ψE]
      _ = inner ψE (incidenceOperator edgeList φV) := inner_symm _ _
      _ = (∑ e : Fin E, ψE e * (incidenceOperator edgeList φV e)) := by
        unfold inner; simp
  rw [h_edge, h_vertex]
  ring

/-! ## Square Identity: D² = [B B† 0; 0 B† B] -/

theorem dirac_square {V E : ℕ} (edgeList : Fin E → Fin V × Fin V)
    (ψ : Fin (E + V) → ℝ) :
    (diracOperator edgeList (diracOperator edgeList ψ)) =
    fun (i : Fin (E + V)) =>
      if h : (i : ℕ) < E then
        incidenceOperator edgeList
          (fun w => incidenceAdjoint edgeList (fun e => ψ (Fin.castAdd V e)) w)
          ⟨i.val, h⟩
      else
        incidenceAdjoint edgeList
        (fun w => incidenceOperator edgeList (fun v => ψ (Fin.natAdd E v)) w)
        ⟨(i : ℕ) - E, by
          omega⟩ := by
  ext i
  dsimp [diracOperator]
  by_cases h : (i : ℕ) < E
  · simp [h]
  · simp [h]

end VDIS.Dirac
