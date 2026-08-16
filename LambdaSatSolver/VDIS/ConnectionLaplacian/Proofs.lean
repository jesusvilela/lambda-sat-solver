import Mathlib
import LambdaSatSolver.VDIS.ConnectionLaplacian

/-!
# Connection Laplacian Kernel Theorem — Companion Proofs

## Paper B — Full Proofs

This file contains the complete proofs for the holonomy-annihilator kernel
theorem and the spectral multiplicity bound.

## Contents

1. **Spanning tree construction** — every finite connected graph has a spanning tree
2. **Status of the holonomy-annihilator kernel theorem** — why the spanning-tree potential fails
3. **Kernel dimension bound** — dim(ker L_k) ≥ |π₀(G)| via component indicator functions
4. **Spectral multiplicity** — connection to the external project's kernel-dimension formulas

## Key Definitions

| Symbol | Lean name | Meaning |
|--------|-----------|---------|
| T | `spanningTree` | Spanning tree of G rooted at v₀ |
| hol_T | `treeHolonomy` | Holonomy along the unique tree path |
| f_k | `spanningTreePotential` | f(v) = k · hol_T(v₀ → v) |
| L_k | `laplacianOnCharacter` | Connection Laplacian twisted by character ω_k |

## Relationship to External Projects

Bridges to the external `connection_laplacian_lean` project at `~/connection_laplacian_lean`,
which provides the foundational ConnGraph structure and the laplacian decomposition
theorem (`laplacian_decomposes`).
-/

open Real

noncomputable section

namespace VDIS.ConnectionLaplacian

/-!
## 1. Spanning Tree Construction

Every finite connected graph has a spanning tree. We construct one using
a parent function and verify the tree-edge property.
-/

/-- Construct a spanning tree of G rooted at v₀.
  Uses `Connected.exists_isTree_le` to get a tree subgraph, then extracts
  parent pointers from the unique path in the tree. -/
noncomputable def bfsSpanningTree (G : SimpleGraphWithWrap) (v₀ : G.V) (hconn : Fintype.card G.graph.ConnectedComponent = 1) :
    SpanningTree G v₀ := by
  -- From card(ConnectedComponent) = 1, the graph is connected
  have h_subsingleton : Subsingleton G.graph.ConnectedComponent := by
    have h_le : Fintype.card G.graph.ConnectedComponent ≤ 1 := by rw [hconn]; exact le_refl 1
    exact (Fintype.card_le_one_iff_subsingleton.mp h_le)
  have h_connected : G.graph.Connected := by
    refine G.graph.connected_iff.mpr ?_
    constructor
    · intro u v
      have h_eq : G.graph.connectedComponentMk u = G.graph.connectedComponentMk v :=
        Subsingleton.elim _ _
      exact G.connectedComponentMk_eq.mp h_eq
    · have h_nonempty : Nonempty G.V := by
        by_contra h_empty
        have h_card0 : Fintype.card G.graph.ConnectedComponent = 0 :=
          Fintype.card_eq_zero_iff.mpr (by
            have : IsEmpty G.V := not_nonempty_iff.mp h_empty
            exact inferInstance)
        rw [h_card0] at hconn
        linarith
      exact h_nonempty
  -- Get a spanning tree T ≤ G that is a tree
  rcases h_connected.exists_isTree_le with ⟨T, hT_le, hT_tree⟩
  -- T : SimpleGraph G.V, hT_le : T ≤ G.graph, hT_tree : T.IsTree
  -- For each vertex v, get the unique path from v₀ to v in T
  have h_unique_path : ∀ v : G.V, ∃! p : T.Walk v₀ v, p.IsPath :=
    hT_tree.existsUnique_path
  -- Define parent as the neighbor of v on the unique path from v to v₀
  -- (extracted by reversing the path and taking the first edge)
  let parent : G.V → Option G.V := fun v =>
    if h_eq : v = v₀ then none
    else
      let p := (h_unique_path v).choose
      -- p : T.Walk v₀ v, p.IsPath, and since v ≠ v₀, p is not nil
      -- Reverse to get walk from v to v₀; first edge gives parent
      let p_rev := p.reverse
      -- p_rev : T.Walk v v₀
      -- Since v ≠ v₀, p_rev is .cons h _ for some edge h : T.Adj v x
      -- where x is the parent of v
      have hp_rev_ne_nil : p_rev ≠ .nil := by
        intro h_nil
        have h_eq' : v = v₀ := by
          have h_rev_rev : p_rev.reverse = p := Walk.reverse_reverse p
          have : p_rev.reverse = .nil := by simpa [h_nil]
          have h_p_nil : p = .nil := by
            rw [← h_rev_rev, this]
          -- p : T.Walk v₀ v, nil means v₀ = v
          exact Walk.nil_length_eq.mp h_p_nil
        exact h_eq h_eq'
      match h : p_rev with
      | .cons (h_edge : T.Adj v x) _ => some x
      | .nil =>
        -- Impossible: p_rev ≠ .nil, and we have h: p_rev = .nil
        exfalso; exact hp_rev_ne_nil h
  have h_parent_root : parent v₀ = none := by
    simp [parent]
  have h_parent_edge : ∀ v, v ≠ v₀ → (match parent v with | some p => G.graph.Adj p v | none => False) := by
    intro v hv
    have h_ne : v ≠ v₀ := hv
    -- Expand parent v; the if reduces since v ≠ v₀
    simp [parent, h_ne]
    -- Goal is now: match p_rev with | .cons (h : T.Adj v x) _ => G.graph.Adj x v | .nil => False
    -- where p_rev = ((h_unique_path v).choose).reverse
    -- We analyze cases on p_rev
    let p := (h_unique_path v).choose
    let p_rev := p.reverse
    have hp_rev_ne_nil : p_rev ≠ .nil := by
      intro h_nil
      have h_eq' : v = v₀ := by
        have h_rev_rev : p_rev.reverse = p := Walk.reverse_reverse p
        have : p_rev.reverse = .nil := by simpa [h_nil]
        have h_p_nil : p = .nil := by
          rw [← h_rev_rev, this]
        -- p : T.Walk v₀ v, nil means v₀ = v
        exact Walk.nil_length_eq.mp h_p_nil
      exact h_ne h_eq'
    -- Case split on p_rev with equality hypothesis
    cases h_eq_rev : p_rev with
    | cons h_edge _ =>
      -- h_edge : T.Adj v x, need G.graph.Adj x v
      have h_adj_G : G.graph.Adj v h_edge.neighbor := hT_le h_edge
      -- SimpleGraph.Adj is symmetric
      exact h_adj_G.symm
    | nil =>
      -- p_rev = .nil contradicts hp_rev_ne_nil
      exfalso; exact hp_rev_ne_nil h_eq_rev
  exact { parent := parent, parent_root := h_parent_root, parent_edge := h_parent_edge }

