#!/usr/bin/env python3
"""Search for T ∈ 𝕆 (Fin 8 → ℝ) such that:
1. (T,T,T) ≠ 0 (non-associative)
2. T*T ≠ T (not idempotent)
3. The halting set {s | T*s = s} is nontrivial (many fixed points, > 1)
4. The halting set is NOT a subalgebra (closure fails)

We use the Cayley-Dickson multiplication implemented in VDIS.
"""

import sys
sys.path.insert(0, '/Users/jesusvilelajato/lambda-sat-solver')

from LambdaSatSolver.VDIS.Algebra.CD import mulByLevel, associator

def mul3(a, b, c):
    """Compute (a,b,c) = (ab)c - a(bc) at level 3."""
    return mulByLevel(3, mulByLevel(3, a, b), c) - mulByLevel(3, a, mulByLevel(3, b, c))

def count_fixed_points(T):
    """Count fixed points s where T*s = s, with s in {-1,0,1}^8."""
    count = 0
    fixed = []
    for s0 in (-1, 0, 1):
        for s1 in (-1, 0, 1):
            for s2 in (-1, 0, 1):
                for s3 in (-1, 0, 1):
                    for s4 in (-1, 0, 1):
                        for s5 in (-1, 0, 1):
                            for s6 in (-1, 0, 1):
                                for s7 in (-1, 0, 1):
                                    s = [s0, s1, s2, s3, s4, s5, s6, s7]
                                    result = mulByLevel(3, T, s)
                                    if result == s:
                                        count += 1
                                        fixed.append(tuple(s))
    return count, fixed

def is_subalgebra(T):
    """Check if the halting set is closed under multiplication."""
    count, fixed = count_fixed_points(T)
    if count <= 1:
        return True  # trivial or empty halting set is always a subalgebra
    
    # Pick two distinct fixed points and check if their product is also fixed
    for i in range(min(10, len(fixed))):
        for j in range(i+1, min(10, len(fixed))):
            p = mulByLevel(3, fixed[i], fixed[j])
            if p not in fixed:
                return False
    return True

# Search systematically
def search():
    """Search over all T with entries in {-1, 0, 1}."""
    results = []
    
    # Enumerate all 3^8 = 6561 possible T
    from itertools import product
    
    for t_vals in product((-1, 0, 1), repeat=8):
        T = list(t_vals)
        
        # Check 1: (T,T,T) ≠ 0
        a = mulByLevel(3, mulByLevel(3, T, T), T)
        b = mulByLevel(3, T, mulByLevel(3, T, T))
        assoc = [a[i] - b[i] for i in range(8)]
        if all(x == 0 for x in assoc):
            continue  # skip associative T
        
        # Check 2: T*T ≠ T
        TT = mulByLevel(3, T, T)
        if TT == T:
            continue  # skip idempotent T
        
        # Check 3 & 4: count fixed points
        count, fixed = count_fixed_points(T)
        if count > 1:  # nontrivial
            is_sub = is_subalgebra(T)
            if not is_sub:
                results.append((T, count, is_sub))
    
    return results

print("Searching for non-quine universal T in 𝕆...")
print("Enumerating all 3^8 = 6561 possible T with entries in {-1,0,1}")
print()

results = search()

print(f"Found {len(results)} candidates:")
print()

for i, (T, count, is_sub) in enumerate(results[:20]):
    T_str = " ".join(f"{v:+d}" for v in T)
    print(f"T{i+1}: [{T_str}]")
    print(f"  Halting set size: {count} (nontrivial ✓)")
    print(f"  Is subalgebra: {is_sub} (NOT ✓)" if not is_sub else f"  Is subalgebra: {is_sub} (FAIL)")
    print()
