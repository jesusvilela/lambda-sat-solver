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

## What grows next

The fusion gives a clean growth point: enrich the lambda payload beyond Boolean
(a typed / graded fragment) so the projection into CNF becomes genuinely
lossy, `ε > 0`, and the remainder becomes a first-class carrier of what the
Boolean shadow dropped — measured, not asserted. That is where Λᴿ stops being a
lens and becomes a contract. Until then: lambda supplies the term, SAT selects
the survivor, the certificate is the braid, and the remainder is the fossil
record — all of it verified.
