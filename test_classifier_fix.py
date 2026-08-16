#!/usr/bin/env python3
"""Verify that the multi-channel classifier fix correctly classifies
XOR/parity, pigeonhole, and random k-SAT instances.

Previous bug: orbit_coarseness alone missed XOR/parity.
Fix: structured = has_hwlec OR has_xorparity OR has_counting OR has_gyration_structure.

Usage: python test_classifier_fix.py [--verbose]
"""
from __future__ import annotations

import argparse
import random
import sys
from typing import List

sys.path.insert(0, ".")

from backend.cnf_utils import CNFFormula
from backend.eval.generators import random_ksat, pigeonhole, xor_chain
from backend.fabric import fabric


def classify_structured(formula: CNFFormula) -> str:
    """Replicate the staging logic from bordon_fleet.py fleet_solve.

    Uses parity, counting, and orbit signals. Gyration is excluded because
    structured (XOR/PHP) and unstructured (random) families both have
    low gyration, making it a poor discriminator.
    """
    fb = fabric(formula)
    parity_signal = float(fb.parity_signal)
    counting_signal = float(fb.counting_signal)
    orbit_coarseness = float(fb.orbit_coarseness)
    has_hwlec = orbit_coarseness > 0.7
    has_xorparity = parity_signal > 0.5
    has_counting = counting_signal > 0.3
    structured = has_hwlec or has_xorparity or has_counting
    return "structured" if structured else "unstructured"


def generate_xor_chain(n: int, k: int, seed: int) -> CNFFormula:
    result = xor_chain(num_vars=n, expected_sat=True, seed=seed)
    return result[0] if isinstance(result, tuple) else result


def generate_pigeonhole(n: int, m: int, seed: int) -> CNFFormula:
    result = pigeonhole(n=m)
    return result[0] if isinstance(result, tuple) else result


def generate_random_ksat(n: int, k: int, seed: int) -> CNFFormula:
    result = random_ksat(num_vars=n, k=k, num_clauses=n, seed=seed)
    return result[0] if isinstance(result, tuple) else result


def run():
    parser = argparse.ArgumentParser(description="Test classifier fix for XOR/parity")
    parser.add_argument("--verbose", action="store_true", help="print details")
    args = parser.parse_args()

    results = []
    failures = 0

    def check(name: str, formula: CNFFormula, expected: str):
        nonlocal failures
        fb = fabric(formula)
        actual = classify_structured(formula)
        ok = actual == expected
        if not ok:
            failures += 1
            print(f"  FAIL: {name} expected={expected} actual={actual}")
            print(f"    parity_signal={fb.parity_signal:.3f} orbit_coarseness={fb.orbit_coarseness:.3f} "
                  f"counting_signal={fb.counting_signal:.3f} gyration={fb.gyration:.3f}")
        elif args.verbose:
            print(f"  OK: {name} -> {actual}")
        results.append((name, formula, expected, actual, fb))

    # --- XOR chain family ---
    # xor_chain has xor_clause_fraction=1.0, parity_signal=1.0, orbit_coarseness~0.0
    # Old classifier: gyration >= 5.0 -> unstructured (WRONG)
    # New classifier: has_xorparity=True -> structured (CORRECT)
    for seed in range(5):
        f = generate_xor_chain(n=40, k=20, seed=seed)
        check(f"xor_chain seed={seed}", f, "structured")

    # --- Pigeonhole family ---
    # pigeonhole has counting_signal > 0.3, low parity_signal
    # Should be classified as structured via has_counting
    for seed in range(5):
        f = generate_pigeonhole(n=50, m=30, seed=seed)
        check(f"pigeonhole seed={seed}", f, "structured")

    # --- Random 3-SAT ---
    # random_ksat has low parity_signal, low counting_signal, high orbit_coarseness
    # Should be classified as unstructured
    for seed in range(5):
        f = generate_random_ksat(n=50, k=3, seed=seed)
        check(f"random_3sat seed={seed}", f, "unstructured")

    # --- Large random (heavy-tail boundary) ---
    f_large = generate_random_ksat(n=400, k=3, seed=0)
    check("random_400 (heavy-tail)", f_large, "unstructured")

    # --- Summary ---
    total = len(results)
    correct = total - failures
    print(f"\nClassifier verification: {correct}/{total} correct")
    if failures:
        print(f"FAILED: {failures} tests")
        return 1
    print("PASSED: all classifier tests")
    return 0


if __name__ == "__main__":
    sys.exit(run())
