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

## What still grows next

Meta-resolution is now real for the parity frame; extending the frame-native
recognizer to the **counting** frame (ALO/AMO structure in a β-normal term) is
the direct sequel. And the deeper contract is unchanged: enrich the payload
beyond Boolean so the projection becomes genuinely lossy, `ε > 0`, and the
remainder carries active, unprojected truth — *measured, not asserted*. That is
where Λᴿ stops being a lens. Until then: lambda supplies the term, the shallowest
frame selects the survivor, the certificate is the braid, and the remainder is
the fossil record — all of it verified.
