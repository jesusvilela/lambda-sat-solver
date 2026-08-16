# RE-AUDIT — HardnessHolonomy.lean (2026-07-20, post-update)

**Auditor:** Claude (composer), MacBook Air M1
**Method:** re-read from disk after operator update; trust no prior audit (σ₃).
**File:** 1888 lines, 75 KB, modified 2026-07-18 (was ~40 KB on 2026-07-17).
**Prior audit:** `AUDIT_HardnessHolonomy.md` (2026-07-17).

## Verdict shift

The update is a **real improvement on the honesty axis** and a **partial fix on the
compile axis**, but the **mathematical core remains vacuous** — and one former `sorry`
was closed by *leaning into* that vacuity rather than removing it.

---

## What was FIXED (σ₄ — credit where due)

| Prior finding | Status now | Evidence |
|---|---|---|
| **A. λ₃ wrapper-overclaim** (docstring claimed "No sorry/admit/axiom" while 4 sorries present) | **FIXED** | Docstring now reads: *"Three `sorry`s in convergence proofs (lines ~1057,1058,1080) are load-bearing and documented inline."* The claim now matches — and in fact **understates** — the body. |
| **The 4 sorries themselves** | **CLOSED** | `grep '^\s*sorry'` → **zero** load-bearing sorries. Only two "sorry" strings remain: the docstring note and a `-- No sorry is used` comment. `admit`/`axiom`: none. |
| **B9 duplicated header docstring** | **FIXED** | Header appears once. |
| Theorem/def counts | 15 theorems, 30 defs, 15 structures | file is substantially larger and more built-out |

The docstring correction is exactly repair **F1** from the prior audit. The sorry closures
go beyond F1. This is genuine progress and removes the most serious integrity problem.

---

## What PERSISTS (still compile-blocking or vacuous)

### C3 (the mathematical crux) — the correspondence relation is still VACUOUS, and a sorry was closed by exploiting it

`SplitSignatureCorrespondence` (line 1669):
```lean
def SplitSignatureCorrespondence (inv₁ inv₂ : SplitSignatureInvariant) : Prop :=
  (inv₁.κ₁⁺ * inv₂.κ₁⁺ ≥ 0.0 ∧ inv₁.κ₁⁻ * inv₂.κ₁⁻ ≥ 0.0) ∨
  (inv₁.κ₂⁺ * inv₂.κ₂⁺ ≥ 0.0 ∧ inv₁.κ₂⁻ * inv₂.κ₂⁻ ≥ 0.0)
```
All interpretation maps emit only `0.0` or `1.0`, so every product is `≥ 0` **always**.
The relation holds for **every** pair of invariants. It certifies nothing.

The former sorry in `protensor_sectionability_convergence` (line 990) was closed like this:
```lean
  left
  -- Both carriers have κ₁⁺ = κ₁⁻ = 0.0 ... So κ₁⁺*κ₁⁺ = 0.0 ≥ 0.0
  -- The left branch holds trivially regardless of path₁ ≠ path₂
```
The proof **succeeds precisely because the relation is empty** — `0.0 ≥ 0.0`. The comment
states it outright: *"holds trivially regardless of path₁ ≠ path₂"*. The protensor carrier's
actual content (non-reconstructibility, `path₁ ≠ path₂`) is **irrelevant to the proof**.

> This is a valid Lean proof of a statement with no content. It is no longer a `sorry`,
> but it is not evidence of convergence either. The theorem proves `0 ≥ 0`, dressed in
> carrier types. **`diagonal_hypercomplex_split_signature_correspondence` (1683) takes no
> defect hypotheses at all** and still "proves" correspondence — confirming vacuity.

This is the decisive point: **closing the sorries did not make the diamond real.** It made
the emptiness provable. The honest status is the same as before on the math axis — the
convergence is not yet substantive — even though the sorries are gone.

### C1 — `Classical.em` inside `if` still present (10 sites, 1556–1643)
```lean
let κ₁⁺ := if Classical.em (h.semanticIdentityDefect) then 1.0 else 0.0
```
`Classical.em p : p ∨ ¬p` is a **proof term**, not a decidable proposition. `if _ then _ else _`
needs a `Decidable` condition or a `Prop` with `Classical.propDecidable`. As written the
`if` branches on an (always-inhabited) `Or` proof, so even if it typechecks under
`open Classical`, **κ is the constant `1.0`** — the map does not depend on the defect.
The docstring says *"branches on whether the defect is nontrivial"*; the code does not.
(There is no `open Classical` in the file — only `open Real` at line 75 — so whether this
even elaborates is doubtful.)

### B8 — namespace still not opened
`grep '^namespace'` → **0**. The file ends `end VDIS.HardnessHolonomy` (line 1888) but never
opens that namespace. This alone fails `lake build`.

