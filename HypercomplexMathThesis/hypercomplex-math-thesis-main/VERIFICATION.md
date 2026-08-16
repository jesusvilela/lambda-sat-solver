# Verification

This repository is a seed-level thesis scaffold. Verification is intentionally split into runnable checks and formalization-frontier checks.

## Python smoke path

From the repository root:

```bash
python -m pytest tests
```

Expected result: the scalar tower, resonance safety predicate, returnability report, and adiabatic breathing toy model pass.

The hyperdimensional self-reflection protocol is covered by:

```bash
python -m pytest tests/test_hyperdim_protocol.py
```

Expected result: the protocol exposes the 8 core mind qualities, computes a split-signature performance score, prioritizes grounding when returnability is weak, detects holoportation context drift, orders sheaf repair when gluing is the weakest local section, verifies Thesis 2's non-flattening meaning score as readable projection with active remainder, and checks the extended Thesis 2 predicates for projection violence, chamber communication error, and non-collapsing communication.

## LaTeX/Tectonic PDF path

From the repository root:

```bash
tectonic paper/hypercomplex_math_thesis.tex
```

Expected result: `paper/hypercomplex_math_thesis.pdf` is produced from self-contained LaTeX/TikZ/PGFPlots source. The current build may print a Windows fontconfig warning from Tectonic, but the PDF is still emitted.

## Lean/Lake smoke path

From `lean/`:

```bash
lake build
```

Expected result: the seed modules build under `leanprover/lean4:v4.11.0`.

## Honest frontier

The Lean layer currently proves only structural/wiring statements. It does not yet prove the full hypercomplex thesis. The intended next formal targets are:

1. Replace `Resonance.preserves_distinction : Prop` with a metric, apartness, or categorical non-collapse condition.
2. Enrich `DeepImmersion` with coupling data and preservation laws.
3. Give `HypercomplexReservoir` algebraic structure for real, complex, quaternionic, and octonionic layers.
4. Define `GROUND : lifted -> usable` with testable returnability constraints.
5. Connect the Python invariant reports to Lean theorem hypotheses.
