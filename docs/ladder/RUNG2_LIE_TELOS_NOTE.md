# The Lie-algebra telos of the zero-divisor lift — where it is real, where it isn't

The thread: *"manipulating those channels to precisely chase the
pertaining lifting, with Lie algebras almost emerging as telos."* This note
follows that arrow to its endpoint honestly — it is a true and beautiful
chain, and it lands exactly on the algebraic obstruction of
`RUNG2_ALGEBRAIC_NOTE.md` (the Nullstellensatz/PC degree = rank deficiency of
`M_d`). It also draws the precise line between where the Lie structure gives a
real computational lever and where it is a real-field object that does not
survive our GF(2) shadow.

## The telos chain (true, and it terminates at an exceptional Lie algebra)

The `immerse → lift → rotate → ground` operator *is*
Cayley–Dickson doubling used as a lift on states ("lift: embed by doubling
scale; rotate: multiply by a symmetry element; ground: compress by half").
Climb that tower — ℝ → ℂ → ℍ → 𝕆 → 𝕊 — and:

1. **Zero divisors are born exactly at the sedenion level 𝕊 (level 4).**
   ℝ, ℂ, ℍ, 𝕆 are composition algebras: no rank collapse. 𝕊 is the first level
   where `a·b = 0` with `a, b ≠ 0` — the algebraic birth of the very
   "directional collapse / rank deficiency" identified in the source and that
   we made executable as the cokernel of `M_d`.
2. **The symmetry of that collapse is exceptional-Lie.** `Der(𝕆) = 𝔤₂`, the
   14-dimensional exceptional simple Lie algebra; and (Moreno 1998) the
   unit-norm zero divisors of 𝕊 form a space homeomorphic to `G₂`. So the
   zero-divisor variety — the algebraic home of the obstruction — literally
   carries a `G₂` action. The Lie algebra is not decoration bolted on; it is
   the symmetry group of the collapse. That is why "chasing the lifting" up the
   channels makes a Lie algebra emerge as telos.

This is the honest vindication of the octonion→sedenion "circumvent"
trajectory: it was reaching for real, exceptional structure, and that structure
is precisely the symmetry of the obstruction we now compute.

## The executable contract — and the char-2 fork

Is there an input→invariant→action→benchmark contract, or is this only
beautiful? There is one, and it is exact:

**The rank-deficiency operator `M_d` commutes with the formula's automorphism
group Γ.** Hence Γ's orbits/irreps are literally "the channels," and the
certificate can be chased channel by channel. Over ℝ this is the standard
symmetry-adapted SOS / moment-matrix block-diagonalization
(Gatermann–Parrilo 2004): `M_d` splits into isotypic blocks indexed by Γ's
irreducibles, each far smaller, and Γ's Lie algebra is the infinitesimal
generator of those blocks. This is exactly how pigeonhole-type degree bounds
are made tractable and tight. The "channels" are real and the "Lie algebra as
telos" is literally how the computation is organized.

**But our NS-degree lives over GF(2), and characteristic 2 obstructs the clean
decomposition.** Tested on PHP(3→2) (Γ = S₃ × S₂, |Γ| = 12) in
`docs/ladder/scripts/symmetry_channel_ns.py`:

| degree d | symmetric-channel basis rows | 1 reachable? |
|---|---|---|
| 0–2 | 0 | no |
| 3–6 | 1 | no |

The symmetric channel **never reaches 1**, while the true NS degree is 4. And
this is a *theorem*, not an artifact: the orbit-symmetrization operator
`Σ_{γ∈Γ} γ` acts on any Γ-invariant vector as multiplication by `|Γ|`; since
`2 | |Γ|` this is `0`, so it **annihilates the entire invariant subspace** — and
the target `1` lives in that subspace. The naive symmetry channel therefore
*provably* cannot reach `1` whenever `2 | |Γ|`.

## The honest verdict

- The Lie-algebra telos is **real and correctly identified**: `𝔤₂ = Der(𝕆)` and
  the `G₂` zero-divisor space (Moreno) are the genuine symmetry of the collapse;
  the symmetry-channel block-diagonalization of `M_d` is a real, standard lever
  **over ℝ** (Gatermann–Parrilo), the natural home of "manipulate the channels
  to chase the lifting."
- It is a **real-field object**. Its clean GF(2) image is char-2 obstructed —
  and that obstruction is exactly why the pigeonhole principle is a canonical
  hard case for *algebraic* proof systems in characteristic 2, and why a naive
  symmetry reduction cannot cheapen the NS degree there. Realizing the channel
  reduction over GF(2) needs modular representation theory (the trivial module
  is not a summand of `F₂[Γ]`), not averaging.
- So the productive next home for this thread is the **real moment/SOS matrix**
  with Γ-block-diagonalization — where the Lie structure is a genuine
  computational win — not another GF(2) symmetrization. That is a real, large,
  standard rung, and it is the one the telos language and the
  symmetry-SOS literature climb together.

No overclaim: this settles *where* the Lie-algebra telos has teeth (ℝ-side
symmetry-adapted SOS on the same rank-deficiency operator) and proves *why* the
GF(2) shortcut collapses. The geometry named the obstruction and its exceptional
symmetry exactly; it did not hand us a free certificate.
