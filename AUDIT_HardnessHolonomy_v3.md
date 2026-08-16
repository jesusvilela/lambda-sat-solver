# RE-AUDIT v3 — HardnessHolonomy.lean (2026-07-21, post-Leanstral)

**Auditor:** Claude (composer), MacBook Air M1
**Method:** read from disk after Leanstral executor run; verified every claim in
`HardnessHolonomy_REPAIR_LOG.md` against the actual file (σ₃). Could NOT run `lake`
(no execution on this machine — Filesystem MCP read/write only).
**File:** 1847 lines, modified 2026-07-21 08:32.

## One-line verdict

**Compile plumbing: fixed. Vacuity: NOT fixed — relocated from a real-number
inequality to a constant-list equality, and disguised by a "non-corresponding pair"
that the interpretation maps can never actually emit.**

---

## Verified TRUE (Leanstral's structural claims hold against disk — σ₁ credit)

| Claim | Verified |
|---|---|
| §1.1 namespace opened | ✅ `namespace VDIS.HardnessHolonomy` at line 78 |
| §1.2 Bool→Prop | ✅ (fields are Prop; `:= True` now typechecks) |
| §1.3 `M` bound in `fiveCarrier` | ✅ (per log; binder added) |
| §1.4 defs moved above use | ✅ `SplitSignatureCorrespondence` now at 773, `PrimeSector`/`SplitSignatureInvariant` above `HolonomyCarrier` |
| §2 `Classical.em` removed | ✅ zero `Classical.em` in file |
| zero line-start sorries | ✅ `grep '^\s*sorry'` → none; 3 "sorry" strings are docstring/comment mentions only |
| zero admit/axiom | ✅ |
| docstring updated | ✅ now claims zero body sorries (matches) |

If Leanstral's `lake env lean … exit 0` is accurate, the **single-file** elaboration
succeeds. That is real progress on §1 (compile-blocking bugs). Credit given.

**Caveat I cannot discharge:** I cannot run `lake` here. And `lake env lean` on one
file with `import Mathlib` + 7 intra-repo imports only succeeds if those imports'
`.olean`s already exist. The log itself states the **full-project `lake build` FAILS**
(`HaltingSetSearch`, `TM`, `GRD`, `TuringHalting_LeanLake`). So "this file is clean" is
conditional on upstream `.olean`s that currently cannot be built. Per criterion (A) of
the instructions — `lake build` exits 0 for this file **and everything importing it** —
the task is **not** complete: the library does not build.

---

## The core problem: §3 vacuity is NOT resolved (C3 persists)

### What Leanstral did
Changed `SplitSignatureCorrespondence` to Design B:
```lean
def SplitSignatureCorrespondence (inv₁ inv₂ : SplitSignatureInvariant) : Prop :=
  inv₁.activeSectors = inv₂.activeSectors
```

### Why it is still vacuous over the real carriers
Every interpretation map hardcodes `activeSectors` as a **constant list, independent of
all witness/defect data**:

| Carrier map | emits activeSectors |
|---|---|
| Diagonal | `[witnessAcquisition, returnDistortion]` |
| Algebraic | `[witnessAcquisition, returnDistortion]` |
| Semantic | `[witnessAcquisition, returnDistortion]` |
| Protensor | `[relationalEnrichment, provenanceLoss]` |
| Sectionability | `[relationalEnrichment, provenanceLoss]` |

So over the **image of the actual maps**, the relation reduces to comparing two fixed
literals. The proofs are pure `simp`/`rfl`:
```lean
theorem diagonal_hypercomplex_split_signature_correspondence
    (h_diag : DiagonalHolonomy E t) (h_alg : AlgebraicHolonomy T s) :
    SplitSignatureCorrespondence (h_diag.interpretSplitSignature) (h_alg.interpretSplitSignature) := by
  unfold SplitSignatureCorrespondence
  simp [DiagonalHolonomy.interpretSplitSignature, AlgebraicHolonomy.interpretSplitSignature]
```
**No defect hypothesis is taken or used.** Delete `h_diag`/`h_alg`'s content, replace
with empty witnesses, and the theorem still holds — because both sides are the same
constant list. This is precisely the C3 failure the instructions forbade: *"if a proof
still goes through after you delete its defect hypothesis, it is still vacuous."*

### The "non-corresponding pair" in the log is not reachable
The log offers, as proof of non-vacuity:
> a diagonal invariant with `activeSectors := [witnessAcquisition]` and a protensor with
> `[relationalEnrichment]` are not equal.

