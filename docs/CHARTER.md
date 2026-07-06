# Charter — stance, claim discipline, and the shared geometry

*Load first. Non-negotiable. This is the document that keeps the science honest;
everything else in the repository answers to it.*

This project has two temperaments living in one body: an **imaginative** one that
reaches for deep geometric and algebraic structure in SAT hardness, and a
**skeptical** one that refuses to believe anything it has not verified. They are
not rivals. They are conjugates — and the whole method is to let them cancel into
what survives.

## Part I — Claim discipline (the skeptic's law)

These rules are absolute. A contribution that violates one is wrong regardless of
how beautiful it is.

1. **A name is not a proof.** "`EmperorEmpressTheorem`", "`P_neq_NP`",
   "`equivalent_to_BQP`" — the label carries no truth. Check the body. Several
   Lean "theorems" in this project's heritage proved `168 = 168` or
   `1 < degeneracy` under an impressive name; that is documented, not hidden.

2. **Verify before you trust — empirically, end to end.** Kissat is not in the
   Trusted Computing Base; every SAT result is model-replayed and every UNSAT
   result is proof-checked. Every research claim is bound to a test. If it isn't
   tested, it isn't claimed.

3. **No vocabulary without a contract.** You may not import a word — *sheaf,
   gyrovector, holonomy, chromatic height* — unless you can state its
   **input → invariant → action → benchmark**. `backend/complexity/contracts.py`
   enforces this: every invariant carries its promise, its theorem (if any), and
   its honest limit, and a test fails if a "carrier" cites no theorem.

4. **Label the register.** Every claim is one of: *proven* (a theorem, cited),
   *measured* (a benchmark, with its scope), or *speculative* (a lens, said so).
   Mixing these is the cardinal sin. "Rich obstruction" is not "superpolynomial
   lower bound"; `48×` more coupling channels is a count, not a hardness proof.

5. **Report what the data said, not what you hoped.** Every pre-registered
   prediction in this project's history that failed is recorded as having failed.
   The negative results (cheap graph invariants do *not* carry hardness; the
   symmetry channel *collapses* in characteristic 2; "NS ≥ width" was *false*,
   Tseitin being the witness) are load-bearing, not embarrassments.

6. **The verdict casts a scalar; the object need not be one.** Hardness is a
   scalar because "harder" is an order relation. But the object it measures may be
   a field, a variety, a group. Do not mistake the shadow for the thing — and do
   not pretend the shadow is dispensable when a decision is demanded.

## Part II — The shared geometry (the imaginer's lens)

This is the interpretive frame the research half is written in. It is a **lens**,
explicitly — it earns its place only where Part I lets it. Where it has produced
theorem-backed or benchmarked objects, they live in `docs/ladder/`.

- **The obstruction is where 0 stops being a point.** In a division algebra 0 is
  isolated; leave them (sedenions) and the zero-set of multiplication becomes a
  variety — the zero divisors. Hardness lives exactly there: the *rank
  deficiency* / cokernel of an obstruction operator. Executable form:
  `nullstellensatz_degree` (the Nullstellensatz degree over GF(2)).

- **Emperor and Empress.** Conjugation is an exact anti-pairing: for the octonion
  associator, `A_conj = −A_std` (verified, cos = −1 to machine precision).
  Opposition is not loss; the anti-pair is the conserved record of a collapse.
  The verifier is the Emperor to the imaginer's Empress — and what survives their
  cancellation is the part that is actually true.

- **Depth is algebra-relative; stratify, don't collapse.** A formula's hardness is
  the depth at which its obstruction becomes irreducible *in a given proof
  algebra* — and that depth changes with the algebra (PHP: width 2, NS-degree 4;
  Tseitin: width 4, NS-degree 3 — incomparable). You never collapse the depth to
  a point; you read it stratum by stratum (resolution width, NS degree, chromatic
  height, XOR-frame). Solving = finding the algebra where the obstruction is
  shallow — which is exactly what a portfolio solver does, and what
  `xor_extraction` cheaply detects.

- **The drone.** Smoothing dissolves the *removable* part of hardness into
  simplicity (rationalize the torsion away; relax to a convex program). What
  survives every smoothing is the irreducible obstruction — the drone. The point
  of every invariant here is to hear that one conserved note precisely, and never
  to let it be smoothed to zero.

## Part III — How the two live together

The imaginer proposes; the skeptic disposes; and the method is the cancellation.
A geometric idea (Part II) is admitted only once it is turned into a computable,
contracted, tested object (Part I) — and when it fails that test, the failure is
reported and kept. This is why the ladder's honest survivors are all classical
(resolution width, Nullstellensatz degree, XOR/Gaussian frame detection), and why
the exceptional structure (𝔤₂, G₂, braids) is documented as *real mathematics
that names hard objects without cheapening them* — never as a solved P vs NP.

If you are extending this work: bring your wildest idea. Then make it a function
with a contract and a test, run it, and write down what actually happened. That
is the whole discipline, and it is the only thing that has ever moved this
project forward.
