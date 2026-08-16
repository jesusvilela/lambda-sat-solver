import LambdaSatSolver.VDIS.Algebra.CD
import LambdaSatSolver.VDIS.WeaveShadow

/-!
# Hypercomplex Mind Games

Three thought experiments posed against *The Weave Never Ends* (r2) and
then mechanized in the repository's own Cayley–Dickson kernel
(`VDIS.Algebra.CD`). Each game isolates one carrier from the thesis and
asks the same question from an independent angle (three-angle floor):

**what does an endpoint-level verdict fail to determine?**

| Game | Carrier | Thesis anchor |
|------|---------|---------------|
| 1. The Null Courier | split-signature ℤ⁴ | theorem-seed *Null cancellation with nontrivial holonomy*; Prop. *Scalar non-certification* |
| 2. The Two Couriers | ℍ (level 2 kernel) | theorem-seed *Visible verdict agreement without diamond closure*; braid order content |
| 3. The Bracket Amnesiac | 𝕆 (level 3 kernel) | association holonomy `Ω_assoc`; "an un-gen-weave that recovers the endpoint but not the association tree has not recovered the same object" |

Boundary (thesis ch. 10 §4, honored here): these are **algebraic
witnesses**. None of them is promoted to a semantic hardness claim;
the bridge is a research obligation, not an identification.

All results verified; axiom audit at end of file.
-/

namespace VDIS.MindGames

open VDIS.Algebra.CD
open VDIS.WeaveShadow

/-!
## Game 1 — The Null Courier

*Posed.* A courier crosses the hardness field. On the way it acquires
one unit of witness (κ⁺_w = 1) and suffers one unit of reconstruction
loss (κ⁻_r = 1). At the gate sits a scalar auditor who computes only
the split norm Q(κ) = (κ⁺_w)² + (κ⁺_g)² − (κ⁻_d)² − (κ⁻_r)².
The auditor stamps the ledger: "Q = 0. Nothing happened."

*Question.* Is the auditor's stamp a certificate?

*Resolution.* No. The courier is on the null cone: the typed state is
nonzero while its scalar shadow vanishes. Worse, the auditor cannot
even distinguish this courier from the one who stayed home.
-/

/-- A split-signature coupling section: two productive directions
(witness acquisition, enrichment), two destructive (distortion,
reconstruction loss). Integer-valued so every question is decidable. -/
structure Coupling where
  /-- witness acquisition (productive) -/
  w : ℤ
  /-- geometric/relational enrichment (productive) -/
  g : ℤ
  /-- distortion / absorptive capture (destructive) -/
  d : ℤ
  /-- reconstruction loss (destructive) -/
  r : ℤ
deriving DecidableEq, Repr

/-- The split quadratic form `Q(κ) = w² + g² − d² − r²`
(signature (2,2)). -/
def Q (κ : Coupling) : ℤ := κ.w ^ 2 + κ.g ^ 2 - κ.d ^ 2 - κ.r ^ 2

/-- The idle courier. -/
def idle : Coupling := ⟨0, 0, 0, 0⟩

/-- The null courier: real acquisition, real loss, silent shadow. -/
def nullCourier : Coupling := ⟨1, 0, 0, 1⟩

/-- **Null cancellation with nontrivial state** (theorem-seed
instantiated): the null courier sits on the null cone yet its typed
state is nonzero. -/
theorem null_cone_hides_activity :
    Q nullCourier = 0 ∧ nullCourier ≠ idle := by
  constructor
  · decide
  · decide

/-- **Scalar non-certification** (Prop. of ch. 8 instantiated): the
scalar shadow of the null courier equals that of the idle courier while
the typed states differ. `Q` is a diagnostic projection, not a
certificate. -/
theorem scalar_shadow_not_certificate :
    Q nullCourier = Q idle ∧ nullCourier ≠ idle := by
  constructor
  · decide
  · decide

/-- Packaging into the weave layer: judging couriers by their scalar
shadow is a `ReturnComparison`; under it the loop "travel and return
with damage" closes, while the relational comparison records the
defect. -/
def scalarCmp : ReturnComparison Coupling := ⟨fun a b => Q a = Q b⟩

/-- The loop that sends the idle courier through the field and back as
the null courier (and fixes everything else — one loop, one lesson). -/
def fieldRoundTrip : TransportLoop Coupling :=
  ⟨fun κ => if κ = idle then nullCourier else κ⟩

/-- Under the scalar comparison the round trip closes at `idle`:
the auditor waves the courier through. -/
theorem scalar_closure_at_idle :
    ¬ StructuredReturnDefect scalarCmp fieldRoundTrip idle :=
  fun h => h (by decide : Q (fieldRoundTrip.transport idle) = Q idle)

/-- Under the relational comparison the same round trip is defective at
`idle`: the damage is real, the stamp was blind. -/
theorem relational_defect_at_idle :
    StructuredReturnDefect (eqCmp Coupling) fieldRoundTrip idle :=
  fun h =>
    (by decide : fieldRoundTrip.transport idle ≠ idle) h

/-!
## Game 2 — The Two Couriers

*Posed.* Two couriers carry the same two quaternionic transports
`i` and `j` around the block, in opposite orders. At the gate the
auditor measures magnitude: both return with norm 1. The auditor
stamps: "identical returns."

*Question.* Did the same object return?

