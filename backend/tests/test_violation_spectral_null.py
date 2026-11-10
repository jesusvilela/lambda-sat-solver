"""Centered finite overlap has gauge-invariant cycle signs and null controls."""
import math
import numpy as np
import pytest
from backend.violation_spectral_null import (
    centered_incidence, _correlations, _triangle_stats)


def test_centered_constant_rows_drop():
    assert centered_incidence((0, 0), (1,), 1).variable_checks == 0
    assert centered_incidence((1, 1), (1,), 1).variable_checks == 0


def test_independent_binary_checks_decorrelated():
    # Both checks are balanced and independent over all four possible patterns.
    cor = _correlations(((0, 0, 1, 1), (0, 1, 0, 1)))
    assert np.allclose(cor, np.eye(2))
    assert math.isclose(float(np.linalg.eigvalsh(cor)[-1]), 1.0)


def test_complementary_rows_negative_correlation_gram_psd():
    cor = _correlations(((0, 1, 0, 1), (1, 0, 1, 0)))
    assert np.allclose(cor, np.array([[1, -1], [-1, 1]]))
    # Nonnegative power iteration starting at all-ones would incorrectly get zero.
    assert math.isclose(float(np.linalg.eigvalsh(cor)[-1]), 2.0)


def test_triangle_product_is_invariant_under_row_orientation():
    bits = np.array([[0, 0, 0, 1, 1, 1, 1, 0],
                     [0, 0, 1, 1, 1, 0, 0, 1],
                     [1, 1, 0, 1, 0, 0, 1, 0]], dtype=int)
    cor = _correlations(bits)
    flipped = bits.copy()
    flipped[0] = 1 - flipped[0]
    flipped[2] = 1 - flipped[2]
    cor2 = _correlations(flipped)
    assert np.allclose(cor2, cor * np.outer(np.array([-1, 1, -1]),
                                           np.array([-1, 1, -1])))
    f, m = _triangle_stats(cor, threshold=0)
    f2, m2 = _triangle_stats(cor2, threshold=0)
    assert math.isclose(f, f2)
    assert math.isclose(m, m2)


def test_explicit_negative_cycle_has_frustration_one():
    c = np.array([[1, .5, -.5], [.5, 1, .5], [-.5, .5, 1]])
    f, m = _triangle_stats(c)
    assert f == 1.0 and math.isclose(m, .125)
    assert min(np.linalg.eigvalsh(c)) >= -1e-9


def test_centered_one_clause_and_bounded_errors():
    result = centered_incidence((1, 2, 3), (1, 2), 2)
    assert result.variable_checks == 2
    assert 0 <= result.mean_absolute_correlation <= 1
    assert 0 <= result.largest_eigenvalue_per_check <= 1
    with pytest.raises(ValueError):
        centered_incidence((4,), (1,), 2)
    with pytest.raises(ValueError):
        centered_incidence((1,), tuple([1] * 65), 2)
    with pytest.raises(ValueError):
        _correlations(((1, 1, 1),))
