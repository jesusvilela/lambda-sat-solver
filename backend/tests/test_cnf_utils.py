"""
Tests for CNF utilities
"""

import pytest
from pathlib import Path
import tempfile
from backend.cnf_utils import (
    CNFFormula,
    DimacsParseError,
    parse_dimacs,
    parse_dimacs_file,
    write_dimacs,
    verify_model,
    parse_model_line,
    format_model
)


class TestCNFFormula:
    """Test CNFFormula data structure"""

    def test_create_cnf_formula(self):
        """Test creating CNF formula"""
        cnf = CNFFormula(num_vars=3, clauses=[[1, 2], [-1, 3], [-2, -3]])
        assert cnf.num_vars == 3
        assert cnf.num_clauses == 3
        assert len(cnf.clauses) == 3

    def test_cnf_to_dict(self):
        """Test conversion to dictionary"""
        cnf = CNFFormula(num_vars=3, clauses=[[1, 2], [-1, 3]])
        d = cnf.to_dict()
        assert d['variables'] == 3
        assert d['num_clauses'] == 2
        assert d['clauses'] == [[1, 2], [-1, 3]]

    def test_empty_formula(self):
        """Test empty formula"""
        cnf = CNFFormula(num_vars=0, clauses=[])
        assert cnf.num_vars == 0
        assert cnf.num_clauses == 0


