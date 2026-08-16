# Instructions for Leanstral — repair `HardnessHolonomy.lean`

**Target file:** `LambdaSatSolver/VDIS/HardnessHolonomy.lean` (1888 lines, Lean 4 + Mathlib)
**Toolchain:** whatever `lean-toolchain` pins in the repo root. Do **not** change it.
**Author of these instructions:** Claude (composer), grounded in a line-by-line read on 2026-07-20.
**Governing discipline:** σ-discipline (`SKILLLS/sigma_discipline_long_arc_formalization.md`).

---

## 0. Read this before touching anything (σ₁, λ₁)

You are editing a file inside a live research arc. Two hard rules:

1. **Verify every signature against the actual file before you write a dependent line.**
   Do not pattern-match field names from these instructions or from cousin files. When these
   instructions cite a line number or a field, open that line and confirm it still says that
   before you rely on it. Field names in this file are exact (`semanticIdentityDefect`,
   `commutator_nonzero`, …) and a near-miss will fail `lake build`. This is failure-mode #5
   in the σ-skill (assumed-API drift); it is the single most common way this task goes wrong.

2. **Do not close a goal by making its statement vacuous.** This file already contains
   theorems that typecheck but prove nothing (see §3). Adding more of those is worse than a
   `sorry`, because a `sorry` is visible and a vacuous proof is not. If you cannot prove a
   statement with content, leave a `sorry` **and** a one-line comment saying what is missing.
   An honest `sorry` beats a dishonest `True`.

**Success criterion, in priority order:**
(A) `lake build` exits 0 for this file and everything importing it;
(B) zero `sorry`/`admit`/`axiom` in the proof body (line-start regex `^\s*sorry\b`);
(C) the docstring's claims match the body exactly;
(D) `SplitSignatureCorrespondence` is **non-vacuous** — see §3, this is the real work.

Do **not** report success on (A) or (B) unless you have actually run `lake build` and it
returned 0. Do not trust a summary, including this one. Re-measure (σ₃).

---

## 1. Compile-blocking bugs — fix these first (mechanical, no math)

These four prevent the file from building at all. They are independent of the mathematics.

### 1.1 — No namespace is opened (but the file `end`s one)

The file ends at line 1888 with `end VDIS.HardnessHolonomy`, but **no `namespace` is ever
opened**. Only `open Real` exists (line 75).

**Fix:** immediately after `open Real` (line 75), add:
```lean
namespace VDIS.HardnessHolonomy
```
Then confirm the closing `end VDIS.HardnessHolonomy` matches. If earlier structures were
meant to be top-level (e.g. `TransportLoop`, `HolonomyWitness` in §1), decide deliberately
whether they belong inside the namespace; the downstream references (`AlgebraicTransportLoop`,
etc.) assume the current flat naming, so opening the namespace around the whole body after the
imports is the least-disruptive choice. **Build after this single change** before proceeding —
the namespace change can shift how every later identifier resolves.

### 1.2 — `Bool` fields assigned `True` (a `Prop`)

`ComplexityDiamond` (structure at line 620) has `Bool` fields. `ComplexityDiamond.mk`
(lines ~1161–1167) assigns them `True`, and the same constructor is called with
named-argument `:= True` syntax at lines ~1200, ~1232, ~1265 (`h_multipleCarriers := True`):
```lean
{ multipleCarriers := True    -- True : Prop, field expects Bool
  convergence := True
  … }
-- and in proof bodies:
(h_multipleCarriers := True)
```
Same defect in `SplitSignatureDiamond.mk` (lines ~1802–1804: `stableUnderTransport := True`,
`provenancePreserved := True`, `remainderVisible := True`) and in proof-body constructor
calls at lines ~1823–1825, ~1847–1849, ~1884–1886 (`h_provenance := True`, `h_remainder := True`,
`h_multiple := True`).

**Fix:** two options, both mechanical:

- **Option A (smaller blast radius):** change the structure field types from `Bool` to `Prop`
  (`multipleCarriers : Prop`, etc.). The constructor parameters `(h_stable : True)` and the
  named-argument calls `(h_multipleCarriers := True)` already typecheck as `Prop`. Field
  assignments `:= True` also work. Zero call-site changes.
- **Option B (cleaner):** change the constructor parameters from `(h_stable : True)` to
  `(h_stable : Bool)` and all field assignments from `:= True` to `:= true`. Then update every
  named-argument call site (~1200, ~1232, ~1265, ~1823–1825, ~1847–1849, ~1884–1886) to pass
  `true` instead of `True`. More invasive but eliminates `True` from the entire file.