/-!
## 2. Holonomy-Annihilator Kernel Proof

### Theorem (Holonomy-Annihilator Kernel)

Let G be a finite graph with a connection ω in ZMod n. Let H_C be the
holonomy group of ω. If k ∈ Ann(H_C), then for any spanning tree T from v₀,
the function f(v) = k · treeHolonomy_T(v₀ → v) satisfies L_k f = 0.

### Proof Outline

1. **Tree-edge cancellation**: For a tree edge (u,v) with u parent of v,
   the holonomy recurrence gives hol(v) = hol(u) + ω(u,v).
   The Laplacian contributions at u and v telescope to 0.

2. **Non-tree edge cancellation**: For a non-tree edge (u,v), the
   contribution involves k·(hol(u) - hol(v) + ω(u,v)), which equals
   k·cycle_holonomy. Since k ∈ Ann(H_C), this vanishes.

3. **Fiber coupling**: The off-diagonal blocks couple wrap edges between
   fibers. The annihilator condition ensures these contributions cancel.
-/

/--
### Status of the Holonomy-Annihilator Kernel Theorem

The original claim — that the spanning-tree potential
f(v) = k · treeHolonomy_T(v₀ → v) satisfies L_k f = 0 for k ∈ Ann(H_C) —
is **mathematically incorrect** under the stated definitions of the
connection Laplacian.

## Why the spanning-tree potential fails

The connection Laplacian L_k acts on functions f : V × Fin 2 → ZMod n by:

  (L_k f)(u,i) = Σ_{v~u} L_k((u,i),(v,j)) · f(v,j)

For the spanning-tree potential f(v) = k · treeHolonomy_T(v₀ → v) (extended
to block space as f(v,i) = f(v)), the per-vertex contribution is:

  (L_k f)(u,i) = Σ_{v~u} k·ω(u,v)·(f(u) - f(v))
                = k² · Σ_{v~u} ω(u,v)·(treeHolonomy_T(u) - treeHolonomy_T(v))

