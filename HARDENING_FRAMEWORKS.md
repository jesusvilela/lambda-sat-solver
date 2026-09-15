# Hardening Frameworks: Doubt the Machine + Post-Singleton RSI

## Overview

This document describes how to apply two external research frameworks to harden
the lambda-sat-solver project:

1. **[Doubt the Machine](https://github.com/jesusvilela/doubt-the-machine)** —
   A verification framework for using AI without being fooled
2. **[Post-Singleton RSI](https://github.com/jesusvilela/post-singleton-rsi)** —
   A falsifiable theory of recursive self-improvement beyond the singleton

---

## 1. Doubt the Machine: Verification Gate for AI-Assisted Proofs

### Application to Lambda-Sat-Solver

The lambda-sat-solver project uses AI-assisted theorem proving. Doubt the
Machine provides a 5-question gate that should be applied to every theorem
before accepting it as verified:

```
1. CLAIM      What exactly is being claimed?
2. FAILURE    What is one plausible way it could be wrong?
3. EVIDENCE   What evidence is meaningfully independent of the model?
4. TEST       What is the cheapest test that could falsify it?
5. REVERSAL   If I am wrong, can I undo the decision cheaply?
```

### Applying to Current Theorems

| Theorem | Claim | Failure Mode | Test |
|---------|-------|--------------|------|
| `associator_nonzero` | Associator at level 2 is non-zero | The witness might not actually be non-zero | Compute associator(1, k, ω) explicitly |
| `exists_nontrivial_halting` | There exists T with >1 fixed point | Identity element might not have 256 fixed points | Count fixed points of `one` explicitly |
| `CayleyDicksonRecurrenceLow` | Recurrence formula for levels 1-3 | The formula might be wrong for level 2 or 3 | Test with concrete values in GF(16) and GF(16,16) |
| `σ_external_invariant` | Human recognition doesn't imply external verification | The proof might be circular | Check if the proof uses `ExternallyVerified` from `HumanRecognized` |

### Three Surfaces to Doubt

#### Doubt the Machine (AI Author)

- The AI-generated proofs should not be trusted without verification
- Apply Rule 0: "apply this framework to itself"
- For code proofs: run the actual Lean code to verify it compiles and the theorem holds

#### Doubt the Bits (Information)

- Generated proofs may contain unsourced assumptions
- Check that all definitions are properly unfolded
- Verify that `native_decide` and `dec_trivial` actually run on the finite types

#### Doubt the Build (Execution)

- The build is currently failing for CD.lean — this must be fixed before theorems can be verified
- Run `lake build` regularly to ensure all theorems compile
- Use `lean --verify` to check theorem axioms

### Falsification Strategy

For each theorem in lambda-sat-solver, apply the "DOUBT → MEASURE → TEST → REVERT → REPEAT" cycle:

```
DOUBT:  Does this theorem rest on an unexamined assumption?
MEASURE: Can I compute a concrete counterexample?
TEST:   Does the computation fail?
REVERT: If the theorem is wrong, can I revert to a previous state?
REPEAT: Fix and re-verify.
```

### Integration with Lean

The lambda-sat-solver already has verification infrastructure. Enhance it with:

1. **Pre-commit hooks** that run `lake build` to ensure all theorems compile
2. **Theorem verification** using `lean --verify` to check axioms
3. **Automated testing** for the finite-type theorems using `native_decide`
4. **Falsification tests** that search for counterexamples using `dec_trivial`

---

## 2. Post-Singleton RSI: Recursive Improvement Framework

### Application to Lambda-Sat-Solver

The lambda-sat-solver project is itself a recursive improvement system:
- Theorems are proved (improved from `True` placeholders)
- The Cayley-Dickson tower is extended (GF(2,2) → GF(16) → GF(16,16))
- The README is enhanced (improved documentation)
- Build errors are fixed (improved code)

Post-Singleton RSI provides a framework to measure this improvement:

### The Closure Ladder

Apply the closure ladder to the lambda-sat-solver project:

| Level | Description | Lambda-Sat-Solver Status |
|-------|-------------|--------------------------|
| `human_led_baseline` | Pure human effort | Initial state (many sorries) |
| `singleton_agent` | Single AI agent | Current state (AI-assisted proofs) |
| `homogeneous_multi_agent` | Multiple agents with same architecture | Not yet implemented |
| `heterogeneous_ecology` | Distributed ecology with verifiers | Future goal |

### Capability Profile

Track improvement across dimensions (not just one scalar):

```
K_t = (theorem_verification, code_compilation, documentation_quality,
       build_success, algebra_coverage, holonomy_understanding, ...)
```

### Recursive Cycle

The lambda-sat-solver follows this cycle:

```
Propose change (new theorem, fix, enhancement)
  -> Verify candidate (build, test, review)
  -> Select (keep if verified)
  -> Commit (merge to main)
  -> Evaluate on held-out tasks (peer review, build status)
  -> State_1 (next version)
  -> Repeat using state_1 machinery
```

### Falsification Patterns

The post-singleton hypothesis is weakened if:

1. **No closure**: The improvement loop doesn't actually improve anything
   - Fix: Build metrics that show improvement over time

2. **False gains**: Apparent improvement is due to exogenous factors (e.g., more compute)
   - Fix: Track compute/human/time spent

3. **No inheritance**: Later cycles don't benefit from earlier changes
   - Fix: Ensure each cycle builds on the previous state

4. **Coordination overhead**: Improvements are canceled by overhead
   - Fix: Measure overhead separately

### Application to Current State

| Dimension | Current Value | Measurement |
|-----------|---------------|-------------|
| Theorems verified | 47+ | Count `theorem` declarations without `sorry` |
| Build status | Broken (CD.lean) | `lake build` exit code |
| Documentation | 1869 lines | README word count |
| Algebra coverage | GF(2,2), GF(16), GF(16,16) | Algebra files |
| Holonomy | Level 2 non-zero | `associator_nonzero` theorem |

---

## 3. Integration: Hardening Lambda-Sat-Solver

### Immediate Actions

#### 1. Fix the Build

Apply "Doubt the Build" to the current broken state:

```bash
# Verify current state
lake build 2>&1 | grep "error:" | wc -l
# Expected: 0

# If non-zero, apply the 5-question gate:
# 1. CLAIM: What is the build error?
# 2. FAILURE: Could the error be a false positive?
# 3. EVIDENCE: Is there independent verification?
# 4. TEST: Does reverting the change fix it?
# 5. REVERSAL: Can we revert safely?
```

#### 2. Verify Each Theorem

For each theorem, apply the verification cycle:

```lean
-- Example: verify associator_nonzero
theorem associator_nonzero : ∃ (x y z : Fin 256), associator x y z ≠ zero := by
  -- DOUBT: Could this be false?
  -- TEST: Find concrete x, y, z
  refine ⟨encode one zero, encode zero one, encode (fromPair 0 1) zero, ?_⟩
  -- MEASURE: Compute the associator
  native_decide
  -- REVERT: If wrong, revert to previous state
```

#### 3. Document Falsification Conditions

For each theorem, document:

```markdown
## Falsification

This theorem would be falsified if:
- [ ] The witness doesn't actually satisfy the condition
- [ ] The computation shows associator = 0
- [ ] A simpler counterexample exists
```

### Medium-Term Actions

#### 4. Implement Automated Verification

Add pre-commit hooks:

```bash
#!/bin/bash
# verify-theorems.sh
lake build 2>&1 | grep "error:" && exit 1
echo "All theorems compile"
```

#### 5. Add Falsification Tests

For finite-type theorems, add explicit falsification tests:

```lean
-- Test: associator_nonzero is falsifiable
example : ¬ ∀ (x y z : Fin 256), associator x y z = zero := by
  -- Find a counterexample using native_decide
  native_decide
```

#### 6. Track Improvement Metrics

Create a metrics dashboard:

| Metric | Current | Target |
|--------|---------|--------|
| Build status | Broken | Fixed |
| Theorems verified | 47 | 54+ |
| Build time | ? | < 5 min |
| Documentation | 1869 lines | 2000+ lines |
| Algebra coverage | GF(2,2), GF(16), GF(16,16) | Full tower |

---

## 4. References

- [Doubt the Machine](https://github.com/jesusvilela/doubt-the-machine)
- [Post-Singleton RSI](https://github.com/jesusvilela/post-singleton-rsi)
- [PRINCIPLES.md](PRINCIPLES.md) — Doubt the Machine principles
- [THEORY.md](THEORY.md) — Post-Singleton RSI theory
- [FALSIFIERS.md](FALSIFIERS.md) — Falsification conditions

## 5. Conclusion

The lambda-sat-solver project can be hardened by applying:

1. **Doubt the Machine** to verify AI-generated proofs
2. **Post-Singleton RSI** to measure recursive improvement
3. **Closure ladder** to assess the maturity of the improvement loop
4. **Falsification tests** to ensure theorems are not vacuously true

Apply the "DOUBT → MEASURE → TEST → REVERT → REPEAT" cycle to every theorem,
and the project will become increasingly robust against false claims.
