# Frame benchmark — the shallow-Emperor corollary, tested on real solvers

**Claim under test (the corollary of `LEARNINGS.md`):** a formula's `xor_fraction`
predicts a *frame advantage* — on parity-structured (high `xor_fraction`)
instances the GF(2) frame (Gaussian elimination) is polynomial while CDCL is
exponential; on random 3-SAT the reverse. Tested with **Kissat 4.0.4** and
**CaDiCaL** against a GF(2) Gaussian decision, 97 instances across 5 families,
20 s timeout. Harness: `docs/ladder/scripts/frame_benchmark.py`; raw rows:
`frame_benchmark_results.json`.

**Verdict: confirmed, decisively — and it is not solver-specific.**

## 1. Tseitin-expander (xor_fraction 1.0, UNSAT) — the theoretical separation, realized

Tseitin over random 3-regular graphs: resolution width is Ω(n) (Ben-Sasson–
Wigderson) so CDCL must be exponential, while the constraints are pure parity so
Gaussian elimination is polynomial. Measured (median over seeds):

| vertices | edges (vars) | Kissat | CaDiCaL | GF(2) Gaussian |
|---|---|---|---|---|
| 30 | 45 | 0.01 s | 0.01 s | 0.03 ms |
| 50 | 75 | 0.08 s | 0.08 s | 0.04 ms |
| 70 | 105 | ~1.0 s (up to 3.4 s) | up to **18.7 s** | 0.05 ms |
| 80 | 120 | up to timeout | up to timeout | 0.06 ms |
| 90 | 135 | **2/3 timeout** | **3/3 timeout** | 0.07 ms |
| 100 | 150 | **timeout (>20 s)** | **timeout (>20 s)** | 0.08 ms |

Both CDCL engines blow up exponentially; **Gaussian is flat sub-millisecond the
entire way** — a >200,000× gap by nv=100, and growing. CaDiCaL is often *worse*
than Kissat (nv=70: 18.7 s vs 0.6 s), so this is a property of the resolution
frame, not of one solver.

## 2. The controls behave exactly as the corollary requires

- **PHP (xor_fraction 0.0, UNSAT):** Kissat is exponential (PHP(11→10) 2.55 s),
  and Gaussian is **N/A** — 0 XORs recovered. The detector correctly says "the
  algebraic frame does not apply here," so you would *not* misroute PHP. Both
  frames are hard; this is the counting obstruction, not the parity one.
- **Random 3-SAT (α=4.26, xor_fraction ~0):** Kissat is fast (≤0.05 s), the
  algebraic frame is absent. CDCL's own frame — correctly left to CDCL.
- **Random XORSAT (xor_fraction 1.0):** Gaussian decisive; Kissat also solves
  these ~instantly at n≤80. Honest nuance: *random* XORSAT is not width-hard for
  CDCL at these sizes — it is the **expander** structure of Tseitin that forces
  the width. High `xor_fraction` flags where Gaussian *applies*; the dramatic
  win needs the expander too.
- **Mixed (0<xor_fraction<1):** at xor 0.80–0.89 the Gaussian core alone
  **certified UNSAT** (agreeing with Kissat) — the algebraic frame refuting the
  whole formula through its parity core; at xor 0.67 it was inconclusive and
  correctly deferred to CDCL.

## 3. Portfolio analysis (97 instances, 6 Kissat timeouts)

| strategy | PAR-2 (s) |
|---|---|
| Kissat-always | **2.858** |
| xor-router (Gaussian when decisive, else Kissat) | **0.036** |
| virtual-best-solver | **0.036** |

The `xor_fraction` router gives a **~79× PAR-2 reduction** and **equals the
virtual-best** — the cheap detector routes essentially optimally — while the
detector itself adds **0.66 ms/instance**. **Soundness: 53/53** Gaussian-UNSAT
verdicts agreed with Kissat (0 unsound refutations), as the entailment guarantee
requires.

## 4. Honest scope

The 79× is *concentrated in the Tseitin family* — the 6 timeouts drive the PAR-2
gap. On XORSAT / random-3-SAT / PHP the router ties Kissat or correctly defers.
So the earned claim is precise, not universal: **XOR-aware Gaussian reasoning is
a large, sound win exactly where the frame is algebraic *and* CDCL is width-hard
(parity over expanders), and a no-op elsewhere.** This is the CryptoMiniSat
lesson reproduced from first principles — and it is exactly what the corollary
predicted: the shallow Emperor is algebra-relative, and cheaply detectable.

## 5. What this earned

The evidence clears the repo's standing bar ("route only on demonstrated
benchmark evidence"), so the sound integration is now in the tree:
`backend.xor_extraction.gf2_xor_refutation` — an engine-independent UNSAT
fast-path (the GF(2) sibling of `binary_clause_check`) that returns in <<1 ms on
exactly the instances where CDCL times out. It is *sound* (recovered XORs are
entailed, so an inconsistent XOR subsystem refutes the formula), so running it
before CDCL can only help.

**Update — the SAT side is now complete too.** `gf2_xor_solve` closes the loop:
on a parity-covered formula it decides both directions — `UNSAT` (sound for any
formula) or `SAT` with a model **independently re-checked by `verify_model`**
before it is ever returned (Charter: verify, don't trust). Cross-checked on 40
random XORSAT instances: 0 unverified models, 39/40 agree with Kissat (the 40th
correctly `INCONCLUSIVE`, not a disagreement). The algebraic frame is now a full
poly-time decision procedure for the pure-parity fragment, SAT and UNSAT alike.
