/-!
# Weave Shadow: Comparison-Parametric Return Defect

Mechanized finite instantiation of the theorem-seed
"Visible closure versus relational closure"
(*The Weave Never Ends*, Definitive Edition r2, ch. 2).

The existing `VDIS.HardnessHolonomy.HolonomyWitness` detects strict
endpoint inequality (`returned ≠ x`). The thesis's central cases are
stronger: the endpoint returns while the *relation* that made it
meaningful does not. This file adds the comparison-parametric layer:

* `ReturnComparison X`  — a declared equivalence for judging return;
* `StructuredReturnDefect C L x` — defect relative to a comparison;
* `ComparativeHolonomyWitness` — witness-bearing record of such a defect;
* a two-Boolean carrier `WCarrier` (endpoint × witness) with a
  witness-flipping loop that is **closed under the endpoint comparison
  and defective under the relational comparison** — the smallest model
  of visible closure without relational closure.

Claim tier: upgrades the seed from Defined to Tested at the smallest
scale. The universal statement (per declared carrier and comparison)
remains open.

## Import status (disclosed, per σ₃)

This file is deliberately import-free. As of 2026-07-15 the chain
`HardnessHolonomy → … → Algebra.CD` does not build under toolchain
v4.32.0-rc1 (`interval_cases` failures at `CD.lean:601, 612`), so
`TransportLoop` and `ReturnDefect` are restated here with signatures
byte-compatible with `VDIS.HardnessHolonomy`. Merge path once CD.lean
is repaired: delete the two local definitions, add
`import LambdaSatSolver.VDIS.HardnessHolonomy`, and
`open VDIS.HardnessHolonomy`. Nothing else changes.

Verified with core Lean only: no Mathlib, no axioms (see
`#print axioms` at end of file).
-/

namespace VDIS.WeaveShadow

universe u

/-- Local restatement of `VDIS.HardnessHolonomy.TransportLoop`
(see Import status above). -/
structure TransportLoop (X : Type u) where
  /-- The state transformation for this loop. -/
  transport : X → X

/-- Local restatement of `VDIS.HardnessHolonomy.ReturnDefect`. -/
def ReturnDefect {X : Type u} (L : TransportLoop X) (x : X) : Prop :=
  L.transport x ≠ x

/-- A declared return comparison: the equivalence a chart, task, or
verifier requires for judging that transport has faithfully returned. -/
structure ReturnComparison (X : Type u) where
  /-- The comparison relation. Not assumed to be `Eq`. -/
  Equivalent : X → X → Prop

/-- Return defect relative to a declared comparison: transport fails to
return `x` up to `C`. -/
def StructuredReturnDefect {X : Type u} (C : ReturnComparison X)
    (L : TransportLoop X) (x : X) : Prop :=
  ¬ C.Equivalent (L.transport x) x

/-- A witness-bearing record of a comparison-relative return defect:
the returned object, evidence it is the actual transport result, and
evidence it fails the declared comparison. -/
structure ComparativeHolonomyWitness {X : Type u} (C : ReturnComparison X)
    (L : TransportLoop X) (x : X) where
  /-- The actual result of applying the transport. -/
  returned : X
  /-- Proof that the transport returned this value. -/
  returnsBy : returned = L.transport x
  /-- Proof that the returned value fails the declared comparison. -/
  differs : ¬ C.Equivalent returned x

/-- A comparative witness yields the comparison-relative defect. -/
theorem ComparativeHolonomyWitness.toDefect {X : Type u}
    {C : ReturnComparison X} {L : TransportLoop X} {x : X}
    (w : ComparativeHolonomyWitness C L x) :
    StructuredReturnDefect C L x :=
  fun h => w.differs (w.returnsBy ▸ h)

/-- Strict equality as a return comparison. -/
def eqCmp (X : Type u) : ReturnComparison X := ⟨Eq⟩

/-- Under the strict-equality comparison, the comparative defect is
definitionally the endpoint-level `ReturnDefect`. The new layer
generalizes and does not fork the kernel. -/
theorem comparative_generalizes_return_defect {X : Type u}
    (L : TransportLoop X) (x : X) :
    StructuredReturnDefect (eqCmp X) L x ↔ ReturnDefect L x :=
  Iff.rfl

/-! ## The smallest carrier: endpoint × witness -/

/-- Minimal typed fiber: a visible endpoint and one witness bit. -/
structure WCarrier where
  /-- The visible endpoint of transport. -/
  endpoint : Bool
  /-- The witness that made the endpoint meaningful. -/
  witness : Bool
deriving DecidableEq, Repr

/-- The loop that returns the endpoint but corrupts the witness:
visible closure with relational damage. -/
def witnessFlip : TransportLoop WCarrier :=
  ⟨fun s => ⟨s.endpoint, !s.witness⟩⟩

/-- Endpoint-only comparison: what a scalar or verdict-level observer
checks. -/
def endpointCmp : ReturnComparison WCarrier :=
  ⟨fun a b => a.endpoint = b.endpoint⟩

/-- Relational comparison: endpoint and witness must both return. -/
def relationalCmp : ReturnComparison WCarrier :=
  ⟨Eq⟩

/-- Under the endpoint comparison the loop closes at every point:
the visible verdict survives. -/
theorem visible_closure (x : WCarrier) :
    ¬ StructuredReturnDefect endpointCmp witnessFlip x :=
  fun h => h rfl

/-- Under the relational comparison the loop is defective at every
point: the witness never returns. -/
theorem relational_defect (x : WCarrier) :
    StructuredReturnDefect relationalCmp witnessFlip x := by
  intro h
  have hw : (!x.witness) = x.witness := congrArg WCarrier.witness h
  cases hx : x.witness
  · rw [hx] at hw; exact Bool.noConfusion hw
  · rw [hx] at hw; exact Bool.noConfusion hw

/-- Explicit witness record at a sample point. -/
def sampleWitness :
    ComparativeHolonomyWitness relationalCmp witnessFlip ⟨true, true⟩ :=
  ⟨⟨true, false⟩, rfl,
    fun h => Bool.noConfusion (congrArg WCarrier.witness h)⟩

/-- **Theorem-seed instantiated** (ch. 2, *Visible closure versus
relational closure*): there exists a carrier, a transport loop, and two
declared comparisons such that the loop is closed under the visible
comparison and defective under the relational one. -/
theorem visible_closure_without_relational_closure :
    ∃ (X : Type) (L : TransportLoop X)
      (Cvis Crel : ReturnComparison X) (x : X),
      (¬ StructuredReturnDefect Cvis L x) ∧
        StructuredReturnDefect Crel L x :=
  ⟨WCarrier, witnessFlip, endpointCmp, relationalCmp, ⟨true, true⟩,
    visible_closure _, relational_defect _⟩

end VDIS.WeaveShadow

#print axioms VDIS.WeaveShadow.visible_closure_without_relational_closure
#print axioms VDIS.WeaveShadow.relational_defect
#print axioms VDIS.WeaveShadow.visible_closure
