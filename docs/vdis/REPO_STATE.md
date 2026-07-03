# VDIS Track B1 — Phase −1: Repo State Verification

Recorded before any Phase 0 work. All claims below are EMPIRICAL (checked
directly, this session).

## Branch / sync

- Branch: `claude/2026-sota-benchmark-xyp1zh`
- HEAD: `81bd46cf8b5b56da2852a4b7c84bd6fb86c819bf`
- `origin/main` HEAD: `d2d26f7` (merge of PR #14, which carried this
  branch's proof-timeout fix, commit `706f759`)
- `706f759` is an ancestor of HEAD: yes — the proof-timeout fix is merged
  upstream.
- HEAD is 2 commits ahead of `origin/main`, no divergence, no conflicts:
  - `014fe03` — CNF profiling, rule-based policy, certificate statuses
  - `81bd46c` — binary-clause (2-SAT) consistency pre-check
- PR #16 (`copilot/improve-proof-handling`, the empirically-probed Kissat
  flag fix) is confirmed merged and an ancestor of HEAD.

## Prior-session artifact presence

| Artifact | Status |
|---|---|
| `backend/cnf_profile.py` | present |
| `backend/policy.py` | present |
| `backend/binary_clause_check.py` | present |
| Certificate-status enum (`CERTIFICATION_MODES`, `_certificate_status`) | present |
| CPU-aware portfolio default (`max_parallel is None` branch in `portfolio.py`) | present |

Branch confirmed correct. Proceeding.

## Test baseline

`python3 -m pytest backend/tests/ -q` → **247 passed** (matches last known
good count exactly).

## Architectural fact confirmed

Kissat is invoked exclusively via `subprocess.run` in `kissat_wrapper.py`
(`_check_availability`, `solve`, `_probe_flag`) — there is no native CDCL
loop, no in-process solver object, anywhere in `backend/`. Grepped for
`class.*Solver` / `def solve` across `backend/*.py`: matches are
`api_server.py`, `kissat_wrapper.py` (the subprocess wrapper),
`middleware.py` (calls the wrapper), `portfolio.py` (calls the wrapper).
None instrument Kissat's internal decision heuristic. This confirms
§2's premise: VDIS cannot be tested inside Kissat without a C patch, and
`backend/refsolver/` is the correct starting point for Phase 0.

Gate: **passed.** Proceeding to Phase 0.