*Resolution.* No. `i·j = k` and `j·i = −k` in the repository's own
level-2 kernel. The verdict (norm) agrees; the route is written into
the sign. Order holonomy is algebraically real: braid crossing has
content, exactly as the Θ-braid chapter demands.
-/

/-- Quaternion basis vector `i`. -/
def qi : Fin 4 → ℝ := fun k => if k.val = 1 then 1 else 0

/-- Quaternion basis vector `j`. -/
def qj : Fin 4 → ℝ := fun k => if k.val = 2 then 1 else 0

/-- Quaternion basis vector `k`. -/
def qk : Fin 4 → ℝ := fun k => if k.val = 3 then 1 else 0

/-- `i·j = k` in the level-2 kernel. -/
theorem ij_eq_k : mulQuat qi qj = qk := by
  funext i
  fin_cases i <;> norm_num [mulQuat, qi, qj, qk]

/-- `j·i = −k` in the level-2 kernel. -/
theorem ji_eq_negk : mulQuat qj qi = -qk := by
  funext i
  fin_cases i <;> norm_num [mulQuat, qi, qj, qk]

/-- The two returns are distinct objects. -/
theorem order_holonomy : mulQuat qi qj ≠ mulQuat qj qi := by
  rw [ij_eq_k, ji_eq_negk]
  intro h
  have h3 := congrFun h 3
  norm_num [qk] at h3

/-- Yet the endpoint-level verdict (norm) agrees: **visible verdict
agreement without route agreement**, in the repository's own kernel. -/
theorem verdict_agreement_without_route_agreement :
    normByLevel 2 (mulQuat qi qj) = normByLevel 2 (mulQuat qj qi) ∧
      mulQuat qi qj ≠ mulQuat qj qi := by
  refine ⟨?_, order_holonomy⟩
  rw [ij_eq_k, ji_eq_negk]
  norm_num [normByLevel, qk]

/-!
## Game 3 — The Bracket Amnesiac

*Posed.* A courier carries three octonionic transports `e₁, e₂, e₄`.
An archivist records which operators were used — the multiset, the
order — but forgets the association tree, reasoning that "composition
is composition." A reconstructor is later asked to un-generate the
result from the archive.

*Question.* Does the archive determine the object?

*Resolution.* No. In the repository's own level-3 kernel,
`(e₁·e₂)·e₄ = −e₇` while `e₁·(e₂·e₄) = +e₇`. Same operators, same
order, opposite objects. The parenthesization is load-bearing: an
un-gen-weave that recovers the endpoint but not the association tree
has not recovered the same object. `Ω_assoc` is not decoration.
-/

/-- Octonion basis vector `e₁`. -/
def E1 : Fin 8 → ℝ := fun i => if i.val = 1 then 1 else 0

/-- Octonion basis vector `e₂`. -/
def E2 : Fin 8 → ℝ := fun i => if i.val = 2 then 1 else 0

/-- Octonion basis vector `e₄`. -/
def E4 : Fin 8 → ℝ := fun i => if i.val = 4 then 1 else 0

/-- Octonion basis vector `e₇`. -/
def E7 : Fin 8 → ℝ := fun i => if i.val = 7 then 1 else 0

/-- Left association: `(e₁·e₂)·e₄ = −e₇`. -/
theorem left_assoc_value :
    mulOct (mulOct E1 E2) E4 = -E7 := by
  funext i
  fin_cases i <;> norm_num [mulOct, mulQuat, E1, E2, E4, E7]

/-- Right association: `e₁·(e₂·e₄) = +e₇`. -/
theorem right_assoc_value :
    mulOct E1 (mulOct E2 E4) = E7 := by
  funext i
  fin_cases i <;> norm_num [mulOct, mulQuat, E1, E2, E4, E7]

/-- **Association holonomy is real**: the bracket amnesiac's archive
(operators and order, no tree) does not determine the object. -/
theorem association_holonomy :
    mulOct (mulOct E1 E2) E4 ≠ mulOct E1 (mulOct E2 E4) := by
  rw [left_assoc_value, right_assoc_value]
  intro h
  have h7 := congrFun h 7
  norm_num [E7] at h7

/-!
## Boundary and next games (posed, not implemented — pre-registration
required before mechanizing)

* **Game 4 — The Prime Stowaway.** A residue invisible at resolution
  `n = 2` but present at `n = 4` in a compatible tower: mechanize a
  profinite shadow where shallow non-detection is not loss
  (`ℤ/2 ← ℤ/4` with `h₂ = 0`, `h₄ = 2`). Anchor: ch. 9 prime towers.
* **Game 5 — The Honest Forger.** Two distinct gluing certificates
  over the same cover producing the same global section: sectionability
  holonomy at fabric level. Anchor: ch. 12 membranes.
* **Game 6 — The Adiabatic Tortoise.** A discrete two-sector system
  where slow deformation tracks sectors and a fast schedule mixes them:
  finite butterfly flap with computable gap. Anchor: ch. 10.

Per the thesis's no-semantic-promotion warning: none of the games
above, present or future, asserts consequences for undecidability.
-/

end VDIS.MindGames

#print axioms VDIS.MindGames.null_cone_hides_activity
#print axioms VDIS.MindGames.scalar_shadow_not_certificate
#print axioms VDIS.MindGames.scalar_closure_at_idle
#print axioms VDIS.MindGames.relational_defect_at_idle
#print axioms VDIS.MindGames.order_holonomy
#print axioms VDIS.MindGames.verdict_agreement_without_route_agreement
#print axioms VDIS.MindGames.association_holonomy
