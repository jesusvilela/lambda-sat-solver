# AUDIT — HardnessHolonomy.lean (σ₃/λ₃/λ₄ artifact audit)

**Auditor:** Claude (composer), on MacBook Air M1, 2026-07-17
**Method:** direct artifact read (λ₄ — no trust in self-summary or MEMORY_INDEX)
**Verdict:** **aspirational architecture, not verified mathematics.** The file's own
docstring claims sorry-freedom that the body contradicts, and the file cannot compile
in its present state. `HardnessHolonomy` **is** imported by `LambdaSatSolver.lean`
(last line), so the `MEMORY_INDEX.md` claim `lake build: exit 0` is **stale**.

> This audit is not a rejection of the design. The design is good and matches the
> σ-discipline. The audit is about the gap between the claim and the artifact.

---

## A. The headline defect (λ₃ — wrapper-overclaim)

The file docstring states, twice (the whole header is duplicated verbatim):

> "No `sorry`, `admit`, or `axiom` in this file. All four legacy placeholders in the
> repository (CD.lean:363,366; TuringHalting_Master.lean:362,393) remain explicitly
> isolated."

**This is false.** The body contains **four `sorry`s**:

| # | Location | Context |
|---|----------|---------|
| 1 | `protensor_sectionability_convergence` | inside `have h_prot_paths : h_prot.path₁ ≠ h_prot.path₂` — the comment reasons itself into a dead end: *"there's no field saying path₁ ≠ path₂ — it's implicit"* |
| 2 | `protensor_sectionability_convergence` | the theorem's final goal |
| 3 | `protensor_sectionability_convergence_transport` | `-- Same proof as ... sorry` |
| 4 | (same theorem, trailing) | — |

**These are load-bearing.** `ComplexityDiamond.protensorSectionability` is *constructed
from* `protensor_sectionability_convergence`. That diamond therefore rests on a `sorry`.

This is failure-mode #1 from `sigma_discipline_long_arc_formalization.md`: a summary
declaring PROVEN while the proof body carries load-bearing sorries.

---

## B. Compile-blocking defects (would fail `lake build` independent of sorries)

| # | Defect | Detail |
|---|--------|--------|
| B1 | **Use-before-definition: `PrimeSector`** | `HolonomyCarrier` (§9) has `activeSectors : List PrimeSector`, but `inductive PrimeSector` is declared in §15. Lean is order-sensitive. |
| B2 | **Use-before-definition: `SplitSignatureInvariant`** | Used by `HolonomyCarrier.toSplitSignatureInvariant` and the §11 convergence theorems; defined in §15. |
| B3 | **Use-before-definition: `SplitSignatureCorrespondence`** | Used in §11 theorem statements; defined in §16. |
| B4 | **Duplicate `splitNorm`** | `SplitSignatureCoupling` declares `splitNorm` as a field with a default *and* as a standalone `def` on the same namespace → name collision. |
| B5 | **`Bool` field assigned `Prop`** | `ComplexityDiamond` fields are `Bool`; `ComplexityDiamond.mk` assigns `True` (a `Prop`). Same in `SplitSignatureDiamond.mk` (`stableUnderTransport := True` etc.). Type error. |
| B6 | **`default` with no `Inhabited`** | `AdmissibleCouplingWindow.holonomyNontrivial` uses `... ≠ default` on `HolonomyWitness`, which has no `Inhabited` instance. |
| B7 | **Unbound variables** | `five_carrier_split_signature_convergence` references `R` and `V` (and `M`) in `h_sem : SemanticHolonomy R V ...` without binding them. Same class of error in `SplitSignatureDiamond.fiveCarrier` (`M` unbound). |
| B8 | **Namespace mismatch** | File ends `end VDIS.HardnessHolonomy` but never opens that namespace. |
| B9 | **Duplicated header** | The entire module docstring appears twice back-to-back. |

---

## C. Non-proof proofs (would fail even if B were fixed)

### C1 — `Classical.em` misuse makes the interpretation maps constant

Every `interpretSplitSignature` uses:

```lean
let κ₁⁺ := if Classical.em (h.semanticIdentityDefect) then 1.0 else 0.0
```

`Classical.em p : p ∨ ¬p` is a **proof term**, always inhabited. This is not a
decidable branch on the defect. The docstring says *"branches on whether the semantic
identity defect is nontrivial"* — **the code does not do this.** It is either a type
error (no `Decidable` instance for the `Or`) or, if coerced, a constant.

Same pattern in `DiagonalHolonomy.interpret`, `AlgebraicHolonomy.interpret`,
`SemanticHolonomy.interpret`, `SectionabilityHolonomy.interpret`
(`if h.semanticIdentityDefect then ...` — branching on a **`Prop` field**, not a `Bool`).

### C2 — `nlinarith` given structure values, not hypotheses

```lean
nlinarith [h_diag.interpretSplitSignature, h_alg.interpretSplitSignature]
```

These are `SplitSignatureInvariant` *values*, not arithmetic facts. `nlinarith` cannot
use them. The goal (`κ₁⁺ * κ₁⁺ ≥ 0`) is in fact trivially true for reals
(`mul_self_nonneg`), so the *statement* is provable — but not by this tactic call, and
the theorem as written proves something weaker than the docstring claims.

### C3 — `SplitSignatureCorrespondence` is nearly vacuous

```lean
def SplitSignatureCorrespondence (inv₁ inv₂) : Prop :=
  (inv₁.κ₁⁺ * inv₂.κ₁⁺ ≥ 0 ∧ inv₁.κ₁⁻ * inv₂.κ₁⁻ ≥ 0) ∨ (…κ₂…)
```

