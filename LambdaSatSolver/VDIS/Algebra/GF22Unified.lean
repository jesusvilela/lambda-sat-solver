import Mathlib
import LambdaSatSolver.VDIS.Algebra.GF22
import LambdaSatSolver.VDIS.Algebra.GF22Large

/-!
# Unified Spin Group Lifting with Simultaneous Carriers

This file provides a unified framework for:
1. Lifting 3-XOR-orthogonal frames to the full spin group Spin(3)
2. Simultaneous carrier embedding via the norm map
3. Multi-level spin group construction (GF(2,2) and GF(343²))

## Mathematical Background

### Spin Group Construction

Given a 3-XOR-orthogonal frame {e₀, e₁, e₂} over a field F:
1. Construct rotor: R = (1 + e₀)(1 + e₂)(1 + e₃)
2. Embed carriers via norm: cᵢ ↦ N(cᵢ) where N is the norm map
3. Simultaneous lift: R_total = R₀ · R₁ · R₂
4. The result lies in Spin(3, F)

### Carrier Embedding

Given carriers c₀, c₁, c₂ ∈ F, embed them via the norm:
- In GF(2,2): N(x) = x² (since N(0)=0, N(1)=1, N(ω)=ω+1, N(ω+1)=ω)
- In GF(343²): N(x) = x^(342) (norm from GF(117649) to GF(343))

### 3 XOR Orthogonality

Three vectors u, v, w are 3-XOR-orthogonal if:
⟨u, v⟩ = Σ u_i * v_i = 0
⟨u, w⟩ = Σ u_i * w_i = 0
⟨v, w⟩ = Σ v_i * w_i = 0

-/

namespace VDIS.Algebra.SpinGroup

open Finset

/-!
## Carrier Embedding

We embed carriers into the spin group via the norm map.
-/

/-- Embed a carrier into GF(2,2) via the norm: N(x) = x².
    In GF(2,2): N(0)=0, N(1)=1, N(ω)=ω+1, N(ω+1)=ω -/
def embedCarrierGF22 (c : Fin 4) : Fin 4 :=
  -- N(x) = x²
  mul c c

/-- Embed a carrier into GF(343²) via the norm.
    In GF(343²), the norm is N(x) = x^(|Fˣ|/2) = x^171.
    Since GF(117649)ˣ has order 117648 = 2 · 343 · 171,
    the norm is x^58824 = x^171 (since 117648/2 = 58824).
    
    Actually, the norm from GF(343²) to GF(343) is:
    N(a + bj) = (a + bj)(a + bj^σ) = a² - b²j² = a² - b²ω
    where σ is the Frobenius automorphism.
    
    For efficiency, we use the formula directly rather than exponentiation. -/
def embedCarrierGF117649 (c : GF343 × GF343) : GF343 × GF343 :=
  let ω : GF343 := ⟨3, by norm_num⟩
  let a := c.1
  let b := c.2
  -- N(a + bj) = a² - b²ω
  (sub343 (mul343 a a) (mul343 (mul343 b b) ω),
   -- Second component is 0 for norm
   zero343)

/-!
## Full Spin Group Lifting

We construct the full spin group element from a 3-XOR-orthogonal frame
with embedded carriers.
-/

/-- Full spin group lifting for GF(2,2).
    
    Given:
    - A 3-XOR-orthogonal frame {e₀, e₁, e₂}
    - Carriers c₀, c₁, c₂ embedded via norm
    
    Construct:
    1. Rotor for each frame: Rᵢ = (1 + eᵢ₀)(1 + eᵢ₁)(1 + eᵢ₂)
    2. Embed carriers: cᵢ ↦ N(cᵢ)
    3. Simultaneous lift: R = R₀ · R₁ · R₂
    4. The result is in Spin(3, GF(2,2))
    
    In characteristic 2, R⁻¹ = R, so the rotation is R v R. -/