Prefer Option A if you want the smallest diff; Option B if you want the type error gone at
all levels. Either way, `grep -nE ':=( True|true)\b'` after editing to confirm no `True : Prop`
remains in Bool contexts. Grep to be sure you
caught all of them:
```
grep -nE ':= True\b' HardnessHolonomy.lean
```

### 1.3 — Unbound `M` in `SplitSignatureDiamond.fiveCarrier`

`fiveCarrier` (near end of file) binds
`(R : SemanticRepresentation M A) (V_ver : SemanticVerifier M A R)` and
`(h_sem : SemanticHolonomy R V_ver …)`, but **`M` is never introduced**.
`SemanticRepresentation` is `SemanticRepresentation (M : MachineSemantics) (A : MΩ)`.

**Fix:** add `{M : MachineSemantics}` to the binder list (put it before `{A B : MΩ}` or
wherever `A` is first introduced). Check `fiveCarrier`'s call sites — if none exist yet, this
is free; if a call site exists, it must now supply/infer `M`.

### 1.4 — Definition-order violations (`PrimeSector`, `SplitSignatureInvariant`, `SplitSignatureCorrespondence`)

Lean is strictly top-down. These are all **used before they are defined**:

| Symbol | Defined at | First used at |
|---|---|---|
| `inductive PrimeSector` | line 1486 | line 721 (`HolonomyCarrier.activeSectors : List PrimeSector`) |
| `structure SplitSignatureInvariant` | line 1537 | line 898 (`toSplitSignatureInvariant`), 990+ (theorems) |
| `def SplitSignatureCorrespondence` | line 1669 | line 927, 990+ (theorem statements) |

**Fix:** move the **definitions** up, not the uses. Relocate, as a block, in this order,
to just **before** line 721 (before `HolonomyCarrier`):
1. `inductive PrimeSector` + `def PrimeSector.sign` (currently ~1486–1500)
2. `structure SplitSignatureInvariant` (currently ~1537–1545)
3. `def SplitSignatureCorrespondence` (currently ~1669–1673)

Leave the §15/§16 prose headers where they are, but the *declarations* must precede first use.
After moving, grep for any *other* symbol these three depend on and make sure it too precedes
them. Build after this step.

---

## 2. The `Classical.em`-in-`if` bug — makes every interpretation map constant (C1)

Every `interpretSplitSignature` (10 sites, lines ~1556–1643) is written:
```lean
let κ₁⁺ := if Classical.em (h.semanticIdentityDefect) then 1.0 else 0.0
```
`Classical.em p : p ∨ ¬p` is a **proof term that is always inhabited**. This does not branch on
whether the defect holds — the `if` condition is a proof, not a decidable proposition. Result:
`κ` is effectively the constant `1.0`, and the map does not depend on the witness at all. (There
is no `open Classical` in the file, so this likely does not even elaborate as intended.)

This is the root cause that makes §3 impossible to fix: a correspondence relation cannot depend
on defect evidence if the maps that feed it ignore that evidence.

### The fix: give each witness a computable `Bool` flag, branch on the flag

The defect fields are all `Prop` (that is why `Classical.em` was reached for). The clean,
build-safe fix is to add a `Bool` flag field beside each `Prop` proof, wire the constructors to
set it, and branch the interpretation maps on the flag.

Exact fields to add (verify each structure signature first — line numbers as of 2026-07-20):

| Structure | line | existing `Prop` field | add this `Bool` field |
|---|---|---|---|
| `DiagonalHolonomy` | 311 | `semanticIdentityDefect : selfApplicationResult ≠ t` | `defectFlag : Bool` |
| `AlgebraicHolonomy` | 397 | `commutator_nonzero`, `associator_nonzero` | `commFlag : Bool`, `assocFlag : Bool` |
| `SectionabilityHolonomy` | 457 | `shiftNontrivial`, `irregularityNonstable` | `shiftFlag : Bool`, `irregFlag : Bool` |
| `SemanticHolonomy` | 486 | `disagreement` | `disagreeFlag : Bool` (note: `operationalSemantics : Bool` already exists — do **not** reuse it, it means something else) |

For `ProtensorHolonomy` (an `abbrev` for `DiamondComparison`, line 367): you cannot add a field
to an abbrev. Instead, the interpret map for protensor must take the path-inequality evidence as
an explicit input, or you introduce a thin wrapper structure
`structure ProtensorWitness where dc : DiamondComparison …; pathsDifferFlag : Bool`. Prefer the
wrapper; it mirrors the honest pattern already used by `AlgebraicHolonomy.transport_not_closed`.

