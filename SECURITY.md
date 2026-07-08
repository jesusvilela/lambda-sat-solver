# Security policy

This is a research library and CLI, not a network service. Its security surface is
unusual and worth stating plainly: the project's core promise is **soundness** — that a
verdict it certifies is correct. The most serious class of defect here is therefore not a
memory-safety bug but a **soundness bug**: a formula reported `SAT`/`UNSAT` (with
`certified = True`) whose verdict is wrong.

## Trusted computing base

By design, the external SAT solver (Kissat) is **not trusted**. Every verdict is
re-checked by a small, independent core:

- SAT — the model is replayed against the original formula (`cnf_utils.verify_model`);
- UNSAT via a frame — sound by construction (2-SAT SCC, GF(2) refutation, counting bound);
- UNSAT via CDCL — the DRAT proof is replayed by `drat-trim` (LRAT optional).

A bug in Kissat, CaDiCaL, or CryptoMiniSat that produced a wrong answer would be **caught**
by this core, not trusted. A soundness-relevant bug is therefore one in the trusted core
itself (parser, Tseitin transform, model checker, the frame refutations, or the proof-checker
invocation).

## Reporting a vulnerability

Please report privately rather than in a public issue:

- Use **GitHub Security Advisories** ("Report a vulnerability") on this repository, or
- email the maintainer via the address on the GitHub profile of the repository owner.

Please include a minimal reproducing formula and the observed vs expected verdict. A
witnessed soundness violation (a certified-but-wrong verdict) will be treated as the
highest priority.

## Supported versions

The project is pre-1.0; fixes land on the default branch. Pin a commit for reproducibility.
# Security Policy

Please do **not** report security issues through public GitHub issues, discussions, or pull requests.

This repository is a research SAT middleware and benchmarking harness. It shells out to external solver/proof binaries such as Kissat, CaDiCaL, CryptoMiniSat, and `drat-trim`, and it reads attacker-controllable CNF/proof files when you choose to run those inputs.

## Supported versions

The supported branch is `main`.

## Reporting a vulnerability

Report security concerns privately to the maintainer through the contact information listed on the GitHub profile, or through GitHub private vulnerability reporting if it is enabled for this repository.

Please include:

- affected commit, branch, or release;
- affected command or API entry point;
- minimal reproduction input, if safe to share;
- expected impact;
- whether the issue requires untrusted CNF/proof input or a hostile local environment.

## Operational safety

For untrusted inputs, prefer the Docker container or another sandbox. Do not run untrusted CNF/proof corpora with elevated privileges. External solver binaries are outside this project's trusted computing base; this project verifies SAT/UNSAT verdicts, but it does not make external solver processes memory-safe.
