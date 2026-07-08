# Hyperbolic PROGRAMMING and the frame ladder (a state-of-the-art bridge)

*Applying a genuine state-of-the-art technique — hyperbolic programming — to our
own object, honestly. This is a lens/substrate note, not a solver claim.*

## The disambiguation that unlocks it

Earlier in this program "hyperbolic" was read as hyperbolic *geometry* (curvature,
the Lorentz model) and honestly scoped out — Rung 1 showed geometric embeddings
do not carry SAT hardness. But the intended sense was something different and much
more load-bearing: **hyperbolic PROGRAMMING** in the Gårding–Güler–Renegar–Brändén
sense — convex optimization over the *hyperbolicity cone* of a hyperbolic
polynomial, the largest structured generalization of conic optimization, with
**LP, SOCP and SDP as special cases**. That reading has a real bridge to this
repo, and it had been mislabeled "no connection." This note repairs that.

## Definitions, made computable

A homogeneous polynomial `p` of degree `d` is **hyperbolic** w.r.t. a direction
`e` if `p(e) > 0` and, for every `x`, the univariate `t ↦ p(t·e − x)` has all
real roots. Those roots are the **hyperbolic eigenvalues** of `x`; the
**hyperbolicity cone** `Λ_{p,e}` is where they are all ≥ 0 (Gårding: it is
convex). The canonical special cases:

| `p(x)` | cone `Λ_{p,e}` | conic program |
|---|---|---|
| `x₁···xₙ` | non-negative orthant | **LP** |
| `r² − ‖x‖²` | Lorentz cone | **SOCP** |
| `det(X)`, `e = I` | PSD cone `Sⁿ₊` | **SDP** |

`docs/ladder/scripts/hyperbolic_frames.py` computes hyperbolic eigenvalues by
interpolate-and-root-find and checks the SDP case as a correctness anchor: for a
symmetric `X`, the hyperbolic eigenvalues of `X` w.r.t. `I` **are** its matrix
eigenvalues (verified to 1e-6).

## The genuine bridge: two of our three frames live on the HP ladder

Our solver rests on three sound frames. Hyperbolic programming places two of them
precisely, and — just as precisely — **cannot see the third**.

**Implication / 2-SAT ↔ the orthant (the LP vertex).** The 2-SAT frame is the
Boolean face of the non-negative orthant `p = x₁···xₙ`, the base case of the
whole HP hierarchy.

**Counting / cardinality ↔ the elementary-symmetric derivative relaxations.**
This is the non-obvious, verified part. The **elementary symmetric polynomials**
`e_k` are hyperbolic w.r.t. `(1,…,1)` (the demonstrator confirms every restriction
is real-rooted for all tested `n,k`; Brändén proved their cones are even
*spectrahedral*). And they are exactly **Renegar's derivative relaxations** of the
LP cone: `e_{n-1} ∝ D_e(x₁···xₙ)`, and the iterated derivatives give a **nested
tower**

```
orthant = Λ(eₙ) ⊆ Λ(e_{n-1}) ⊆ ··· ⊆ Λ(e₁) = { Σxᵢ ≥ 0 }  (a halfspace).
```

The demonstrator witnesses the nesting is *strict*: `x = (1,1,−1)` is in the `e₁`
halfspace but out of the orthant. **Cardinality constraints — at-least-k,
at-most-k, the pigeonhole counting bound — are the combinatorial face of exactly
this symmetric-function ladder.** So `cardinality_check` is not an ad-hoc trick;
it sits on the derivative-relaxation tower of the LP cone, which is a
state-of-the-art object in convex algebraic geometry.

## The disanalogy, named honestly (and why it matters)

The **parity / GF(2) frame has no hyperbolicity cone at all.** Hyperbolicity is a
*real-rootedness / ordering* notion — "all eigenvalues real, all ≥ 0". GF(2) has
no order, no reals, no eigenvalues to be real. This is the **same char-2 wall**
the ladder already hit for the Lie telos (`RUNG2_LIE_TELOS_NOTE.md`: real over ℝ,
char-2 obstructed) and for the symmetry channel (`symmetry_channel_ns.py`). So
hyperbolic programming illuminates implication and counting and is *structurally
blind* to parity — which is a second, independent derivation of **why the frame
trilogy needed a characteristic-2 member in the first place**. The thing HP cannot
see is exactly the thing GF(2) Gaussian elimination was there to catch.

## Where HP touches the hardness carrier (the honest, non-solver payoff)

Our `nullstellensatz_degree` carrier is the GF(2)/char-2 algebraic proof object.
Its **real-closed-field cousin** is the sum-of-squares / Positivstellensatz
certificate — and SOS optimization *is* SDP, the special case of HP. Saunderson
(2019) showed **hyperbolic certificates of nonnegativity** that are strictly more
general than SOS. This is the honest formal home for the recurring instinct that
"the exceptional symmetry should be a computational lever rather than a name": if
that lever exists, it lives as a **symmetry-adapted hyperbolic/SOS certificate**
on the ℝ-side rank-deficiency operator — precisely the "open / next" item the
ladder README already lists. HP tells us what that object *is*; it does not make
it cheap (deciding hyperbolicity is co-NP-hard; these certificates are
exponential-degree, like every honest proof-complexity carrier).

## Status (Charter labels)

- **Proven / cited:** Gårding (convex cones), Güler (`−log p` self-concordant
  barrier), Helton–Vinnikov / Lewis–Parrilo–Ramana (Lax in 3 vars),
  Brändén (`e_k` cones spectrahedral), Renegar (derivative relaxations),
  Saunderson (hyperbolic nonnegativity; co-NP-hardness).
- **Measured here:** det = matrix eigenvalues; `e_k` real-rooted; strict
  derivative-relaxation nesting (`test_hyperbolic_frames.py`, 4 tests).
- **Lens / open, NOT claimed:** that HP gives a faster SAT decision (it does
  not — it is a certificate/relaxation world, exponential in the worst case); the
  symmetry-adapted hyperbolic certificate on the rank-deficiency operator (the
  same ℝ-side rung that remains open). No metal, no solver route, no external
  SDP/HP dependency added — numpy-only, already core.
