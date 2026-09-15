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

---

## 6. Additional Falsification Conditions

### GF(2,2) Algebra (GF22.lean)

| Theorem | Falsification Condition |
|---------|------------------------|
| `mul_invariant` | If x ≠ 0, there exists y such that x*y = 1. Counterexample: check if any non-zero element lacks an inverse. |
| `add_self_eq_zero` | x + x = 0 for all x. Counterexample: find any x where x + x ≠ 0. In char 2, this should always hold. |
| `sub_eq_add` | x - y = x + y. Counterexample: find any x, y where x - y ≠ x + y. In char 2, this should always hold. |
| `frobenius_add` | (x + y)² = x² + y². Counterexample: find any x, y where (x + y)² ≠ x² + y². In char 2, Frobenius should hold. |
| `omega_sq` | ω² = ω + 1. Counterexample: compute ω² and check if it equals ω + 1. |
| `omega_cube` | ω³ = 1. Counterexample: compute ω³ and check if it equals 1. |

### GF(16) Multiknob (GF22Multiknob.lean)

| Theorem | Falsification Condition |
|---------|------------------------|
| `j_squared` | k² = 1. Counterexample: compute mul(encode zero one, encode zero one) and check if it equals one. |
| `not_a_domain` | There exist non-zero x, y such that x*y = 0. Counterexample: find any pair of non-zero elements whose product is zero. |
| `associator_nonzero` | There exist x, y, z such that (xy)z ≠ x(yz). Counterexample: try basis elements 1, j, ω. |
| `exists_nontrivial_halting` | There exists T with >1 fixed point. Counterexample: find any T with exactly 1 fixed point. |
| `every_element_is_a_plus_bj` | Every element can be written as a + bj. Counterexample: find any element that cannot be decomposed. |

### GF(16,16) Superior Lift (GF22MultiknobLevel2.lean)

| Theorem | Falsification Condition |
|---------|------------------------|
| `k_squared` | k² = 1. Counterexample: compute mul(encode zero one, encode zero one) and check if it equals one. |
| `not_a_domain` | There exist non-zero x, y such that x*y = 0. Counterexample: find any pair of non-zero elements whose product is zero. |
| `even_mul_closed` | Even elements are closed under multiplication. Counterexample: find even elements whose product is odd. |
| `associator_nonzero` | There exist x, y, z such that (xy)z ≠ x(yz). Counterexample: try basis elements 1, k, ω from GF(16). |
| `exists_nontrivial_halting` | There exists T with >1 fixed point. Counterexample: find any T with exactly 1 fixed point. |
| `every_element_is_a_plus_bk` | Every element can be written as a + bk. Counterexample: find any element that cannot be decomposed. |

### Turing/Halting (TuringHalting_LeanLake.lean, AcafQuine.lean)

| Theorem | Falsification Condition |
|---------|------------------------|
| `haltingSet_e1_eq_zero` | The halting set of e₁ is {0}. Counterexample: find any non-zero element in the halting set. |
| `trivial_quine` | 0 is a quine. Counterexample: check if 0*0 = 0 (it should, but verify). |
| `hybrid_not_idempotent` | hybridProgram * hybridProgram ≠ hybridProgram. Counterexample: find if it is idempotent. |
| `hybrid_nontrivial_halting` | hybridProgram has nontrivial halting set. Counterexample: find if it has only 1 fixed point. |
| `hybrid_not_subalgebra` | The halting set is not a subalgebra. Counterexample: find two fixed points whose product is not fixed. |
| `hybrid_nonassoc` | The associator of hybridProgram is non-zero. Counterexample: compute associator(hybrid, hybrid, hybrid) and check if it's zero. |
| `hybrid_is_acaf_quine` | hybridProgram is an ACAF quine. Counterexample: show it doesn't satisfy the ACAF quine conditions. |
| `hybrid_actor_gap_nonzero` | actorGap(hybridProgram) ≠ 0. Counterexample: compute actorGap and check if it's zero. |

### Quine Family (QuineFamily.lean)