### B5 — `Bool` fields still assigned `Prop` (`True`)
`ComplexityDiamond.mk` (1161–1167) and `SplitSignatureDiamond.mk` (1802–1804) assign
`multipleCarriers := True`, `convergence := True`, etc., to fields declared `: Bool`.
`True : Prop ≠ Bool`. Type error (should be `true`).

### B7 — unbound variable in `fiveCarrier`
`SplitSignatureDiamond.fiveCarrier` binds `h_sem : SemanticHolonomy R V_ver (R.encode …)`
where `R : SemanticRepresentation M A` — but `M` is never bound in the signature.

### C2 — `nlinarith [structure values]` still present
`diagonal_hypercomplex_split_signature_correspondence` (1683):
```lean
· nlinarith [h_diag.interpretSplitSignature, h_alg.interpretSplitSignature]
```
passes `SplitSignatureInvariant` **values** as hints to an arithmetic tactic. The goal
(`x*x ≥ 0`) is true via `mul_self_nonneg`, so `nlinarith` may close it *ignoring* the bad
hints — but the hint list is meaningless and the theorem is (again) vacuous.

---

## Net assessment

| Axis | 2026-07-17 | 2026-07-20 | Direction |
|---|---|---|---|
| Honesty (docstring vs body) | false sorry-free claim (λ₃) | accurate, even understated | **FIXED** |
| Load-bearing sorries | 4 | 0 | **FIXED** (but see below) |
| Compiles under `lake build` | no | **still no** (B5, B7, B8, C1) | unchanged |
| Correspondence is substantive | no (C3 vacuous) | **still no** — sorry closed *via* the vacuity | unchanged |
| Design quality (σ₁) | good | good | unchanged |

**The update fixed the integrity problem and removed the sorries, but did not make the
mathematics real.** The three convergence sorries were discharged by taking the `left`
disjunct of a relation that is true for all inputs (`0 ≥ 0`). So the file now honestly
*claims less* (docstring) while the proofs *contain the same emptiness* — just formalized
instead of `sorry`'d. That is a subtle regression risk: a future reader sees "0 sorries"
and may over-trust. The `MEMORY_INDEX` "lake build exit 0" is **still not achievable**
(B5/B7/B8/C1 remain), so any such claim is still stale (λ₁).

---

## Priority repairs (candidates, not directives — λ₅)

The ranking has changed because the trivial fixes are done. The math is now the whole game.

1. **B8 namespace** (1 line): add `namespace VDIS.HardnessHolonomy` after the imports/`open`.
   Without it nothing compiles. Cheapest remaining blocker.
2. **B5 Bool/Prop** (7+3 lines): `True` → `true` in the two `.mk`s, or change fields to `Prop`.
3. **C1 Classical.em** (10 sites): replace `if Classical.em p then a else b` with a genuine
   decidable branch. Cleanest fix: give each witness a `Bool` flag field (e.g.
   `semanticIdentityDefectFlag : Bool` alongside the `Prop` proof) and branch on the flag,
   so the map actually varies with the defect. This is prerequisite to C3.
4. **B7 unbound `M`** (1 line): add `{M : MachineSemantics}` to `fiveCarrier`.
5. **C3 — make the correspondence non-vacuous** (the real theorem, unchanged from prior audit).
   A relation satisfied by `0 ≥ 0` proves nothing. Options, strongest first:
   - **strict firing**: require `κ₁⁺ > 0 ∧ κ₂⁺' > 0` (both carriers *actually* detected a
     defect), so the theorem needs the defect hypotheses and cannot be proved vacuously;
   - **active-sector equality**: require `inv₁.activeSectors = inv₂.activeSectors`;
   - **split-norm agreement**: `inv₁.splitNorm = inv₂.splitNorm`, making the null cone
     (`splitNorm = 0`) a meaningful frontier.
   Any of these forces the convergence proofs to *use* the witness content that
   `path₁ ≠ path₂` / `shiftNontrivial` provide — which is the entire point of the file.

---

## Standing (σ₂)

- **Integrity: restored.** The overclaim is gone; the docstring is honest.
- **Sorries: closed** — but three were closed by proving a vacuous statement, so the
  *mathematical* gap they marked is still open, now hidden inside valid-but-empty proofs.
- **Build: still fails** (B5, B7, B8, C1). `lake build exit 0` remains unachievable.
- **Math core (C3): unchanged** — the complexity diamond certifies nothing until the
  correspondence relation is made non-vacuous.
- **Design: still good** and worth carrying forward.
- **Arc coupling:** still forbidden without a matched-null test (R189: SAT backbone
  holonomy = 0.000; separate prime ray).

`[R] > 0`. The file went from *dishonest and broken* to *honest and broken*. That is real
progress — honest-and-broken is the right precondition for making it honest-and-true. The
next decisive move is C3: a correspondence relation that `0 ≥ 0` cannot satisfy.