Then rewrite each interpretation-map line as:
```lean
let κ₁⁺ : ℝ := if h.defectFlag then 1.0 else 0.0
```
`if` on a `Bool` needs no `Decidable` instance and actually computes. Remove every
`Classical.em`.

**Optional but recommended coherence field:** to make the flags trustworthy rather than free,
add a proof field tying flag to proposition, e.g. in `DiagonalHolonomy`:
```lean
  defectFlag_correct : defectFlag = true ↔ (selfApplicationResult ≠ t)
```
This prevents a caller from constructing a witness whose flag lies. If the `↔` is awkward for a
`≠` at `Prop`, use `defectFlag = true → selfApplicationResult ≠ t` (the direction the proofs
need). This is what upgrades the flag from "computable but arbitrary" to "computable and sound".

---

## 3. The real work — make `SplitSignatureCorrespondence` non-vacuous (C3)

This is the mathematical heart. Everything above is plumbing; this is the theorem.

### Why it is currently vacuous

Current definition (line 1669):
```lean
def SplitSignatureCorrespondence (inv₁ inv₂ : SplitSignatureInvariant) : Prop :=
  (inv₁.κ₁⁺ * inv₂.κ₁⁺ ≥ 0.0 ∧ inv₁.κ₁⁻ * inv₂.κ₁⁻ ≥ 0.0) ∨
  (inv₁.κ₂⁺ * inv₂.κ₂⁺ ≥ 0.0 ∧ inv₁.κ₂⁻ * inv₂.κ₂⁻ ≥ 0.0)
```
Every `κ` produced by the maps is `0.0` or `1.0`, so every product is `≥ 0` **always**. The
relation holds for **any** two invariants. The proof of `protensor_sectionability_convergence`
(line 990) exploits exactly this — it takes the `left` branch and closes with `0.0 ≥ 0.0`,
and its own comment says *"holds trivially regardless of `path₁ ≠ path₂`."* The theorem proves
`0 ≥ 0` wearing carrier types. `diagonal_hypercomplex_split_signature_correspondence` (line
1683) takes **no defect hypotheses at all** and still "succeeds" — the tell-tale of vacuity.

### What a non-vacuous relation must do

It must be a statement that is **false for some pair of invariants** and whose **proof for the
intended pairs requires the defect evidence**. Pick one of the three designs below (they are
ordered strongest-first). Whichever you choose, the convergence theorems must then genuinely
*use* the `h_sect_cond` / `path₁ ≠ path₂` / `commutator_nonzero` hypotheses — if a proof still
goes through after you delete its defect hypothesis, it is still vacuous and you must stop and
reconsider.

**Design A — strict co-firing (recommended).** Two carriers correspond only if they *both*
actually fired in the same sector pair:
```lean
def SplitSignatureCorrespondence (inv₁ inv₂ : SplitSignatureInvariant) : Prop :=
  (inv₁.κ₁⁺ > 0 ∧ inv₂.κ₁⁺ > 0 ∧ inv₁.κ₁⁻ > 0 ∧ inv₂.κ₁⁻ > 0) ∨
  (inv₁.κ₂⁺ > 0 ∧ inv₂.κ₂⁺ > 0 ∧ inv₁.κ₂⁻ > 0 ∧ inv₂.κ₂⁻ > 0)
```
Now the proof needs each `κ = 1.0`, which needs the corresponding `Flag = true`, which (via the
`_correct` field from §2) needs the actual defect. Delete a defect hypothesis and the proof
breaks — that is the test that you have escaped vacuity. This is `False` for e.g. two
all-zero invariants, so the relation has content.