| Theorem | Falsification Condition |
|---------|------------------------|
| `family_in_tangent_screen` | Each family member is in the tangent screen. Counterexample: find a k where familyMember k ∉ tangentScreen. |
| `family_not_idempotent` | Each family member is not idempotent. Counterexample: find a k where familyMember k * familyMember k = familyMember k. |
| `family_nontrivial_halting` | Each family member has nontrivial halting. Counterexample: find a k with only 1 fixed point. |
| `family_not_subalgebra` | Each family member's halting set is not a subalgebra. Counterexample: find a k where the halting set is closed under multiplication. |
| `family_nonassoc` | Each family member has non-zero associator. Counterexample: find a k where associator(familyMember k, familyMember k, familyMember k) = 0. |
| `family_is_acaf_quine` | Each family member is an ACAF quine. Counterexample: show any family member doesn't satisfy ACAF quine conditions. |
| `family_card` | There are exactly 7 family members. Counterexample: find any duplicate or missing member. |
| `family_members_distinct` | All 7 family members are distinct. Counterexample: find k ≠ ℓ where familyMember k = familyMember ℓ. |

### Hypercomplex Mind Games (HypercomplexMindGames.lean)

| Theorem | Falsification Condition |
|---------|------------------------|
| `ij_eq_k` | qi * qj = qk. Counterexample: compute qi * qj and check if it equals qk. |
| `ji_eq_negk` | qj * qi = -qk. Counterexample: compute qj * qi and check if it equals -qk. |
| `order_holonomy` | qi * qj ≠ qj * qi. Counterexample: find if they commute (they shouldn't). |

### Visibility Field (VisibilityField.lean)

| Theorem | Falsification Condition |
|---------|------------------------|
| `backbone_card` | The structural backbone has cardinality 3. Counterexample: count the elements and show it's not 3. |
| `visibilityFieldCD_zero` | visibilityFieldCD n r = 0.0 for n ≥ 3. Counterexample: find any n ≥ 3, r where it's not zero. |

### IG Bundle (IGBundle.lean)

| Theorem | Falsification Condition |
|---------|------------------------|
| `σ307_nonneg` | σ307 T1 T2 ≥ 0 for all T1, T2. Counterexample: find any T1, T2 where σ307 < 0. |
| `transfer_invariant` | σ307 T T = σ307 (hyperbolicSwap T) (hyperbolicSwap T). Counterexample: find any T where this fails. |

### Tangent Holographic Screen (TangentHolographicScreen.lean)

| Theorem | Falsification Condition |
|---------|------------------------|
| `family_in_screen` | All family members are in the tangent screen. Counterexample: find any k where familyMember k ∉ tangentHolographicScreen. |
| `screen_is_translate` | tangentHolographicScreen = {v | v 0 = 0.0} + {fun _ => 1.0}. Counterexample: find any vector in the screen that doesn't match this form. |
| `screen_is_hyperplane` | Same as screen_is_translate. Counterexample: find any vector in the screen that doesn't match this form. |

### Dirac (Dirac.lean)

| Theorem | Falsification Condition |
|---------|------------------------|
| `inner_symm` | inner x y = inner y x. Counterexample: find any x, y where this fails (it should always hold). |

### Turing Halting Master (TuringHalting_Master.lean)

| Theorem | Falsification Condition |
|---------|------------------------|
| `bool_not_fixed_point_of_not` | !b ≠ b for all b. Counterexample: find any b where !b = b (this should never happen). |

### General Hardening Checklist

For every theorem in the project, apply:

- [ ] Can I compute a concrete counterexample?
- [ ] Does the proof use `native_decide` on finite types? (If so, it's verifiable)
- [ ] Does the proof use `sorry`? (If so, it's a placeholder)
- [ ] Does the proof use circular reasoning? (Check that hypotheses aren't derived from the conclusion)
- [ ] Is the theorem falsifiable? (Can I state what would make it false?)
- [ ] Is there independent evidence? (Not just the proof itself)