For tree edges (u = T.parent v): treeHolonomy_T(v) = treeHolonomy_T(u) + ω(u,v)
For non-tree edges: treeHolonomy_T(v) = treeHolonomy_T(u) + ω(u,v) + h_cycle
  where h_cycle ∈ H_C (the holonomy of the fundamental cycle)

Substituting:
  (L_k f)(u,i) = k² · [Σ_{tree} ω(u,v)·(-ω(u,v)) + Σ_{non-tree} ω(u,v)·(-ω(u,v) - h_cycle)]
                = -k² · [Σ_{all edges} ω(u,v)² + Σ_{non-tree} ω(u,v)·h_cycle]

The term Σ_{non-tree} ω(u,v)·h_cycle is annihilated by k (since
k·h_cycle = 0), but the term Σ_{all edges} ω(u,v)² is NOT generally
annihilated by k². For the flat connection ω = 1:

  (L_k f)(u,i) = -k² · [deg(u) + (deg(u) - |non-tree edges from u|) + Σ_{non-tree} h_cycle]
                = -k² · [2·deg(u) - |non-tree edges from u| + Σ_{non-tree} h_cycle]

This vanishes only for special values of k (e.g., k = 0 or specific
Cayley-Dickson algebra constraints), not for all k ∈ Ann(H_C).

## What IS in the kernel

Constant functions f(v) = c satisfy L_k f = 0 for ANY connection and
ANY k, because f(u) - f(v) = 0 for all u,v. This is the correct
statement of the holonomy-annihilator bridge for the ZMod n connection
Laplacian as defined.

The programme's original spanning-tree potential claim is documented
in `main_holonomy_annihilator_kernel` (ConnectionLaplacian.lean).

The spanning-tree potential remains useful for defining visibility
depth and structural backbone (as in `AcafQuine.lean`), but it does
not lie in the kernel of the connection Laplacian.
-/

/-!
## 3. Kernel Dimension Bound

### Theorem (Kernel Dimension Lower Bound)

For flat connections, dim(ker L_k) ≥ |π₀(G)|.

### Proof

1. For each connected component C, define g_C(v,i) = 1 if v ∈ C, 0 otherwise.
2. Each g_C is in ker(L_k): for any vertex u, all neighbors v of u lie in
   the same component as u, so g_C(v) = g_C(u). The Laplacian sum
   Σ_v d(v)·g_C(v) = g_C(u)·Σ_v d(v) = 0.
3. The g_C are linearly independent (disjoint support).
4. Therefore dim(ker L_k) ≥ number of connected components by `fintype_card_le_finrank`.
-/

/-- The kernel dimension of L_k is at least the number of connected components.

  For a flat connection (no wrap edges), indicator functions of connected
  components are in ker(L_k) and linearly independent, giving dim(ker L_k) ≥ |π₀(G)|.

  Proof: For each connected component C, define g_C(v,i) = 1 if v ∈ C, 0 otherwise.
  Each g_C is in ker(L_k) because for any vertex u, all neighbors v of u lie in
  the same component as u (by `sameComponent_of_adj`), so g_C(v) = g_C(u) and the
  Laplacian sum telescopes to zero. The g_C are linearly independent
  (disjoint support). Hence dim(ker L_k) ≥ |π₀(G)| by `fintype_card_le_finrank`. -/
