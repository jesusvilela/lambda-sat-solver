---
title: "Benchmark capsule"
---

# Benchmark capsule

Every number here is a **measured** claim on a small, fixed, synthetic mix — **not** the SAT
Competition set, and **not** a claim of general CDCL dominance. Numbers are hardware-sensitive
(wall-clock, core count); regenerate on your machine. Commands and pinned versions:
[REPRODUCIBILITY.md](https://github.com/jesusvilela/lambda-sat-solver/blob/main/REPRODUCIBILITY.md).

## Setup

| | |
|---|---|
| **engines** | Kissat 4.0.4 · CaDiCaL 3.0.0 · CryptoMiniSat 5.14.7 (pycryptosat) |
| **families** | random-3SAT (α≈4.26) · Tseitin/XOR · XORSAT · pigeonhole (PHP) · mixed |
| **timeout** | 20 s (main mix) · 30 s (random-3SAT tail study) |
| **hardware** | 4 vCPU dev container (portfolio numbers are core-bound) |
| **metric** | solved-count and PAR-2 (timeout counts as 2×) |
| **certification** | every middleware verdict: SAT model-replayed, UNSAT frame-sound or DRAT |

## Main mix — frame-aware middleware vs raw CDCL and CMS

`python -m docs.ladder.scripts.metasolver_benchmark` · 40 instances · 20 s

| family | n | Kissat | CaDiCaL | CryptoMiniSat | **middleware** |
|---|---|---|---|---|---|
| random-3SAT | 9 | 9/9 · 0.12 s | 9/9 · 0.13 s | 9/9 · 0.18 s | 9/9 · 0.23 s |
| Tseitin (parity) | 9 | 5/9 · 18.98 s | 5/9 · 18.83 s | 9/9 · 0.95 s | **9/9 · 0.00 s** |
| XORSAT | 12 | 12/12 · 0.00 s | 12/12 · 0.00 s | 12/12 · 0.00 s | 12/12 · 0.00 s |
| PHP (counting) | 4 | 3/4 · 10.77 s | 4/4 · 0.12 s | **2/4 · 24.51 s** | **4/4 · 0.00 s** |
| mixed | 6 | 6/6 · 0.00 s | 6/6 · 0.00 s | 6/6 · 0.00 s | 6/6 · 0.01 s |
| **total** | 40 | 35/40 · 5.38 s | 36/40 · 4.28 s | 38/40 · 2.71 s | **40/40 · 0.05 s** |

CryptoMiniSat is the strongest baseline (38/40): its Gaussian engine **owns parity** (9/9
Tseitin, where the raw CDCL engines get 5/9). It carries **no counting engine**, so
pigeonhole is exponential for it (php10/php12 time out) while the counting frame is instant.

## Random-3SAT tail — the honest tunnel

`python -m docs.ladder.scripts.metametasolver_benchmark` · n=220–280 · 30 s

| solver | solved | PAR-2 (wall) |
|---|---|---|
| single Kissat (1 core) | 15/16 | ~5.3 s |
| CryptoMiniSat (1 core) | 14/16 | 10.01 s |
| fractal portfolio (~nproc cores) | 15/16 | 6.22 s — beats CMS wall-clock on 13/16 |

The portfolio's advantage over CMS is a **parallel, mixed-strategy** effect (heavy-tailed
runtime collapsed by diversified seeds), paid for in `k×` CPU. On few cores it shrinks. It is
**not** a smarter search, and it does **not** beat a single strong Kissat by much on this box.

## What improves

- **Counting**: instant certified refutation where CDCL and CMS are exponential (PHP).
- **Parity**: instant certified verdict; even CMS's Gaussian engine is matched or beaten in
  wall-clock by the direct GF(2) refutation.
- **Aggregate PAR-2 on this mix**: dominated by the structured families the frames own.

## What does **not** improve

- **Random-3SAT**: no exposed frame; the middleware falls to CDCL and is only *comparable* —
  CMS is competitive-to-faster there. This is CDCL's territory and stays that way.
- **Single-thread on obfuscated structure**: if the XOR/counting structure is hidden from the
  cheap detectors, the frame does not fire.
- **Trivial instances under certification**: the DRAT proof of a trivial CDCL UNSAT can cost
  more than the solve — an uncertified solver returns faster. That is the price of proof, and
  it is intentional.

## One-line reading

> On a mix that includes the counting and parity fragments, certified frame routing decides
> the structured islands instantly and provably, and hands the unstructured tail to CDCL. The
> advantage is structural and scoped — not a generally faster SAT solver.
