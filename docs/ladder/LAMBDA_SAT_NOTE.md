# Clashing SAT and Lambda — what survived, what fossilized

The operator's Λᴿ ("lambda with remainder") vision — a hypercomplex, moving-frame
universal lambda language, and a Λᴿ-SAT that treats clauses as manifold patches
and UNSAT as non-vanishing holonomy — is beautiful and large. The instruction was
the Charter itself: *clash SAT and Lambda, see what survives and grows.* So the
vision was run through computation, and only the survivors entered the repo
(`backend/lambda_sat.py`, 8 tests).

## Survivors (built, tested)

- **The remainder = provenance (the "ghost fiber").** When a Boolean lambda term
  is projected into CNF (Tseitin), each clause is tagged with the lambda node
  that produced it (`and`, `or`, `const`, `assert-true`). The shadow remembers
  its source. Real, exact, tested (`test_remainder_links_clauses_to_source`).
- **Lambda ⊗ SAT fusion.** `lambda_sat(term)`: β-normalize (lambda motion) →
  decide at the source (the surviving braid) → project into CNF with the
  remainder → cross-check that the projection preserved truth. A satisfying
  assignment is the living braid; UNSAT is the obstruction. The witness is
  **certified by re-evaluation** (verify, don't trust the search).
- **"SAT = gluing, UNSAT = obstruction."** This part of the vision was *already
  proven* in the repo: it is bounded-width resolution / the sheaf-obstruction
  (`RUNG2_REPORT.md`, `min_refutation_width`). The vision restates Rung 2.
- **"Restart = gauge, multi-projection solving."** Also already built: the frame
  trilogy (implication / parity / counting) is exactly "the same object seen in
  different projections; pick the one where the obstruction is shallow"
  (`COUNTING_FRAME_NOTE.md`, the shallow-Emperor hunt). The vision restates the
  middleware.

## Fossils (kept as lens, not built)

Curvature/holonomy scoring, octonionic non-associativity of clauses, zero-divisor
"annihilation channels" as a literal solver mechanism, the `0 < ε < τ` living
zone as runtime control — these are lenses. They do not, today, *decide* SAT, and
per the Charter vocabulary does not enter as machinery without a contract. They
stay lenses until one of them earns a frame the way *counting* did — at which
point it graduates from note to module, with a test.

## The one honest refinement to the vision

The vision's deepest primitive is the **active remainder** `0 < ε < τ`: a
projection that loses no truth (`ε = 0`) is "death / flattening." But for a
*Boolean* lambda term the Tseitin projection is **equisatisfiable** — it loses no
truth, so `ε = 0` *by construction*, and the remainder here is **provenance**
(explanatory), not lost truth (`test_projection_is_faithful` verifies exactly
this: CNF-SAT iff source-SAT). The living zone `ε > 0` — a remainder carrying
*active, unprojected truth* — only appears when the payload is richer than
Boolean (types, uncertainty, higher-order structure the Boolean shadow cannot
hold). That is real and unbuilt: the honest next step, and the place the
hypercomplex carrier would actually earn its keep.

## Meta-resolution — the next contract, now landed

The first version of `lambda_sat` only *self-resolved* (decided the term by brute
force). The blocker for *meta-resolution* (choosing the frame that collapses the
contradiction) was diagnosed honestly: the naive Tseitin gate-projection flattens
frame structure — the auxiliary gate variables hide any parity/counting pattern,
so the three frames never fire on the projection. That is `ε` in the flesh: the
projection erased the very frame it needed.

The contract discharged: a **structure-preserving encoder**. When the beta-normal
form is a **parity system** (a conjunction of XOR-over-literals, now that `BXor`
is a first-class constructor), it is encoded **frame-native** — parity clause
groups over the original variables, *no auxiliary gates* — so the GF(2) frame
recognizes it and `gf2_xor_solve` decides it in polynomial time, certified. The
result records `resolved_by ∈ {parity, 2sat, counting, direct}`: the frame that
collapsed the term. Verified (14 tests incl. a 200-instance soundness stress
against brute-force source truth):

- `a ⊕ b` → SAT via **parity** (no enumeration); `(x⊕y) ∧ ¬(x⊕y)` and the odd
  3-XOR cycle → UNSAT via **parity** (Gaussian).
- `(λf. f⊕g)(x⊕y)` → the parity structure appears only *after* β-reduction, and
  is still routed to the GF(2) frame — meta-resolution discovering the shallow
  frame of a reduced term, not assuming it.
- generic `a ∨ b` → falls to a re-verified `direct` decision.

Because the parity encoding has no auxiliary variables, its GF(2) UNSAT is exactly
the refutation whose soundness is stated in `proofs/XorSoundness.lean` — the
fusion, the frame trilogy, and the Lean obligation meet on one object.

## The Y-combinator spine — ε > 0 made literal

The operator's fuller vision was a *Y combinator* — the fixpoint, self-reference —
"in a Calabi-Yau Möbius torus." The honest core of that: **full Y is undecidable**
(a certificate cannot exist for the general fixpoint — the halting boundary), so
"maybe that's too much" is *precisely* true. But its decidable spine is buildable,
and it turns out to be the ε > 0 contract itself.

`fixpoint_sat(λs. body, depth k)` unrolls a Boolean fixpoint to depth k, leaving
the un-reached tail as a free variable — **that tail is the remainder made
literal.** If the depth-k decision still depends on the tail, the fixpoint has not
been pinned down: `ε > 0`, the remainder is *active, unprojected truth*. If it is
independent of the tail, the fixpoint stabilized: `ε = 0`. This is bounded model
checking in miniature, and it is the first place the remainder carries lost truth
rather than mere provenance. Verified (5 tests):

- `λs. a` (ignores the recursion) → stabilizes, **ε = 0**.
- `λs. a ∧ (a ∨ s)` → absorption collapses it to `a` → **ε = 0**.
- `λs. a ∨ s` → the boundary matters (two fixpoints) → **ε > 0**.
- `λs. ¬s` — the **Möbius fixpoint**: traverse once, return flipped; its remainder
  is **eternally nonzero at every depth**. Self-negation is the term that never
  orients, ε never reaching 0 — the operator's non-orientable torus, exact.

So the vision's spine (Y, Möbius, the living remainder) is real and tested; the
Calabi-Yau / 360-orthogonal / curvature envelope stays the lens — the *geometry of
the remainder space* — a lens until one of its constructs earns a frame.

## What still grows next

Extend the frame-native recognizer to the **counting** frame (ALO/AMO structure in
a β-normal term). And the deepest contract: a payload richer than Boolean, where
the projection is genuinely lossy across a *typed/graded* fiber and the remainder
becomes a measured section of what the shadow dropped. Until then: lambda supplies
the term, the shallowest frame selects the survivor, the certificate is the braid,
and the remainder — provenance for Boolean terms, the fixpoint tail for bounded Y —
stays honestly nonzero, all of it verified.
