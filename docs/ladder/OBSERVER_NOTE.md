# The synthetic observer A†, distilled onto tested code

*The operator's ideal synthetic observer
`A† = (Θ, Γ, ∇⁻¹, ∂∞, R, C, E, J)` — "a boundary-conditioned geometric immune
system for thought." The exquisite distillation is not another essay: it is the
recognition that **most of A†'s organs are already this repo's verification
architecture**, plus the two hardening organs (C, E) built here as code.*

## The map (what was already real)

| organ | role | where it already lives, tested |
|---|---|---|
| **Θ** hypercomplex valuation (not a scalar) | judge on many axes at once | `contracts.py`: every claim carries `proven` / `benchmark` / `limit` / `verdict` — never one number. The `ObserverVerdict` here is multi-axis (action · status · certified · ambiguity · coherence). |
| **Γ** semantic gluing / global section | glue local views into one | `frame_solve_coupled` — Nelson–Oppen combination *is* sheaf gluing of local frame verdicts. And `gluing_defect ≡ 0` is a tested theorem: sound frames cannot disagree. |
| **∇⁻¹** drift repair / bounded holonomy | keep meaning stable across a long trace | the CONTRACTS.md doc-sync test + every differential test (`extract_xors` vectorized vs reference, `frame_solve_guided`/`_coupled` vs `frame_solve`) pin the system to a reference so it cannot drift. |
| **∂∞** boundary purpose | asymptotic telos, not step correction | `docs/CHARTER.md`: truthful, bounded, world-contacting; "a name is not a proof." |
| **R** active remainder | carry what the answer did not earn | the ε>0 thread: `lambda_sat.fixpoint_sat.remainder_active`; every contract's `limit`; `CDCL_NEEDED` is an explicit remainder, not a fake answer. |
| **J** adjudicator {accept/repair/abstain/escalate} | four honest moves, not always answer | `observer.adjudicate` → **accept** (a single frame certifies), **repair** (the coupling glues what none saw), **escalate** (nothing does → CDCL + remainder). The three tiers we built, named. |

## The two organs built here (the honest gap)

### C — the ambiguous critic (polysemy, not negation)

`observer.frame_ambiguity` measures how many **sound frames independently
decide** an instance. "The object has more than one valid projection" is literal:

- **PHP(3→2)** is decided by *both* implication (2 holes → all binary) and
  counting — **degree ≥ 2, polysemous.** Do not pretend one frame is *the* frame.
- **Tseitin** is **parity only — degree 1.** Genuinely single-projection.
- a structureless 3-SAT is **degree 0** — no single frame sees it (a coupling/CDCL
  object).

C prevents premature disambiguation: the router's *moving frame* picks the
cheapest single frame, but C records that several may be valid — the honest
counterweight to collapsing a polysemous object to one meaning.

### E — the erroneous observer (structured wrongness = a mutation-testing vaccine)

`observer.ERRONEOUS_OBSERVERS` are four **deliberately unsound "seductive"
mock-frames** — mutants, not noise:

- `overconfident_parity` — cries UNSAT on any dense XOR (ignores whether Gaussian
  actually refutes); wrong on a *satisfiable* parity system.
- `naive_counting` — UNSAT if clauses outnumber variables 2:1 (density monist).
- `literalist_sat` — SAT whenever no empty clause is present (wrong on all of
  Tseitin, PHP, …).
- `metric_monist` — collapses judgment to one clause/variable scalar — the exact
  failure Θ exists to prevent.

The defining invariant — *"A† must be harder to fool than the model it observes"*
— becomes a **passing test**: every mutant is witnessed genuinely unsound, and
our sound adjudicator **kills every one** — wherever a mutant is wrong, the
adjudicator never emits that verdict (it gives the truth or escalates). This is
mutation testing with a brute-force truth oracle: the observer is validated by
the false worlds it refuses.

## Status (Charter labels)

- **Measured / tested** (`test_observer.py`): C's polysemy on PHP/Tseitin/void;
  all four mutants unsound and all killed by the adjudicator over 900 random
  instances; `gluing_defect ≡ 0` (sound frames never disagree); the
  accept/repair/escalate tiers.
- **The honest limit**: this is the observer's *logical* immune system over the
  SAT-frame task class — it does **not** claim Θ's full axis set (relevance,
  beauty, ethical-load), world-contact ν, or the hyperbolic boundary ∂∞ beyond
  the Charter. Per §15 of the operator's derivation, there is **no universal
  replacement** — only bounded observer-bisimulation over a task class `K`. Here
  `K` = "certify a SAT verdict soundly," and over that `K` the organs are real.
- **Lens / open**: the `∇⁻¹` gauge-correction one-form, the hypercomplex `Cl(p,q)`
  valuation as a genuine multivector (we approximate it with a struct of axes),
  and `∂∞` as an actual boundary-at-infinity remain geometric lenses, not yet
  earned frames.

The distilled thesis, in this repo's terms: **the observer is not something we
describe; it is the discipline the code already runs under — verify before trust,
carry the remainder, and be harder to fool than what you observe.** C and E make
the last clause testable.