Since all interpretation maps emit only `0.0` or `1.0`, every product is `≥ 0`
**always**. The correspondence relation is satisfied by *any* two invariants the file
can produce. It therefore certifies nothing: **the diamond condition as coded is
trivially true.** This is the mathematical heart of the problem — the convergence
theorems are true but empty.

### C4 — `ComplexityDiamond.mk` ignores its own evidence

It takes `h_convergence`, `h_stable`, `h_multipleCarriers` and then returns a record
with every field set to a constant, using none of them. The certificate is
independent of the evidence supplied.

---

## D. What is genuinely good (σ₁ — recognition)

The **design** is sound and worth preserving:

- **Five typed carriers** (diagonal / protensor / hypercomplex / sectionability /
  semantic) with carrier-specific witness types that do **not** collapse to a scalar.
- **"Interpretation, not equality"** — refusing to assert two holonomies equal before
  an explicit interpretation map. This is exactly the right epistemics.
- **`HolonomyWitness` / `ReturnDefect`** (§1–2) are clean, generic, assumption-free, and
  `witness_implies_return_defect` is a real (if trivial) proof.
- **`AlgebraicHolonomy.transport_not_closed`** is **honest**: it explicitly takes
  `h_transport_not_closed` as a premise and documents *why* it is not derivable from the
  associator alone. This is the discipline working.
- **The (2,2) split-signature lift** (§15) is a genuinely interesting idea: replacing the
  scalar volcano κ with a four-sector split-signature manifold, with a null cone where
  acquisition and loss cancel *metrically but not structurally*.
- **`diagonal_return_path_not_closed`** honestly marks its own gap in the comment
  (`the premise h_neg is intentionally weak to document the gap`), even though it then
  proves `True`.

---

## E. Relation to our arc (σ₂ — evidence class)

The five-carrier holonomy architecture is a **different object** from the arc35
SAT-medium holonomy that R180/R189 demoted. They must not be conflated:

| | arc35 holonomy (R179–R189) | HardnessHolonomy.lean |
| --- | --- | --- |
| object | backbone var-set transported around an α-anneal loop | typed return-defect across 5 representational carriers |
| status | **DEMOTED** (R180 degree-null z=0.00), then **HARDENED** (R189: residual holonomy = 0.000 on cadical — backbone is loop-*invariant*) | unproven architecture |
| instrument | DPLL + cadical153, matched-degree null | Lean types, no empirical null |

**The arc's own finding is a live constraint on this file:** on the hardened instrument
the SAT backbone has holonomy **exactly zero** — it returns to itself perfectly, while
the degree-matched null wobbles (0.19–0.48). If "hardness = structured failure of
return" is to apply to the SAT medium, it must reckon with the fact that our *measured*
return defect there is **null**, and it is the *random control* that fails to return.

That does not refute the file's thesis (its carriers are representational, not the SAT
backbone), but it forbids the lift `arc35 holonomy → hardness-holonomy evidence`.
Per the 360-prime shield: separate ray, no welding without a matched-null test.

---

## F. Minimal repair path (candidates, not directives — λ₅)

Ordered by cost. Each is independently useful.

1. **Fix the docstring** (5 min, σ₄). Replace the false sorry-free claim with the honest
   status: *"4 load-bearing sorries in `protensor_sectionability_convergence` and its
   transport variant; this file is architecture-in-progress."* Removes the λ₃ violation
   immediately, independent of any math.
2. **Reorder the file** (30 min). Move §15's `PrimeSector`, `SplitSignatureInvariant`,
   and §16's `SplitSignatureCorrespondence` **above** §9. Fixes B1–B3.
3. **Fix the type errors** (30 min). `Bool` vs `Prop` (B5), duplicate `splitNorm` (B4),
   `default` (B6), unbound `R`/`V`/`M` (B7), namespace (B8), duplicate header (B9).
4. **Make the interpretation maps actually branch** (2 h, the real work). Replace
   `if Classical.em p` with `Decidable`-backed branching, or — cleaner — make the witness
   fields carry `Bool` flags alongside their `Prop` proofs so the map can compute.
5. **Make `SplitSignatureCorrespondence` non-vacuous** (the mathematical crux). A relation
   satisfied by every pair certifies nothing. Candidates:
   - require **matching active-sector sets**: `inv₁.activeSectors = inv₂.activeSectors`;
   - require **strict positivity**: `κ₁⁺ * κ₁⁺ > 0` (i.e. both carriers actually fired);
   - require **split-norm agreement**: `inv₁.splitNorm = inv₂.splitNorm`, which makes the
     null cone (`splitNorm = 0`) a *meaningful* frontier rather than decoration.
6. **Close or excise the protensor sorries** (unknown). The comment identifies the real
   blocker: `DiamondComparison` has no field asserting `path₁ ≠ path₂`. Either add that
   field to `ProtensorHalting` (making non-reconstructibility part of the witness, which
   is arguably where it belongs), or state the theorem with `path₁ ≠ path₂` as an explicit
   premise — exactly the honest pattern `AlgebraicHolonomy.transport_not_closed` already uses.

---

## G. Standing

- **Design:** worth keeping. Five typed carriers, interpretation-not-equality, (2,2) lift.
- **Artifact:** does not compile; 4 load-bearing sorries; the central correspondence
  relation is vacuous; the diamond constructor ignores its evidence.
- **Claim vs artifact:** the docstring's sorry-free claim is **false** (λ₃).
- **MEMORY_INDEX `lake build: exit 0`:** **stale** (λ₁) — `HardnessHolonomy` is in the
  root import, so a clean build is not possible in this state.
- **Arc coupling:** forbidden without a matched-null test (separate prime ray).

`[R] > 0`. The architecture is a hypothesis with a good shape and no verification yet.
The fastest honest move is F1 — make the file say what it is.
