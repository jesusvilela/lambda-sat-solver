# What survives the collapse — the counting frame (php12)

The SOTA benchmark's one middleware loss was `php12`: the pigeonhole principle,
12 pigeons into 11 holes. It has `xor_fraction = 0` (the GF(2)/parity frame is
blind) and its 2-SAT subset is consistent (the implication frame is blind), so
it *survived* both frames we had — and fell through to a Kissat fallback that
timed out. The question: **what in it survives collapse against our geometry?**

## The answer: it survives because GF(2) cannot count

The pigeonhole obstruction is a **magnitude** fact — 12 > 11 — not a parity
fact. And characteristic 2 destroys magnitude: over GF(2), `1 + 1 = 0`, so
"twelve pigeons" and "eleven holes" both collapse to their parities and the
inequality vanishes. The pigeonhole contradiction lives in the **integers**
(counting), and our GF(2) frame works in the field of two elements. It is not a
weakness of the detector; it is a fact about the characteristic. **PHP survives
the GF(2) collapse because the pigeonhole principle is a statement about
counting, and GF(2) cannot count.**

## PHP is the characteristic-0 dual of Tseitin

This completes a duality that has been implicit the whole way:

| family | shallow frame (collapses) | deep frame (survives) |
|---|---|---|
| **Tseitin** | GF(2) linear algebra (Gaussian) — char 2 | resolution / counting |
| **PHP** | integer counting (cutting planes) — char 0 | resolution / GF(2) |

They are **conjugates** — Emperor and Empress at the level of *proof systems*.
Tseitin is char-2-shallow and char-0-deep; PHP is char-0-shallow and
char-2-deep; and resolution (plain CDCL) is deep for **both** — which is exactly
why Kissat times out on Tseitin *and* on PHP, and why a single-frame or
single-engine solver keeps hitting one or the other. The drone that survives
every collapse is the obstruction that is in the wrong characteristic for your
frame. (This is the algebra-relative Emperor-depth of `LEARNINGS.md`, now with a
name for the second axis: not just *which algebra*, but *which characteristic*.)

The theory is sharp here: PHP has **polynomial-size cutting-planes refutations**
(the counting proof) but requires **2^Ω(n) resolution** (Haken 1985). Tseitin
over expanders is the mirror: polynomial in GF(2), exponential-width in
resolution. Each is the other's canonical hard case.

## Made executable: the third frame

`backend/cardinality_check.py::pigeonhole_counting_refutation` is the counting
frame — the third sibling of `binary_clause_check` (implication) and
`xor_extraction` (parity). It recovers the pigeonhole structure and refutes it by
the sound counting argument:

- **ALO** — each all-positive clause forces ≥ 1 true; `k` variable-disjoint ALO
  clauses ⇒ ≥ `k` trues (the pigeons).
- **AMO** — a clique of pairwise-excluded variables (negative binary clauses)
  holds ≤ 1 true (a hole); `m` disjoint such cliques covering the ALO variables
  ⇒ ≤ `m` trues.
- `k > m` ⇒ UNSAT.

Result: **`php12` now collapses in 0.44 ms**, soundly — under *our* geometry,
not by borrowing CaDiCaL's luck — and the whole PHP family (n = 3..12) refutes in
< 0.5 ms, each with `k = n`, `m = n-1`. Tseitin, random-3-SAT, and XORSAT are
correctly *not* refuted (they fall through). The frame that was missing is the
one the geometry named.

## The trilogy

The middleware now carries three sound, poly-time, engine-independent frames,
one per obstruction type, each collapsing exactly the family that is hard for the
others:

- **implication** (2-SAT / SCC) — `binary_clause_check`
- **parity** (GF(2) / Gaussian) — `xor_extraction`
- **counting** (ℤ / cardinality) — `cardinality_check`

Anything outside all three falls through to a DRAT/model-certified CDCL engine.
That is the shallow-Emperor hunt made concrete: three cheap probes for the three
characteristics in which an instance's obstruction might already be shallow.
