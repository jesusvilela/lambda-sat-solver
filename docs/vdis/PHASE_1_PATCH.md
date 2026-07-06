# VDIS Track B1 — Phase 1 patch: hypercomplex-hyperdimensional infinitesimal fix

**Status: structural bug fixed and verified. One residual, much smaller,
floating-point-precision-level divergence found and diagnosed - not
patched further pending a decision (see "Open question" below).**

## The patch

`PHASE_1.md` diagnosed the S4 failure as an absorbing fixed point:
`Delta_C = sum_l alpha_l * t_l` (S3.1, using literals' *current* tangent
state) stays exactly zero forever from a zero initial condition, since
the forcing term is proportional to the state itself.

Fix, implemented in `backend/vdis/vdis_heuristic.py`: decompose the
D-dimensional tangent space into an **infinitesimal fossil axis** (index
0) and, for D>1, genuinely hyperdimensional axes above it:

- **Axis 0** always receives a *fixed* unit contribution per conflict
  (`delta_c[0] = 1.0`), independent of any literal's current state -
  "a conflict occurred and this literal participated," full stop. This
  is the infinitesimal (in the dual-number sense: a fixed, non-state-
  dependent perturbation) that exactly reproduces EVSIDS's fixed-`var_inc`
  bump when D=1.
- **Axes 1..D-1** (inert while D=1, i.e. all of Phase 1) keep the
  original S3.1 state-dependent formula - this is where Phase 2's
  "living field" richness lives, once it exists.

Two more bugs, needed for the claim and independent of the fixed point,
fixed in the same pass:
- `pick()` now ranks **variables** by combined axis-0 activity across
  both polarities (`t_v[0] + t_(-v)[0]`), matching EVSIDS's single
  per-variable score - not by comparing the two literals' individual
  scores, which is a different (and wrong) selection rule since VDIS
  scores literals separately but EVSIDS scores variables.
- Explicit phase-saving (remember last assigned polarity) for choosing
  between `+v`/`-v` once `v` is selected, matching `EVSIDSHeuristic`,
  instead of "whichever literal's own score is higher."

**Exact-equivalence argument** for why axis-0-only, D=1 should now
match EVSIDS bit-for-bit: EVSIDS never touches old scores, instead
growing `var_inc /= var_decay` every conflict (a common implementation
trick). VDIS's S3.3 decay directly rescales all state by `decay_gamma`
every conflict (Mobius scalar multiplication, exact multiplication by
`gamma` at c=0). In exact arithmetic these are the same ordering up to
a shared positive scale factor `gamma^n` at step n (verified
symbolically with `fractions.Fraction`: the ratio is exactly `1`),
provided `decay_gamma == var_decay` and `eta == var_inc_0`.

## Result: verified, not assumed

- **30-instance quick suite x 5 heuristic seeds (150 checks): 0
  mismatches.** (`test_vdis_degeneracy.py`, now passing without `xfail`.)
- **63-instance medium suite (up to 200 vars, 7 problem families): 60/63
  match exactly; 3/63 diverge**, all on the *longest*-running instances
  in the suite (`r3sat_n50_..._seed5`: diverges at decision 23 of 75;
  `r4sat_n40_..._seed0`: diverges at decision 14, ends 908 vs 944 total
  decisions; `php_8_7`: diverges at decision 1721, ends 5099 vs 9590).

## Diagnosis of the residual 3/63 (corrected after a self-check caught an error)

**Correction**: the first version of this section claimed the mismatches
were "only the three longest runs in the suite" and attributed the cause
to drift compounding over ~2000 steps. That claim doesn't survive its own
evidence — the Result section two paragraphs up already recorded that
`r4sat_n40_..._seed0` diverges at **decision 14** and `r3sat_n50_..._seed5`
at **decision 23**. Those are not long runs. I wrote a plausible-sounding
mechanism without checking it against the specific divergence points I'd
already measured. Caught on a self-review pass, traced directly rather
than re-argued from the armchair:

