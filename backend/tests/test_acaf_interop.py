"""Tests of the portable λSAT/Prolog contract, without external solvers."""
import json
import unittest
from backend.acaf_interop import export_case
from backend.cnf_utils import CNFFormula


class TestAcafPrologContract(unittest.TestCase):
    def test_sat_witness_replayed(self):
        r = export_case(CNFFormula(2, [[1, 2], [-1, -2]]), "sat")
        self.assertEqual(r["lambda"]["status"], "SAT")
        self.assertEqual(r["lambda"]["certification"], "model_replay")
        self.assertTrue(r["lambda"]["model"])

    def test_unsat_refutation_scope(self):
        r = export_case(CNFFormula(1, [[1], [-1]]), "unsat")
        self.assertEqual(r["lambda"]["status"], "UNSAT")
        self.assertEqual(r["lambda"]["certification"], "local_frame_derivation")

    def test_unknown_is_not_unsat(self):
        r = export_case(CNFFormula(3, [[1, 2, 3]]), "unknown", run_frame=False)
        self.assertEqual(r["lambda"]["status"], "UNKNOWN")
        self.assertEqual(r["lambda"]["certification"], "none")

    def test_provenance_cannot_be_promoted(self):
        r = export_case(CNFFormula(1, []), "ghost", role="provenance_only")
        self.assertEqual(r["role"], "provenance_only")
        self.assertEqual(r["lambda"]["status"], "NOT_APPLICABLE")

    def test_empty_clause_preserved(self):
        r = export_case(CNFFormula(1, [[]]), "empty")
        self.assertEqual(r["cnf"]["clauses"], [[]])
        self.assertEqual(r["lambda"]["status"], "UNSAT")

    def test_declared_universe_preserved(self):
        r = export_case(CNFFormula(4, [[1]]), "unused", run_frame=False)
        self.assertEqual(r["schema"], "acaf-sat-v1")
        self.assertEqual(r["count_universe"], "declared_variables")
        self.assertEqual(r["cnf"]["n"], 4)

    def test_invalid_literals_and_roles(self):
        for f in (CNFFormula(1, [[2]]), CNFFormula(1, [[0]]), CNFFormula(-1, [])):
            with self.subTest(f=f), self.assertRaises(ValueError):
                export_case(f, "bad")
        with self.assertRaises(ValueError):
            export_case(CNFFormula(1, [[1]]), "bad", role="proof_of_eth")

    def test_json_safe(self):
        r = export_case(CNFFormula(2, [[-1, 2]]), "encode")
        self.assertEqual(json.loads(json.dumps(r))["cnf"]["n"], 2)


if __name__ == "__main__":
    unittest.main()
