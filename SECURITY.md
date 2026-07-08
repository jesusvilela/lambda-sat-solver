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