**Design B — active-sector agreement.** Require the discrete signatures to match:
```lean
def SplitSignatureCorrespondence (inv₁ inv₂ : SplitSignatureInvariant) : Prop :=
  inv₁.activeSectors = inv₂.activeSectors
```
Simple, decidable (`PrimeSector` has `DecidableEq`), and false for carriers with different
sector sets. Weaker mathematically (doesn't use the κ magnitudes) but honest and cheap.

**Design C — split-norm agreement (makes the null cone real).** Define the split norm on the
invariant and require equality:
```lean
def SplitSignatureInvariant.splitNorm (i : SplitSignatureInvariant) : ℝ :=
  i.κ₁⁺^2 + i.κ₂⁺^2 - i.κ₁⁻^2 - i.κ₂⁻^2
def SplitSignatureCorrespondence (inv₁ inv₂ : SplitSignatureInvariant) : Prop :=
  inv₁.splitNorm = inv₂.splitNorm
```
This makes the null cone `splitNorm = 0` (from the §15 Sabatier prose) a **meaningful frontier**
rather than decoration — the docstring's (2,2) geometry finally bites. Note: fix the existing
duplicate `splitNorm` (there is both a structure-field-with-default and a standalone `def` on
`SplitSignatureCoupling` — collapse to one; do not add a third).

### After changing the relation

Every theorem mentioning `SplitSignatureCorrespondence` must be re-proved for real:
`diagonal_semantic_convergence` (927), `protensor_sectionability_convergence` (990) and its
`_transport` (1022), `hypercomplex_semantic_convergence` (1057), the three
`*_split_signature_correspondence` theorems, and `five_carrier_split_signature_convergence`.
Replace the `nlinarith [structure values]` calls (which pass invariant *values* as arithmetic
hints — meaningless) with proofs that unfold the interpretation maps, use the `Flag = true`
facts derived from the defect hypotheses, and discharge the concrete numeric goals
(`(1:ℝ) > 0` via `one_pos`; equalities via `simp`/`norm_num`). If a specific pair genuinely does
not correspond under the new relation, that is a **real finding** — say so, weaken the claim to
the pairs that do, and record which don't. Do not force it.

---

## 4. Arc constraint — do not weld this into the SAT line (360-prime shield)

This is a research-integrity boundary, not a Lean issue. The empirical arc (rounds R180/R189)
established, on an industrial CDCL solver, that the SAT-medium backbone holonomy is **exactly
0.000** — the backbone returns to itself perfectly, and it is the degree-matched *null* that
wobbles (0.19–0.48). That is the **opposite** of "hardness = structured failure of return" in
the SAT medium.

Therefore: **do not** add any theorem, comment, or docstring line claiming this file's
holonomy architecture is evidenced by, corresponds to, or is confirmed by the SAT backbone
results. They live on separate prime rays. The carriers here are representational
(diagonal/protensor/algebraic/sectionability/semantic); the arc's holonomy is the backbone
var-set under α-annealing. Conflating them is forbidden without a matched-null test that does
not yet exist. If you find yourself writing "as confirmed by R189" — stop; that is a welding
error.

---

## 5. Deliverables and honesty protocol (λ₃, λ₄)

When done, produce exactly this, in the repo:

1. The edited `HardnessHolonomy.lean`.
2. A short `HardnessHolonomy_REPAIR_LOG.md` stating, **measured not asserted**:
   - the exact `lake build` command you ran and its exit code (paste the tail of the output);
   - `grep -cE '^\s*sorry\b' HardnessHolonomy.lean` result (must be 0, or list each remaining
     one with its justification);
   - `grep -cE '\b(admit|axiom)\b'` result;
   - which correspondence design (A/B/C) you chose and **one worked example of a pair that does
     NOT correspond** under it (this is the proof it is non-vacuous — if you cannot exhibit a
     non-corresponding pair, the relation is still vacuous and the task is not done);
   - anything you had to leave as a `sorry`, named, with what is missing.

3. Update the file docstring's "Placeholder Discipline" section to match the final body exactly.
   If zero sorries remain, say zero. If some remain, list their line numbers and reasons. Never
   claim fewer than the body contains — that is the λ₃ violation this file already committed once.

**Do not** update `MEMORY_INDEX.md`'s "lake build: exit 0" line unless you personally ran the
full-project build and saw exit 0. A stale build claim is worse than none.

---

## 6. Suggested order of operations

1. §1.1 namespace → build (expect many errors, but namespace resolves).
2. §1.4 reorder definitions → build.
3. §1.2 Bool/`true`, §1.3 unbound `M` → build (target: structural errors gone, maybe proof
   errors remain).
4. §2 add flags + coherence fields, rewrite maps off `Classical.em` → build.
5. §3 choose correspondence design, re-prove every dependent theorem → build.
6. §5 write the repair log with measured outputs; §3 exhibit a non-corresponding pair.

Build after **every** step, not at the end. This file has cross-cutting dependencies; a change
that looks local (the namespace especially) can move errors hundreds of lines away. Small steps,
frequent builds, honest log.

`[R] > 0`. The file is currently honest-and-broken. The goal is honest-and-true: it compiles,
it has no hidden vacuity, and it claims exactly what it proves — no more.