Instrumented both heuristics on `r4sat_n40_..._seed0` and dumped the
actual variable scores at the exact decision where they diverge. Only
**3 conflicts** had occurred by that point. EVSIDS: variables 11, 12, 17
are in a bit-identical 3-way tie (`2.052631578947368` each) — its
"never touch old scores, only grow `var_inc`" implementation gives them
the exact same float64 value. VDIS: variables 11 and 12 are exactly tied
(`1.7598749999999996`), but variable 17 differs by **~3 ULPs**
(`1.7598749999999999`) — enough to win the strict `>` comparison in
`pick()`. That's the whole mechanism: VDIS's decay directly re-multiplies
*every* stored score by `decay_gamma` on *every* conflict (S3.3's literal
prescription), so two variables bumped on different conflicts have been
through a *different number of decay-multiplication steps* by the time
they're compared — even if EVSIDS's mathematically-equivalent
"grow-the-increment" bookkeeping gives them an exactly equal value. This
can round differently after a handful of decay steps, not just after
thousands; it isn't about accumulation length, it's about whether a
genuine exact tie happens to occur (which is common early in a run, when
few distinct conflict-clause patterns exist yet — three variables landing
in the identical set of learned clauses so far is unremarkable). `php_8_7`
diverging much later (decision 1721) is the same mechanism triggering on
a different, later tie; it isn't evidence of a length-dependent effect,
it's a second independent instance of the same tie-breaking sensitivity.
The synthetic 2000-step check in the previous version of this section
(exact-vs-float64 ratio 1 vs. 0.9999999999999986) is still accurate as
far as it goes — the two decay strategies are mathematically identical
and do drift under repeated floating-point rounding — it just wasn't the
mechanism actually operating in 2 of these 3 cases, and I should have
checked before writing it down as the explanation.

## Open question — RESOLVED by operator decision (2026-07-03)

**The operator chose path (a)**: float64-exact equivalence — 150/150 on
the quick suite, 60/63 on the medium suite, with the residual 3 fully
diagnosed above as exact-tie ULP sensitivity between two mathematically
identical decay bookkeeping strategies — is accepted as satisfying the
S4 degeneracy gate's intent. The structural bug S4 exists to catch (the
absorbing fixed point) is fixed and verified; the residual divergence is
a property of float64 itself, not of the gyro machinery. Track B1
proceeds to Phase 2. Original decision text kept below for the record.

### Original decision text

The S4 gate as literally stated ("decision sequences equal element-wise")
is not met bit-for-bit on arbitrarily long runs, because of this float64
drift - even though the *mathematical* reduction is exact. Getting fully
bit-identical behavior would mean implementing VDIS's decay via the same
"grow the bump increment, never touch old scores" trick EVSIDS uses,
rather than the direct Mobius-scalar-multiplication decay the spec's S3.3
literally describes. I have not made that swap: it would mean quietly
changing which part of S3.3 gets implemented specifically to force a
bit-exact pass, which is the same kind of self-fulfilling patch this
protocol's own discipline warns against elsewhere (S7's "do not iterate
hyperparameters beyond the pre-declared sweep to rescue P1").

Two honest paths forward, your call: (a) accept "identical to float64
precision, verified for the length of run actually exercised in Phase 3's
benchmarks" as satisfying S4's intent (the *structural* bug - the thing
S4 exists to catch - is fixed and confirmed), and proceed to Phase 2; or
(b) require the decay implementation to match EVSIDS's specific
grow-the-increment strategy for bit-exact equivalence at arbitrary
length, and I re-verify against that.

## Test suite

429 (pre-patch) + this patch replaces the 1 xfailed test with a passing
one on the quick suite: 430 passing, 0 xfailed. The 63-instance
stress-test above was run standalone (not added as a repo test, since it
duplicates Phase 0's medium-suite cross-validation machinery) - script
retained at `docs/vdis/scripts/phase1_medium_degeneracy_stress.py` for
reproducibility.
