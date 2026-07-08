# Saddle-point view — its real content and its honest boundary

Prompted by the "hardness as an n-dim saddle point" framing and
own `SaddleInterspace.lean`. Two findings, one refining the other.

## What the saddle view gets right (within a family)

The violated-clause energy landscape's **barrier structure** — the saddle
E* a local search must climb to connect solution basins
(`energy_landscape_saddle`) — is real and measurable, and it tracks
3-SAT hardness better than raw cluster count (rank-corr +0.40 vs +0.20,
n=18 SAT regime; modest/underpowered but in the predicted direction).
This is the instance-level image of the free-energy saddle whose change
of character is the SAT phase transition (Mézard–Parisi–Zecchina). It is
genuinely a *local-search* hardness signal.

## Where it honestly breaks (across problem types) — the guiding insight, verified

`SaddleInterspace.lean §4`: "XOR is MORE rugged than SAT yet is in P via
its gate. Ruggedness does not imply hardness; the separator is gate
existence." Verified computationally (`saddle_ruggedness_vs_gate.py`,
n=16, α=4.25):

| family | max barrier | complexity |
|---|---|---|
| 3-SAT | 0–1 (smooth) | NP-complete |
| 3-XOR | 16–21 (brutal) | **P** (Gaussian elimination) |

XOR-SAT's landscape is savagely more rugged than 3-SAT's, yet Gaussian
elimination over GF(2) decides it in polynomial time — the ruggedness is
irrelevant to its complexity. So the saddle/landscape geometry is **not**
the P-vs-NP separator. **Schaefer's dichotomy (1978)** is: the separator
is the algebraic gate / polymorphism (XOR passes the affine gate; 3-SAT
passes none).

## The honest synthesis (where saddle work touches live theory)

- Saddle/landscape ruggedness → a real **local-algorithm** hardness
  signal within a family. The rigorous current form is the **Overlap Gap
  Property** (Gamarnik et al.): a landscape obstruction that *provably*
  blocks local/stable algorithms — but only that class, which is exactly
  why XOR (rugged, but cracked by the non-local Gaussian gate) is not a
  counterexample to OGP, only to "ruggedness ⇒ hardness" naively.
- P-vs-NP-relevant separation → **algebraic** (Schaefer / the CSP
  dichotomy, Bulatov–Zhuk), not geometric.

The saddle intuition was not wrong; it was precisely scoped by the
the XOR counterexample. That scoping is the result.
