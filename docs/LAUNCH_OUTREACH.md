# Launch outreach shortlist

Purpose: avoid a cold public launch into silence by running a small adversarial sanity-check round before announcement.

The ask is **not**: "please review my whole repo" or "look, I beat your solver".

The ask is:

> I am preparing a scoped release of a certified SAT middleware. Please tell me where the benchmark framing, proof/certification language, or solver comparison is unfair, misleading, or too strong.

## Launch posture

- Lead with certification and scoped routing, not dominance.
- Treat Kissat / CaDiCaL / CryptoMiniSat as respected baselines or external engines, not opponents.
- Keep the core claim classical: implication / 2-SAT, parity / GF(2), counting / pigeonhole, then certified CDCL fallback.
- Keep the geometry as the second layer, not the first-contact hook.
- Invite correction. Do not ask for endorsement.

## Wave 0 — before contacting anyone

Required public surfaces:

- `README.md` scoped benchmark wording.
- `PUBLIC_RESEARCH_CLAIMS.md` as claim ledger.
- `REPRODUCIBILITY.md` as exact reproduction discipline.
- `docs/ladder/README.md` with width vs Nullstellensatz marked incomparable.
- CI with a hard certification lane.

Optional but strongly recommended:

- one benchmark capsule table: family, instance count, timeout, engines, result, caveat;
- one short command that reproduces a small benchmark in minutes;
- one 2–4 page technical note.

## Wave 1 — highest-value sanity checks

| Candidate | Why | Ask | Tone |
|---|---|---|---|
| Mate Soos | CryptoMiniSat; XOR/Gaussian reasoning is the most sensitive baseline for the parity-frame claim. | Is the CMS comparison fair? Are CMS flags/version/framing appropriate? Does the parity/XOR claim overstate anything? | Deferential, precise, no "beat CMS" framing. |
| Armin Biere | Kissat / CaDiCaL / proof-producing SAT ecosystem; relevant to CDCL baseline and proof-producing solvers. | Is the fallback / baseline / proof-command framing fair? Are we abusing solver defaults? | Ask for correction, not validation. |
| Marijn J. H. Heule | DRAT / DRAT-trim / verified SAT proof ecosystem. | Is the certification language accurate? Should the repo speak DRAT/LRAT/FRAT differently? | Proof-checking precision. |
| Randal E. Bryant | Co-author on proof generation for CDCL + Gauss-Jordan elimination with CMS. | Does the parity proof/certification boundary look right? | Narrow and technical. |

## Wave 2 — benchmark and portfolio sanity checks

| Candidate | Why | Ask | Tone |
|---|---|---|---|
| Tomas Balyo | Parallel/portfolio SAT solving, SAT competition context. | Does the portfolio/metametasolver framing report CPU cost and heavy-tail scope fairly? | Portfolio not dominance. |
| Carsten Sinz / Peter Sanders | HordeSat and portfolio SAT lineage. | Same: portfolio framing, CPU-cost accounting, benchmark etiquette. | Historical lineage. |
| Gilles Audemard / Laurent Simon / Daniel Le Berre | SAT competition / solver ecosystem / reproducibility / SAT Heritage. | Is the benchmark presentation acceptable to SAT community expectations? | Benchmark discipline. |
| Mathias Fleury | Proof-producing SAT, Gimsatul/LRAT ecosystem. | Is the proof-producing-solver comparison and certification wording current? | Proof engineering. |

## Wave 3 — proof-complexity / hardness framing

| Candidate | Why | Ask | Tone |
|---|---|---|---|
| Alexey Ignatiev | SAT/MaxSAT/proof-complexity-adjacent work; PySAT ecosystem. | Does the resolution-width / hardness-carrier framing look misleading? | Correct my claim boundary. |
| Antonio Morgado | MaxSAT/SAT encodings, proof-complexity-adjacent work. | Same; especially PHP / MaxSAT / resolution limits. | Narrow. |
| Joao Marques-Silva | SAT, MaxSAT, formal reasoning; senior perspective. | Is the problem framing publishable or socially noisy? | Respectful and concise. |
| Vijay Ganesh / Curtis Bright | SAT for hard combinatorial problems, MapleSAT/CnC ecosystem. | Is the structured-combinatorial benchmark framing useful? | Applied SAT angle. |

## Initial message template

Subject: Scoped SAT middleware benchmark — sanity check request

Hi [Name],

I am preparing a small release of a certified SAT middleware, and I would value a sanity check on the benchmark framing before I overstate anything.

The core idea is not to replace CDCL. The middleware first tries three sound algebraic frames — implication / 2-SAT, parity / GF(2), and counting / pigeonhole-style refutation — then falls back to external CDCL engines. SAT verdicts are model-replayed; UNSAT verdicts are either frame-sound or DRAT-checked.

[CryptoMiniSat / Kissat / CaDiCaL / drat-trim] is treated as [an external engine / a baseline / part of the proof-checking path], not as a trusted authority. The measured claim is scoped: structured frame-decidable regions can be removed before CDCL, producing aggregate wins on the included benchmark mix. I am explicitly not claiming general CDCL dominance.

What I would most appreciate is correction on one question:

Where does this framing look unfair, misleading, or too strong from your perspective?

Repo: https://github.com/jesusvilela/lambda-sat-solver
Repro notes: REPRODUCIBILITY.md
Claim ledger: PUBLIC_RESEARCH_CLAIMS.md

Best,
Jesús

## Candidate-specific one-line substitutions

### Mate Soos

Replace the bracket paragraph with:

> CryptoMiniSat is the most sensitive baseline here because the parity frame overlaps with CMS's XOR/Gaussian strengths. I want to avoid implying that the middleware generally outperforms CMS; the claim should be limited to the included mix and to cases where routing decides before CDCL.

### Armin Biere

> Kissat and CaDiCaL are used as external engines/baselines. I want to make sure the solver flags, proof-command assumptions, and aggregate comparison do not misrepresent what CDCL is doing.

### Marijn Heule

> The repo's credibility depends on the proof-checking language being exact. I currently say SAT is model-replayed and UNSAT is frame-sound or DRAT-checked; I would value correction if this should be phrased differently around DRAT/LRAT/FRAT.

### Portfolio / heavy-tail people

> The meta-metasolver is a seed-diversified portfolio on heavy-tailed instances. I want to make sure CPU cost, launch overhead, and scope are stated in the way portfolio-SAT people expect.

### Proof-complexity people

> The research layer treats resolution width and Nullstellensatz degree as distinct, incomparable hardness carriers. I would value correction if the framing is too informal or if the examples are poorly chosen.

## Public launch only after

- at least one correction from Wave 1, or
- no replies after 7–10 days plus one internal benchmark-capsule cleanup.

Public launch order:

1. GitHub release `v0.1.0`.
2. Short technical note.
3. LinkedIn post focused on "verify the verdict".
4. Optional SAT/Formal Methods community post.

## Anti-patterns

Do not write:

- "I beat CryptoMiniSat."
- "New SAT solver outperforms SOTA."
- "Hyperbolic SAT geometry solves hardness."
- "Please review my repo."

Do write:

- "Certified frame-first SAT middleware."
- "Structured regions before CDCL; CDCL fallback elsewhere."
- "Scoped benchmark mix, not general dominance."
- "Please tell me where the claim boundary is wrong."