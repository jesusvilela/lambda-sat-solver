# proofs/ — formal proof obligations (external instrument)

Per `docs/CHARTER.md`, Lean is used here as an **external instrument**, never a
repository dependency: these files are self-contained and mathlib-free, they are
*not* part of the Python build or test suite, and no Lean toolchain is vendored.
The Lean **compiler** is the trusted arbiter — *a name is not a proof* — so a
theorem in this directory counts as established **only once it compiles**.

## Contents

- `XorSoundness.lean` — the soundness of the GF(2)/XOR refutation used by
  `backend/xor_extraction.py::gf2_xor_refutation` (and the UNSAT branch of
  `gf2_xor_solve`): if some XOR-combination of the recovered parity constraints
  is the contradiction `0 = 1`, then no assignment satisfies all of them, so the
  formula is UNSAT. This is the principle Gaussian elimination exploits.

## Status — READ THIS

`XorSoundness.lean` is a **DRAFT proof obligation, NOT yet compiler-verified.**
It was authored in an environment with **no Lean toolchain**, where the
toolchain download is blocked by egress policy (github release assets return
403). The proof is written carefully and is believed correct, but *belief is not
proof* — until it compiles it must be treated as an obligation, not a fact.

## To verify (seconds, needs only a bare `lean`)

```bash
# with elan/lean installed locally:
lean proofs/XorSoundness.lean        # exit 0 = all theorems check

# or hand it to Leanstral / Mistral Vibe:
vibe --agent lean                    # then ask it to check/complete the file
```

If it compiles clean, update this section to "VERIFIED with Lean <version>" and
the draft header in the `.lean` file accordingly. If it does not, the compiler
error is the honest record of what still needs fixing.