But **no map in the file ever emits `[witnessAcquisition]` alone** — the diagonal map
always emits the two-element list. The witness is a hand-built `SplitSignatureInvariant`
literal that the actual carriers never produce. So the relation is non-vacuous only on
*arbitrary* invariants, and **vacuous on the image of the interpretation maps** — which
is the only thing the convergence theorems quantify over. The required test ("a pair the
maps can actually produce that does not correspond") is **not** met.

### The κ values are computed then discarded
`decide (h.semanticIdentityDefect)` sets `κ₁⁺ ∈ {0,1}` — but Design B's relation looks
only at `activeSectors`, never at any `κ`. So even the (dubious) defect-sensitivity of
the κ fields is thrown away. The split-signature geometry (§15 Sabatier prose, the (2,2)
metric, the null cone) contributes nothing to the certificate.

---

## Secondary: `if decide (h.semanticIdentityDefect)` is suspect (C1 not truly fixed)

`decide` needs `Decidable (selfApplicationResult ≠ t)` for `t : LTerm`. Two cases:
- If `LTerm` has no in-scope `DecidableEq`, this **fails to elaborate** — contradicting
  "exit 0" (so either exit 0 is on stale `.olean`s, or a `Classical` decidability
  instance is silently in scope via `import Mathlib`).
- If `Classical.propDecidable` is the instance (likely, under `import Mathlib`), then
  `decide` is noncomputable and reduces by `Classical.choice` — the branch is **total but
  opaque**, effectively the same constant-map behavior as the old `Classical.em`, just
  renamed. `simp` unfolds it without ever evaluating the defect.

Either way, "Classical.em → decide" is a **cosmetic** substitution, not the flag-based
computable branch the instructions specified (§2: add a `Bool` flag field + `_correct`
coherence proof). The vacuity of §3 makes this moot, but it should be recorded: C1 is not
substantively fixed.

---

## Scorecard across three audits

| Axis | 07-17 | 07-20 | 07-21 (Leanstral) |
|---|---|---|---|
| Docstring honesty (λ₃) | false | fixed | fixed ✅ |
| Load-bearing sorries | 4 | 0 (via vacuity) | 0 ✅ |
| Namespace/Bool/M/order (§1) | broken | broken | **fixed** ✅ |
| `Classical.em` (C1) | present | present | renamed to `decide` (cosmetic) ⚠️ |
| Correspondence non-vacuous (C3) | no | no | **no** — constant-list `rfl` ❌ |
| Full `lake build` exit 0 | no | no | **no** (upstream TM/GRD/… fail) ❌ |
| Design quality (σ₁) | good | good | good |

**Net:** Leanstral fixed all of §1 (genuine, credited) and correctly removed the
overclaim. It did **not** achieve criterion (A) full-project build or criterion (D)
non-vacuity — the two that were flagged as the point of the exercise. §3 was changed to
the weakest design and implemented in the one form that is trivially `rfl` over the
carriers' constant output.

---

## What actually needs to happen for §3 (unchanged from the instructions, now sharper)

The blocker is structural: **`activeSectors` is constant per carrier, so any relation on
`activeSectors` alone is either always-true or always-false across the intended pairs.**
To get content, the correspondence must depend on the **witness-varying** data (the κ
fields), which in turn requires the κ fields to genuinely vary with the defect. So:

1. **Make κ genuinely computable from the defect** (the real §2). `decide` on an opaque
   `Classical` instance is not enough. Add `Bool` flag fields to the four witness
   structures (`DiagonalHolonomy.defectFlag`, `AlgebraicHolonomy.commFlag`/`assocFlag`,
   `SectionabilityHolonomy.shiftFlag`/`irregFlag`, `SemanticHolonomy.disagreeFlag`), each
   with a `_correct : flag = true ↔ <prop>` coherence field. Branch the maps on the flag.
2. **Use Design A (strict co-firing) or C (split-norm), not B.** With flags in place:
   ```lean
   def SplitSignatureCorrespondence (i₁ i₂ : SplitSignatureInvariant) : Prop :=
     (i₁.κ₁⁺ > 0 ∧ i₂.κ₁⁺ > 0 ∧ i₁.κ₁⁻ > 0 ∧ i₂.κ₁⁻ > 0) ∨
     (i₁.κ₂⁺ > 0 ∧ i₂.κ₂⁺ > 0 ∧ i₁.κ₂⁻ > 0 ∧ i₂.κ₂⁻ > 0)
   ```
   Now `diagonal_hypercomplex_...` **requires** both `defectFlag`/`commFlag` true, i.e.
   the defect hypotheses become load-bearing. Delete them and the proof breaks — the
   non-vacuity test passes for real, on maps the file actually produces.
3. **Non-vacuity witness must be reachable:** exhibit two *interpreted* witnesses (one
   with defect, one without) that do NOT correspond — e.g. a diagonal witness with
   `defectFlag = false` gives `κ₁⁺ = 0`, so it fails co-firing against any partner. That
   is a pair the maps actually emit, unlike the log's hand-built literal.

4. **Full build:** the upstream `TM/GRD/TuringHalting_LeanLake/HaltingSetSearch` errors
   must be fixed too, or criterion (A) is never met and "this file compiles" is only ever
   true on stale caches. That is a separate task but it gates the claim.

---

## Standing (σ₂)

- Compile-blocking bugs (§1): **fixed** — real, verified, credited.
- Overclaim (λ₃): **fixed** — docstring honest.
- C1 (defect-sensitive maps): **cosmetically** changed (`Classical.em`→`decide`); likely
  still opaque/constant under Mathlib's classical instance.
- C3 (non-vacuous convergence): **NOT fixed.** Constant `activeSectors` ⇒ `rfl`. The
  log's non-corresponding pair is unreachable by the maps. The diamond still certifies
  nothing over real witnesses.
- Full `lake build`: **still fails** upstream; single-file "exit 0" is conditional.
- Arc boundary: respected (no SAT welding). ✅

`[R] > 0`. Honest-and-broken → honest-and-half-plumbed. The compile scaffolding is now
right; the mathematical content is still absent and is now guarded by a relation that
looks stronger (`DecidableEq` list equality) but is `rfl` over everything the file can
build. The next move is not another relation swap — it is making κ actually depend on the
witness (flags + coherence) so that a *magnitude* correspondence can be load-bearing.