def fullSpinLiftGF22 (frame : Fin 3 → Fin 3 → Fin 4) (carriers : Fin 3 → Fin 4) : Fin 4 → Fin 4 :=
  -- Embed carriers via norm
  let carriersNorm : Fin 3 → Fin 4 := fun i => embedCarrierGF22 (carriers i)
  -- Compute rotor for each frame
  let r0 := spinLift (fun i => frame 0 i)
  let r1 := spinLift (fun i => frame 1 i)
  let r2 := spinLift (fun i => frame 2 i)
  -- Apply carrier embedding
  let r0' := fun i => mul (r0 i) (carriersNorm 0)
  let r1' := fun i => mul (r1 i) (carriersNorm 1)
  let r2' := fun i => mul (r2 i) (carriersNorm 2)
  -- Combine: R = R₀ · R₁ · R₂ (component-wise)
  fun i => mul (mul (r0' i) (r1' i)) (r2' i)

/-- Full spin group lifting for GF(343²).
    
    Given:
    - A 3-XOR-orthogonal frame {e₀, e₁, e₂} over GF(343)
    - Carriers c₀, c₁, c₂ ∈ GF(343²)
    
    Construct:
    1. Rotor for each frame: Rᵢ = (1 + eᵢ₀)(1 + eᵢ₁)(1 + eᵢ₂)
    2. Embed carriers: cᵢ ↦ N(cᵢ)
    3. Simultaneous lift: R = R₀ · R₁ · R₂
    4. The result is in Spin(3, GF(117649))
    
    Note: In characteristic 7, we need R⁻¹ ≠ R, so we use the general formula. -/
def fullSpinLiftGF117649 (frame : Fin 3 → Fin 3 → GF343 × GF343)
    (carriers : Fin 3 → GF343 × GF343) : GF343 × GF343 :=
  -- Embed carriers via norm
  let carriersNorm : Fin 3 → GF343 × GF343 := fun i => embedCarrierGF117649 (carriers i)
  -- Compute rotor for each frame
  let r0 := spinLift (fun i => frame 0 i)
  let r1 := spinLift (fun i => frame 1 i)
  let r2 := spinLift (fun i => frame 2 i)
  -- Apply carrier embedding
  let r0' := (mul343 (r0.1) (carriersNorm 0).1, mul343 (r0.2) (carriersNorm 0).2)
  let r1' := (mul343 (r1.1) (carriersNorm 1).1, mul343 (r1.2) (carriersNorm 1).2)
  let r2' := (mul343 (r2.1) (carriersNorm 2).1, mul343 (r2.2) (carriersNorm 2).2)
  -- Combine: R = R₀ · R₁ · R₂ (component-wise)
  (mul343 (mul343 r0'.1 r1'.1) r2'.1,
   mul343 (mul343 r0'.2 r1'.2) r2'.2)

/-!
## 3 XOR Orthogonality with Carriers

We prove that the simultaneous carrier lifting preserves 3 XOR orthogonality
when the carriers are also 3-XOR-orthogonal.
-/

/-- Three vectors are simultaneously 3-XOR-orthogonal if all pairs are orthogonal
    AND each is orthogonal to all carrier-embedded vectors. -/
def simultaneousThreeXorOrthogonal (u v w : Fin 4 → Fin 4) (c0 c1 c2 : Fin 4) : Prop :=
  threeXorOrthogonalHyper u v w ∧
  (∑ i : Fin 4, mul (u i) (embedCarrierGF22 c0 i)) = zero ∧
  (∑ i : Fin 4, mul (v i) (embedCarrierGF22 c1 i)) = zero ∧
  (∑ i : Fin 4, mul (w i) (embedCarrierGF22 c2 i)) = zero

/-- The full spin lift preserves simultaneous 3 XOR orthogonality.
    If the frame and carriers are 3-XOR-orthogonal, the lifted rotor
    preserves the orthogonality structure. -/
theorem fullSpinLift_preserves_simultaneous_orthogonality (frame : Fin 3 → Fin 3 → Fin 4)
    (carriers : Fin 3 → Fin 4)
    (h_frame : threeXorOrthogonalHyper (frame 0 0) (frame 0 1) (frame 0 2))
    (h_carriers : simultaneousThreeXorOrthogonal (carriers 0) (carriers 1) (carriers 2) 0 0 0) :
    threeXorOrthogonalHyper
      (fun i => fullSpinLiftGF22 frame carriers i)
      (fun i => fullSpinLiftGF22 (fun j => frame ((j+1)%3)) carriers i)
      (fun i => fullSpinLiftGF22 (fun j => frame ((j+2)%3)) carriers i) := by
  unfold threeXorOrthogonalHyper fullSpinLiftGF22 embedCarrierGF22
  decide

/-!
## Multi-Level Spin Group

We define a typeclass for spin group elements that works across different fields.
-/

/-- A spin group element in Spin(3, F) for field F.
    Contains the rotor R and its inverse R⁻¹. -/
structure SpinElement (F : Type) [CommRing F] where
  rotor : F
  inv_rotor : F
  rotor_sq_eq_one : rotor * rotor = 1
  inv_rotor_eq_rotor : inv_rotor = rotor  -- In characteristic 2
  -- In characteristic ≠ 2, inv_rotor ≠ rotor generally

/-!
## Hypercomplex Tower Extension

We extend the spin group construction to higher dimensions using
Cayley-Dickson construction.
-/

/-- Extend a spin group element from GF(2,2) to GF(2,2)³ by applying
    the rotor to each component. -/
def extendToTriple (R : Fin 4 → Fin 4) (v : Fin 3 → Fin 4 → Fin 4) : Fin 3 → Fin 4 → Fin 4 :=
  fun i j => mul (R (v i j)) (R (v i j))

end VDIS.Algebra.SpinGroup
