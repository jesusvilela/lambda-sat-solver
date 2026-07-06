# Combining ascendency + nudges "into Garrabrant" — assessment

Operator question: "what if we combine ascendancy and other nudges into
garrabant?" Assessment only — not built (n=13 is exhausted; this needs
pre-registration at ~50 instances/family). Third time Garrabrant has
come up; this framing is genuinely new and gets a fresh read.

## The clean split (real vs vocabulary)

**REAL and, in fact, the natural synthesis of everything that survived
five generations:** an *online ensemble* of nudge-traders, each
proposing a per-variable score adjustment, aggregated by
multiplicative weights that update from a measured reward, *within each
solve*. Traders = the surviving mechanisms as independent experts:
  - κ-shaped living-field activity (biggest lever),
  - pair-θ polarity-disagreement (v3),
  - precessing-prime tie preference (v4/MF3),
  - ascendency-gated overhead (below).
Reward signal already exists: `on_conflict` delivers LBD every conflict
(confirmed in refsolver) — a trader that steered recent decisions toward
low-LBD (tight, reusable) learned clauses gets its weight raised;
Hedge/EXP3 update. This is standard adaptive-heuristic territory
(LRB-vs-VSIDS switching, bandit portfolios) and is a legitimate v6-class
hypothesis.

**VOCABULARY, the same conclusion as the two prior Garrabrant passes:**
the *distinctively* Garrabrant machinery — a market over sentences whose
truth is undecided, priced to be inexploitable by every poly-time trader
via LIA market-clearing — is not affordable and not necessary here.
VDIS is already 15–19× EVSIDS per the S3.7 budget; a market-clearing
fixed point per decision is orders of magnitude past that. What you would
actually ship is the reward-attribution online learner, i.e. Hedge/EXP3,
credited to the bandit/online-learning literature, not to logical
induction.

## What IS new in this framing (and why it's not the old dismissal)

The two earlier passes dismissed "bandit over a config grid" (offline,
exhaustively sweepable in 858 s — a bandit only adds variance). This is
different: per-*decision* claims with *deferred* payoff revealed only as
search unfolds. "Is v a good decision now?" is genuinely a claim whose
truth arrives later — the one structural feature logical induction is
actually built around. So the inspiration is fair even though the
mechanism (LIA) is not imported. The honest object is: online experts,
deferred reward, weight update. Name it that.

## The genuinely good sub-idea: ascendency as the overhead gate

Ascendency failed as a κ-rule (ASCENDENCY.md), but its live use lands
exactly here. The reframing already established: EVSIDS = maximal
ascendency (channelized), VDIS living field = overhead (reserve). So use
per-instance α = A/C not to pick κ but to set **how much weight the nudge
ensemble gets at all**:
  - high α (structured, e.g. pigeonhole) → collapse toward the
    channelized core; nudges near-muted (they only ever hurt php),
  - low α (diffuse, e.g. random 3-SAT) → let the ensemble breathe
    (where VDIS's measured 8–9/13 wins live).
This is a *selective-overhead* heuristic — the exact forward hypothesis
ASCENDENCY.md named — with ascendency supplying the missing "when."
The user's instinct connects two threads that were already pointing the
same way.

## Why it's allowed under no-rescue, and the discipline that still binds

An online combiner tunes *within* a solve; it is a heuristic design, not
cross-benchmark hyperparameter iteration, so it does not violate the
no-rescue rules (which forbid re-fitting the grid to rescue a failed
prediction between runs). BUT: it must be pre-registered as its own
protocol with fresh instances, or the extra adaptivity makes it trivially
unfalsifiable. And the binding constraint from v5 stands: at n=13 the
seed lottery exceeds every mechanism effect measured in the track,
including v5's pass. A combiner tested at n=13 would measure noise.

## Disposition

Parked, not built. If pursued, the pre-registration writes itself:
traders = {κ-activity, θ, primes, ascendency-gate}; aggregator = Hedge on
LBD reward; α sets ensemble weight; arbiter = fresh instances,
≥50/family; primary = beat EVSIDS win-count AND aggregate (the track has
never taken the aggregate — php is the wall); ablate each trader; credit
online-learning, cite logical induction as inspiration only. That is a
next-session build.
