# Review — the hypercomplex computer designs & channels

A pass over the operator's computer/architecture designs from the pasted
conversations (the Lean structures, the sedenion clock, the VDIS channels),
in the same discipline as `CONTRACTS.md`: what each design *is*, what is real,
what is a `sorry`/`abbrev` triviality, and its honest computational scope. Two
of the five turn out to bridge directly into the ladder — those are the ones
worth building on.

## Inventory

| design | what it is | real content | honest computational verdict |
|---|---|---|---|
| **BerryBraidComputer** (`ballDim, conePoints, degeneracy`) | holonomy-as-computation: braid non-abelian Berry phases | topological quantum computation; non-abelian anyon braiding is **universal for BQP** (Freedman–Kitaev–Larsen–Wang) | real physics, but **BQP is not believed to contain NP** — power, not a SAT route. `NonAbelianBBCEquivalentToBQP := 1 < degeneracy` is an `abbrev`, not a proof of the equivalence. |
| **SymplecticRAM** (`nAddress`) | reversible / phase-space-preserving RAM | reversible computing is real and universal (Bennett; Toffoli/Fredkin); symplectic = measure-preserving = reversible | reversible computation is **polynomially equivalent to classical** — no NP speedup. `SymplecticRAMEquivalentToClassical := 0 < nAddress` is an `abbrev` triviality. |
| **Orbifold normal forms** (`OrbifoldStratum.coneOrder`, `orbifoldNormalFormMultiplicity`) | computation as motion on an orbifold; branching = multiple normal forms indexed by local **cone order** | the cone order at a point **is the order of the local isotropy (stabilizer) group** — a real, precise invariant | structural, not yet a contract — **but see Bridge 1**: the cone/isotropy structure is exactly the symmetry-channel decomposition already in play. |
| **L63 HypercomplexTime** (sedenion clock) | time as a trajectory in `Im(𝕊₁₆)=ℝ¹⁵`; each step = one imaginary-sedenion displacement; "cost `2^(n/7)`" | the Cayley–Dickson facts under it are true (`seven_barriers_leave_one_dim`: 7 octonionic units; zero divisors at level 4) | the leap "algebra fact `2^(n/7)` ⇒ hardness bound" is **exactly the two open `sorry`s** (`zd_cost_not_poly`, `iphd_correspondence_justified`). **See Bridge 2.** |
| **VDIS channels** (rotor/torsion §3.4, 360-orthogonal, Möbius, bunny channel-set) | decision-heuristic perturbation channels over the tangent state | the channel/mirror-descent machinery is real and was built + tested | across VDIS v1–v8 the honest survivors are all **classical** (degree, Lagrange λ, prime symmetry-break, mirror-descent combiner); the rotor/torsion channel self-extinguished by construction. |

## Bridge 1 — cone order = stabilizer order = the G₂/symmetry channel

The orbifold design's "normal-form multiplicity indexed by local **cone
order**" is not a separate idea from the Lie telos. An orbifold cone point of
order `k` *is* a point whose local isotropy group has order `k`; the multiplicity
of normal forms there is governed by that stabilizer's representation theory.
That is **the same object** as the automorphism group Γ whose irreducibles
block-diagonalize the rank-deficiency operator `M_d` (`RUNG2_LIE_TELOS_NOTE.md`):
the "channels" are the isotypic components, and over ℝ this is the
G₂-adapted / symmetry-adapted SOS decomposition. So the orbifold-computer
picture and the symmetry-SOS lever are two descriptions of one structure — and
the honest, executable home for both is the **ℝ-side Γ-block-diagonalized moment
matrix** (still the standing "next build").

## Bridge 2 — the sedenion clock is the aspiration; NS-degree is its scoped realization

`L63_HypercomplexTime` wants "zero-divisor cost is not polynomial" to be a
hardness theorem. The rigorous, executable form of "zero-divisor cost" is the
**Nullstellensatz degree = rank-deficiency of `M_d`** (`RUNG2_ALGEBRAIC_NOTE.md`)
— the operator's own instinct, made computable. What today's double-check
establishes is precisely the honest boundary the two `sorry`s hide:

- the zero-divisor/NS obstruction is **real and intrinsic**, but it is a carrier
  for the *Nullstellensatz* system only — **incomparable** to resolution/CDCL
  hardness. Witnesses: PHP has NS 4 > width 2; **Tseitin K₄ has NS 3 < width 4**.
- so "`2^(n/7)` ⇒ SAT is hard" does **not** follow from the algebra: the algebra
  fact (7 octonionic units, zero divisors at level 4) is true, but the step to a
  *SAT search-cost* bound is exactly what is unproven — and Tseitin shows the
  algebraic degree can sit *below* the resolution obstruction. The clock names a
  real obstruction; it does not clock SAT.

## Net

Two of the five designs (orbifold, sedenion clock) are genuinely the same
program as the ladder, seen from the computer-architecture side — and both point
at the *same two* honest next objects: the ℝ-side symmetry-adapted moment matrix
(Bridge 1) and the already-built NS-degree/rank-deficiency invariant with its
now-corrected scope (Bridge 2). The other three (Berry-braid = BQP, symplectic
RAM = reversible = classical-poly, VDIS channels = classical survivors) are real
computational models that do **not** give an NP shortcut, and their Lean
`abbrev`-equivalences assert names, not theorems. Nothing here is discarded —
the exceptional structure is real throughout; it just names hard objects rather
than cheapening them, which is the ladder's recurring result.
