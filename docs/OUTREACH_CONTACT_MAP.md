# Outreach contact map

This file is a practical map for the private pre-launch sanity-check round. It deliberately avoids copying raw email addresses into the public repository. Use the linked official pages / GitHub profiles to contact people through their preferred public channel.

## Priority rule

Contact **3 people first**, not 20:

1. Mate Soos — CryptoMiniSat / XOR / Gaussian baseline sensitivity.
2. Marijn J. H. Heule — DRAT/proof-checking/certified SAT language.
3. Armin Biere — Kissat/CaDiCaL/CDCL baseline and SAT-solver framing.

Randal Bryant is excellent but should usually be Wave 1.5 or routed via the proof/certification angle after the first note is polished.

## Wave 1 — highest-signal contacts

| Person | Public route | GitHub / project handle | Why they matter | Exact ask |
|---|---|---|---|---|
| Mate Soos | Blog / GitHub profile / CryptoMiniSat repo | `msoos`, `msoos/cryptominisat` | CryptoMiniSat is the sensitive baseline because CMS has XOR/Gaussian machinery. If the parity-frame language sounds like "we beat CMS", he is the person most likely to detect the overclaim. | "Is the CMS comparison fair, especially flags/version/framing around XOR/Gaussian reasoning?" |
| Marijn J. H. Heule | Official CMU page; GitHub profile / DRAT-trim repo | `marijnheule`, `marijnheule/drat-trim` | Proof logging/checking, DRAT, SAT proof credibility. He is the cleanest sanity check for the certification language. | "Is the SAT model replay / UNSAT frame-or-DRAT wording accurate, or should it be phrased differently?" |
| Armin Biere | Official academic page; GitHub profile / Kissat / CaDiCaL repos | `arminbiere`, `arminbiere/kissat`, `arminbiere/cadical` | Kissat/CaDiCaL are key CDCL baselines; Biere is also central to SAT tooling and proof-producing solver culture. | "Are the baseline flags, proof-command assumptions, and aggregate comparison fair?" |
| Randal E. Bryant | Official CMU page | public CMU page; coauthor with Soos/Heule on proof-generating BDD/SAT work | Strongest bridge for parity + proof-generation + BDD/extended-resolution perspective. | "Does the parity proof/certification boundary look technically honest?" |

## Wave 2 — portfolio / benchmark etiquette

| Person/group | Public route | Why they matter | Exact ask |
|---|---|---|---|
| Tomas Balyo | Academic search / publications / SAT competition ecosystem | HordeSat, portfolio SAT, SAT competition context. | "Does the seed-diversified portfolio framing report CPU cost, launch overhead, and scope fairly?" |
| Carsten Sinz / Peter Sanders | HordeSat author line / Karlsruhe academic pages | Portfolio SAT lineage. | "Is the portfolio comparison framed in a way SAT people would recognize as fair?" |
| Gilles Audemard / Laurent Simon / Daniel Le Berre | CRIL / SAT competition / SAT Heritage public pages | Benchmark and solver-ecosystem discipline. | "Is the benchmark presentation acceptable, or socially noisy?" |
| Mathias Fleury | GitHub / academic page / CaDiCaL-proof ecosystem | Current proof-producing SAT / LRAT / Gimsatul-adjacent work. | "Is the proof-producing-solver and certification wording current?" |

## Wave 3 — proof-complexity / encodings / hardness framing

| Person | Why they matter | Exact ask |
|---|---|---|
| Alexey Ignatiev | PySAT / MaxSAT / explainability via SAT / formal encodings. | "Does the proof-complexity / hardness-carrier framing look misleading?" |
| Antonio Morgado | MaxSAT / SAT encodings / proof-complexity-adjacent work. | "Are the PHP / counting / resolution references too informal?" |
| Joao Marques-Silva | GRASP, SAT, MaxSAT, formal reasoning, rigorous explanations. | "Is this framed as a useful SAT contribution or as avoidable noise?" |
| Vijay Ganesh / Curtis Bright | SAT for hard combinatorial problems and solver engineering. | "Does the structured-combinatorial benchmark framing look useful?" |

## Suggested first three messages

### Mate Soos

Subject: Scoped CryptoMiniSat comparison — sanity check request

Core sentence:

> CryptoMiniSat is the most sensitive baseline here because the parity frame overlaps with CMS's XOR/Gaussian strengths. I want to avoid implying that the middleware generally outperforms CMS; the claim should be limited to the included mix and to cases where routing decides before CDCL.

Ask:

> Where does the CMS comparison look unfair, misleading, or too strong?

### Marijn Heule

Subject: SAT certification wording — sanity check request

Core sentence:

> The repo's credibility depends on the proof-checking language being exact. I currently say SAT is model-replayed and UNSAT is either frame-sound or DRAT-checked.

Ask:

> Is that wording accurate enough, or should the project speak differently around DRAT/LRAT/FRAT and proof checking?

### Armin Biere

Subject: Kissat/CaDiCaL baseline framing — sanity check request

Core sentence:

> Kissat and CaDiCaL are used as respected external engines/baselines, not as trusted authorities. The project tries to route structured regions before CDCL and then certify the fallback result.

Ask:

> Are the baseline flags, proof-command assumptions, and aggregate comparison fair, or am I abusing defaults / benchmark framing?

## Channel discipline

- Prefer direct professional email where the person publishes one on an official page.
- Use GitHub issues only if the question is genuinely repo-specific and respectful of maintainer time.
- Do not open an issue titled anything like "lambda-sat beats CMS".
- Do not mass-message. Send 3 notes, wait, then adjust.
- If someone corrects the framing, patch the repo and credit the correction only if they explicitly agree.

## Evidence anchors already checked

- `msoos/cryptominisat` exists and is owned by GitHub user `msoos`.
- `arminbiere/kissat` and `arminbiere/cadical` exist and are owned by GitHub user `arminbiere`.
- `marijnheule/drat-trim` exists and is owned by GitHub user `marijnheule`.
- Marijn Heule's official CMU page lists SAT solving, proof logging/checking, DRAT, and contact information.
- Armin Biere's official page lists SAT/SMT solver work, Kissat/CaDiCaL-adjacent software ecosystem, and contact information.
- Randal Bryant's official CMU page lists his public contact route and his formal verification / BDD background.

## Minimum viable first wave

Send only these three:

1. Mate Soos — CMS comparison fairness.
2. Marijn Heule — proof/certification wording.
3. Armin Biere — CDCL/Kissat/CaDiCaL baseline fairness.

Then wait 7–10 days before any public launch.