class TestDIMACSParser:
    """Test DIMACS format parsing"""

    def test_parse_simple_cnf(self):
        """Test parsing simple CNF"""
        dimacs = """
        c Simple formula
        p cnf 3 3
        1 2 0
        -1 3 0
        -2 -3 0
        """
        cnf = parse_dimacs(dimacs)
        assert cnf.num_vars == 3
        assert cnf.num_clauses == 3
        assert [1, 2] in cnf.clauses
        assert [-1, 3] in cnf.clauses
        assert [-2, -3] in cnf.clauses

    def test_parse_with_comments(self):
        """Test parsing with comments"""
        dimacs = """
        c This is a comment
        c Another comment
        p cnf 2 2
        1 0
        -2 0
        """
        cnf = parse_dimacs(dimacs)
        assert len(cnf.comments) == 2
        assert cnf.num_clauses == 2

    def test_parse_without_header(self):
        """Test parsing without p cnf header"""
        dimacs = """
        1 2 0
        -1 0
        """
        cnf = parse_dimacs(dimacs)
        # Should infer num_vars from clauses
        assert cnf.num_vars == 2
        assert cnf.num_clauses == 2

    def test_parse_empty_lines(self):
        """Test parsing with empty lines"""
        dimacs = """
        p cnf 2 2

        1 0

        -2 0
        """
        cnf = parse_dimacs(dimacs)
        assert cnf.num_clauses == 2

    def test_parse_unit_clauses(self):
        """Test parsing unit clauses"""
        dimacs = """
        p cnf 2 2
        1 0
        -2 0
        """
        cnf = parse_dimacs(dimacs)
        assert cnf.clauses == [[1], [-2]]

    def test_parse_long_clause(self):
        """Test parsing long clause"""
        dimacs = """
        p cnf 5 1
        1 -2 3 -4 5 0
        """
        cnf = parse_dimacs(dimacs)
        assert cnf.clauses[0] == [1, -2, 3, -4, 5]

    def test_parse_file(self):
        """Test parsing from file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cnf', delete=False) as f:
            f.write("p cnf 2 2\n1 0\n-2 0\n")
            f.flush()
            filepath = Path(f.name)

        try:
            cnf = parse_dimacs_file(filepath)
            assert cnf.num_vars == 2
            assert cnf.num_clauses == 2
        finally:
            filepath.unlink()


class TestDIMACSWriter:
    """Test DIMACS format writing"""

    def test_write_simple_cnf(self):
        """Test writing simple CNF"""
        cnf = CNFFormula(
            num_vars=3,
            clauses=[[1, 2], [-1, 3], [-2, -3]],
            comments=["Test formula"]
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.cnf', delete=False) as f:
            filepath = Path(f.name)

        try:
            write_dimacs(cnf, filepath)
            content = filepath.read_text()

            assert "c Test formula" in content
            assert "p cnf 3 3" in content
            assert "1 2 0" in content
            assert "-1 3 0" in content
            assert "-2 -3 0" in content
        finally:
            filepath.unlink()

    def test_write_and_read_roundtrip(self):
        """Test write and read roundtrip"""
        original = CNFFormula(
            num_vars=4,
            clauses=[[1, -2], [3, 4], [-1, -3]],
            comments=["Original"]
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.cnf', delete=False) as f:
            filepath = Path(f.name)

        try:
            write_dimacs(original, filepath)
            restored = parse_dimacs_file(filepath)

            assert restored.num_vars == original.num_vars
            assert restored.num_clauses == original.num_clauses
            assert restored.clauses == original.clauses
        finally:
            filepath.unlink()


class TestModelVerification:
    """Test model verification"""

    def test_verify_satisfying_model(self):
        """Test verification of satisfying model"""
        cnf = CNFFormula(num_vars=3, clauses=[[1, 2], [-1, 3], [-2, -3]])
        # Model: x1=True, x2=False, x3=True
        # Clause [1, 2]: 1 is True -> satisfied
        # Clause [-1, 3]: 3 is True -> satisfied
        # Clause [-2, -3]: -2 is True (x2 is False) -> satisfied
        model = {1: True, 2: False, 3: True}
        assert verify_model(cnf, model) is True

    def test_verify_unsatisfying_model(self):
        """Test verification of unsatisfying model"""
        cnf = CNFFormula(num_vars=3, clauses=[[1, 2], [-1, 3], [-2, -3]])
        model = {1: False, 2: False, 3: False}
        # Clause [1, 2] is not satisfied
        assert verify_model(cnf, model) is False

    def test_verify_partial_model(self):
        """Test verification with partial model"""
        cnf = CNFFormula(num_vars=3, clauses=[[1, 2], [-1, 3]])
        # Use a model that definitely satisfies both clauses
        model = {1: True, 3: True}  # x1=T, x3=T
        # Clause [1, 2]: x1 is True -> satisfied
        # Clause [-1, 3]: x3 is True -> satisfied
        result = verify_model(cnf, model)
        assert result is True

    def test_verify_empty_formula(self):
        """Test verification of empty formula (trivially SAT)"""
        cnf = CNFFormula(num_vars=0, clauses=[])
        model = {}
        assert verify_model(cnf, model) is True

    def test_verify_unit_clauses(self):
        """Test verification with unit clauses"""
        cnf = CNFFormula(num_vars=2, clauses=[[1], [-2]])
        model = {1: True, 2: False}
        assert verify_model(cnf, model) is True

        model_bad = {1: False, 2: False}
        assert verify_model(cnf, model_bad) is False

    def test_verify_with_negative_literals(self):
        """Test verification with negative literals"""
        cnf = CNFFormula(num_vars=2, clauses=[[-1, -2]])
        model = {1: False, 2: False}  # Both false, so both negations true
        assert verify_model(cnf, model) is True

        model = {1: True, 2: True}  # Both true, so both negations false
        assert verify_model(cnf, model) is False


class TestModelParsing:
    """Test model parsing from solver output"""

    def test_parse_model_with_v_prefix(self):
        """Test parsing model line with 'v' prefix"""
        line = "v 1 -2 3 0"
        model = parse_model_line(line)
        assert model[1] is True
        assert model[2] is False
        assert model[3] is True

    def test_parse_model_without_v_prefix(self):
        """Test parsing model line without 'v' prefix"""
        line = "1 -2 3 0"
        model = parse_model_line(line)
        assert model[1] is True
        assert model[2] is False
        assert model[3] is True

    def test_parse_empty_model(self):
        """Test parsing empty model"""
        line = "v 0"
        model = parse_model_line(line)
        assert len(model) == 0

    def test_format_model(self):
        """Test formatting model as string"""
        model = {1: True, 2: False, 3: True}
        formatted = format_model(model)
        assert "1" in formatted
        assert "-2" in formatted
        assert "3" in formatted
        assert formatted.endswith(" 0")

    def test_format_and_parse_roundtrip(self):
        """Test format and parse roundtrip"""
        original = {1: True, 2: False, 3: True, 4: False}
        formatted = format_model(original)
        parsed = parse_model_line(formatted)
        assert parsed == original


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_large_variable_numbers(self):
        """Test with large variable numbers"""
        cnf = CNFFormula(num_vars=1000, clauses=[[999, 1000], [-999, -1000]])
        # Clause [999, 1000]: x999 is True -> satisfied
        # Clause [-999, -1000]: -x1000 is True (x1000 is False) -> satisfied
        model = {999: True, 1000: False}
        assert verify_model(cnf, model) is True

    def test_single_variable_formula(self):
        """Test single variable formula"""
        cnf = CNFFormula(num_vars=1, clauses=[[1]])
        model = {1: True}
        assert verify_model(cnf, model) is True

    def test_contradictory_unit_clauses(self):
        """Test contradictory unit clauses"""
        cnf = CNFFormula(num_vars=1, clauses=[[1], [-1]])
        model = {1: True}
        assert verify_model(cnf, model) is False

        model = {1: False}
        assert verify_model(cnf, model) is False

    def test_tautological_clause(self):
        """Test clause with complementary literals"""
        # Note: [1, -1] is a tautology and should always be satisfied
        cnf = CNFFormula(num_vars=1, clauses=[[1, -1]])
        model = {1: True}
        assert verify_model(cnf, model) is True

        model = {1: False}
        assert verify_model(cnf, model) is True


class TestStrictDIMACSParser:
    """Strict (TCB-grade) DIMACS validation"""

    def test_valid_strict(self):
        cnf = parse_dimacs("p cnf 3 2\n1 2 0\n-1 3 0", strict=True)
        assert cnf.num_vars == 3
        assert cnf.clauses == [[1, 2], [-1, 3]]

    def test_missing_header_rejected(self):
        with pytest.raises(DimacsParseError):
            parse_dimacs("1 2 0", strict=True)

    def test_duplicate_header_rejected(self):
        with pytest.raises(DimacsParseError):
            parse_dimacs("p cnf 2 1\np cnf 2 1\n1 2 0", strict=True)

    def test_malformed_header_rejected(self):
        with pytest.raises(DimacsParseError):
            parse_dimacs("p cnf 2\n1 2 0", strict=True)

    def test_non_integer_header_rejected(self):
        with pytest.raises(DimacsParseError):
            parse_dimacs("p cnf two 1\n1 2 0", strict=True)

    def test_negative_header_counts_rejected(self):
        with pytest.raises(DimacsParseError):
            parse_dimacs("p cnf -2 1\n1 2 0", strict=True)

    def test_wrong_clause_count_rejected(self):
        with pytest.raises(DimacsParseError):
            parse_dimacs("p cnf 2 3\n1 2 0\n-1 0", strict=True)

    def test_variable_out_of_range_rejected(self):
        with pytest.raises(DimacsParseError):
            parse_dimacs("p cnf 2 1\n1 5 0", strict=True)

    def test_non_integer_clause_token_rejected(self):
        with pytest.raises(DimacsParseError):
            parse_dimacs("p cnf 2 1\n1 x 0", strict=True)

    def test_unterminated_clause_rejected(self):
        with pytest.raises(DimacsParseError):
            parse_dimacs("p cnf 2 1\n1 2", strict=True)

    def test_empty_clause_preserved(self):
        # Empty clause makes the formula trivially UNSAT
        # and must not be silently dropped
        cnf = parse_dimacs("p cnf 2 2\n1 2 0\n0", strict=True)
        assert [] in cnf.clauses
        assert cnf.num_clauses == 2

    def test_permissive_mode_still_lenient(self):
        # Wrong declared count is tolerated in permissive mode
        cnf = parse_dimacs("p cnf 2 5\n1 2 0")
        assert cnf.num_clauses == 1

    def test_permissive_rejects_non_integer_tokens(self):
        with pytest.raises(ValueError):
            parse_dimacs("1 abc 0")

    def test_strict_file_parsing(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cnf', delete=False) as f:
            f.write("p cnf 2 1\n1 5 0")
            path = Path(f.name)
        try:
            with pytest.raises(DimacsParseError):
                parse_dimacs_file(path, strict=True)
        finally:
            path.unlink()
