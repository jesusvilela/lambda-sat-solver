"""Hard certification smoke test for CI (the `certification-hard` lane).

Unlike the unit lane -- which skips gracefully when Kissat/drat-trim are absent -- this
script REQUIRES them and fails red if the certification path does not actually execute:

  1. Kissat and drat-trim must be on PATH (else exit 1).
  2. A CDCL UNSAT verdict must be replayed and accepted by drat-trim (a real DRAT check).
  3. A CDCL SAT verdict must be replayed against the formula (a real model check).

Both instances are plain 3-CNF with no frame structure, so they are decided by the CDCL
engine + certification, not by a self-certifying frame -- this exercises exactly the path
the unit lane is allowed to skip. Exit 0 only if both certifications ran and passed.
"""

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.cnf_utils import CNFFormula                # noqa: E402
from backend.metasolver import _certified_cdcl          # noqa: E402


def _fail(msg: str) -> None:
    print(f"CERTIFICATION LANE FAILED: {msg}")
    sys.exit(1)


def main() -> None:
    for tool in ("kissat", "drat-trim"):
        if shutil.which(tool) is None:
            _fail(f"{tool} is not on PATH; the certification lane requires it")

    # All 8 clauses over 3 variables exclude all 8 assignments -> UNSAT, and it carries
    # no 2-SAT / parity / counting structure, so it is refuted by CDCL + a DRAT proof.
    unsat = CNFFormula(3, [[a, b, c] for a in (1, -1) for b in (2, -2) for c in (3, -3)])
    status, _t, verified = _certified_cdcl(unsat, "kissat", 10.0)
    if status != "UNSAT":
        _fail(f"expected UNSAT on the 8-clause formula, got {status}")
    if not verified:
        _fail("UNSAT verdict was NOT DRAT-certified (drat-trim did not run/accept)")
    print("ok: CDCL UNSAT replayed and accepted by drat-trim")

    sat = CNFFormula(3, [[1, 2, 3], [-1, -2, 3], [1, -2, -3]])
    status, _t, verified = _certified_cdcl(sat, "kissat", 10.0)
    if status != "SAT":
        _fail(f"expected SAT on the satisfiable formula, got {status}")
    if not verified:
        _fail("SAT model was NOT verified against the formula (model replay failed)")
    print("ok: CDCL SAT model replayed against the formula")

    print("CERTIFICATION LANE PASSED: DRAT UNSAT + model-replay SAT both executed.")


if __name__ == "__main__":
    main()