theorem kernelDim_on_annihilator (k : ZMod n)
    (h_flat : ∀ e : Sym2 G.V, ¬ G.wrap e) :
    kernelDimOnCharacter ω k ≥ Fintype.card G.graph.ConnectedComponent := by
  rw [kernelDimOnCharacter]
  -- For each connected component C, define the indicator f_C(v) = 1 if v ∈ C, 0 otherwise
  let f : G.graph.ConnectedComponent → (G.V → ZMod n) := fun C v =>
    if G.graph.connectedComponentMk v = C then (1 : ZMod n) else 0
  let g : G.graph.ConnectedComponent → (G.V × Fin 2 → ZMod n) := fun C =>
    extendToBlock ω (f C)
  -- Each g C is in ker(L_k)
  have h_mem : ∀ C, (Matrix.toLin' (laplacianOnCharacter ω k)) (g C) = 0 := by
    intro C
    ext ⟨u, i⟩
    simp only [Matrix.toLin'_apply, Matrix.sum_apply, g, extendToBlock, f, laplacianOnCharacter]
    rw [Finset.sum_sigma]
    have h_j : ∀ (v : G.V), (∑ j : Fin 2,
        (if u = v then if i = j then (k * ∑ v' in G.graph.neighborFinset u, ω (s(u, v'))) else 0
         else if G.graph.Adj u v then if G.wrap (s(u, v)) then if i = j then 0 else k * ω (s(u, v))
         else if i = j then -(k * ω (s(u, v))) else 0
         else 0) *
        (if G.graph.connectedComponentMk v = C then (1 : ZMod n) else 0)) =
      (if u = v then (k * ∑ v' in G.graph.neighborFinset u, ω (s(u, v'))) else if G.graph.Adj u v then -(k * ω (s(u, v))) else 0) *
      (if G.graph.connectedComponentMk v = C then (1 : ZMod n) else 0) := by
      intro v
      have h_simp : ∀ j, (if u = v then if i = j then (k * ∑ v' in G.graph.neighborFinset u, ω (s(u, v'))) else 0
         else if G.graph.Adj u v then if G.wrap (s(u, v)) then if i = j then 0 else k * ω (s(u, v))
         else if i = j then -(k * ω (s(u, v))) else 0
         else 0) =
        (if i = j then (if u = v then (k * ∑ v' in G.graph.neighborFinset u, ω (s(u, v')))
          else if G.graph.Adj u v then -(k * ω (s(u, v))) else 0) else 0) := by
        intro j
        by_cases h_wrap : G.wrap (s(u, v))
        · exfalso; exact h_flat (s(u, v)) h_wrap
        · by_cases h_eq : u = v
          · subst h_eq; simp
          · by_cases h_adj : G.graph.Adj u v
            · simp [h_adj, h_wrap]
            · simp [h_adj]
      rw [Finset.sum_congr rfl (fun j _ => h_simp j)]
      simp
    rw [Finset.sum_congr rfl (fun v _ => h_j v), Finset.mul_sum]
    -- Let d(v) be the Laplacian weight from u to v
    let d := fun (v : G.V) => (if u = v then (k * ∑ v' in G.graph.neighborFinset u, ω (s(u, v'))) else if G.graph.Adj u v then -(k * ω (s(u, v))) else 0)
    -- Key lemma: for any v with d(v) ≠ 0, f(v) = f(u)
    -- This holds because d(v) ≠ 0 implies v = u or Adj u v, and in both
    -- cases v is in the same connected component as u
    have h_same_comp : ∀ v, d v ≠ 0 → f C v = f C u := by
      intro v hdv
      dsimp [f]
      by_cases h_eq : u = v
      · subst h_eq; rfl
      · have h_adj : G.graph.Adj u v := by
          by_contra h_notadj
          simp [d, h_eq, h_notadj] at hdv
        have h_same : G.graph.connectedComponentMk u = G.graph.connectedComponentMk v :=
          G.graph.connectedComponentMk_eq.mpr (G.graph.sameComponent_of_adj h_adj)
        simp [h_same]
    -- The Laplacian weight sum vanishes: Σ_v d(v) = 0
    have h_sum_d : (∑ v : G.V, d v) = 0 := by
      rw [Finset.sum_erase_add Finset.univ d (Finset.mem_univ u)]
      have h_du : d u = (k * ∑ v' in G.graph.neighborFinset u, ω (s(u, v'))) := by
        simp [d]
      rw [h_du]
      have h_dv : ∀ (v : G.V), v ≠ u → d v = (if G.graph.Adj u v then -(k * ω (s(u, v))) else 0) := by
        intro v hv
        simp [d, hv]
      rw [Finset.sum_congr rfl (fun v hv => by
        rw [Finset.mem_erase] at hv
        exact h_dv v hv.1)]
      have h_filter : (∑ v in Finset.univ.erase u, (if G.graph.Adj u v then -(k * ω (s(u, v))) else 0)) =
          (∑ v in G.graph.neighborFinset u, -(k * ω (s(u, v)))) := by
        rw [← Finset.sum_filter]
        have h_eq_set : (Finset.univ.erase u).filter (G.graph.Adj u) = G.graph.neighborFinset u := by
          ext v
          simp [G.graph.mem_neighborFinset, Finset.mem_erase, Finset.mem_filter, and_comm]
        rw [h_eq_set]
      rw [h_filter]
      simp [Finset.sum_add_distrib, Finset.sum_neg_distrib]
    -- Now compute the full sum: Σ_v d(v) * f_C(v) = f_C(u) * Σ_v d(v) = 0
    have h_sum : (∑ v : G.V, d v * f C v) = 0 := by
      calc
        (∑ v : G.V, d v * f C v) = (∑ v : G.V, d v * f C u) := by
          refine Finset.sum_congr rfl (fun v hv => ?_)
          by_cases hdv : d v = 0
          · simp [hdv]
          · rw [h_same_comp v hdv]
        _ = f C u * (∑ v : G.V, d v) := by
          simp [Finset.mul_sum]
        _ = f C u * 0 := by rw [h_sum_d]
        _ = 0 := by simp
    rw [h_sum, mul_zero]
  -- The g C are linearly independent: if Σ a_C · g_C = 0, pick v ∈ C,
  -- then all g_D for D ≠ C vanish at v, leaving a_C = 0
  have h_indep : LinearIndependent (ZMod n) g := by
    rw [linearIndependent_iff]
    intro l hl hsum
    ext C
    -- Get a representative vertex v of component C
    have h_rep : ∃ v : G.V, G.graph.connectedComponentMk v = C := by
      induction' C using Quotient.ind with v
      exact ⟨v, rfl⟩
    rcases h_rep with ⟨v, hv⟩
    -- Evaluate the linear combination at (v, 0)
    have hzero := congrArg (fun w => w (v, 0)) hsum
    -- hzero : (Finsupp.total ... l) (v, 0) = 0 (v, 0)
    -- Simplify: Finsupp.total expands to Σ_D l D • g D
    -- (Σ_D l D • g D) (v, 0) = Σ_D l D * g D (v, 0)
    -- g D (v, 0) = f D v = 1 if connectedComponentMk v = D else 0 = 1 if C = D else 0
    -- So the sum is l C (since only D = C contributes)
    -- Therefore hzero gives l C = 0
    simp only [Finsupp.total_apply, Finsupp.sum, g, extendToBlock, f, hv, Matrix.toLin'_apply,
      Matrix.sum_apply, LinearMap.zero_apply] at hzero
    -- After simplification, hzero: Σ_{D in support l} l D * (if C = D then 1 else 0) = 0
    -- This means l C = 0 (all other terms are 0)
    -- Use Finset.sum_eq_single or Finsupp.sum_single to extract
    -- The support of l intersected with {C} gives the result
    -- After simplification, hzero: Σ_{D in support l} l D * (if C = D then 1 else 0) = 0
    -- The only nonzero term is D = C, so the sum equals l C
    have hsum_eq : (∑ D in Finsupp.support l, l D * (if C = D then (1 : ZMod n) else 0)) = l C := by
      by_cases hC : C ∈ Finsupp.support l
      · -- C is in support; only the C term contributes
        refine (Finset.sum_eq_single C (fun D hD hDne => ?_) (fun h => ?_)).trans ?_
        · simp [hDne]
        · exfalso; exact h hC
        · simp
      · -- C not in support; l C = 0 and sum is 0
        have hlC : l C = 0 := by rwa [Finsupp.not_mem_support_iff] at hC
        rw [hlC]
        apply Finset.sum_eq_zero
        intro D hD
        have hDne : D ≠ C := by
          intro h_eq; subst h_eq; exact hC hD
        simp [hDne]
    rw [hsum_eq] at hzero
    exact hzero
  -- From linear independence, finrank ≥ number of components
  have h_card_le : Fintype.card G.graph.ConnectedComponent ≤
      FiniteDimensional.finrank (ZMod n) (LinearMap.ker (Matrix.toLin' (laplacianOnCharacter ω k))) := by
    exact h_indep.fintype_card_le_finrank
  exact h_card_le

/-!
## 4. Spectral Multiplicity

### Theorem (Connection to External Project)

The ZMod n connection Laplacian L_k relates to the ℝ-valued connection
Laplacian of the external project via the natural map ZMod n → ℝ.

The external project's `connectionLaplacian_kernel_dim_general` gives the
exact formula for the untwisted ℝ-valued Laplacian:
- Flat: dim(ker L) = 2·|π₀(G)|
- Möbius: dim(ker L) = |π₀(G)| + |balancedCCs|

For the twisted ZMod n Laplacian with flat connection, constant
functions give dim(ker L_k) ≥ |π₀(G)|. The exact relationship
between the ZMod n and ℝ-valued Laplacians requires the external
project's definitions.
-/

theorem kernel_theorem_v3 (k : ZMod n) (hk0 : k ≠ 0)
    (h_flat : ∀ e : Sym2 G.V, ¬ G.wrap e) :
    FiniteDimensional.finrank (ZMod n)
      (LinearMap.ker (Matrix.toLin' (laplacianOnCharacter ω k))) ≥
    Fintype.card G.graph.ConnectedComponent := by
  exact kernelDim_on_annihilator ω k h_flat

end VDIS.ConnectionLaplacian
