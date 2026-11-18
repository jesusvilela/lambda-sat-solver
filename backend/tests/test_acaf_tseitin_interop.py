"""Tests of the λSAT gate exporter (separate Prolog proof obligations)."""
import unittest
from itertools import product

from backend.acaf_tseitin_interop import export_tseitin_case
from backend.cnf_utils import CNFFormula, verify_model
from backend.lambda_sat import (
    App, Lam, BVar, BConst, BAnd, BOr, BNot, BXor, free_vars, beta_normalize
)


def count_gate_extensions(record, original_bits):
    gate = record["gate"]
    src = record["source"]
    env = dict(zip(src["original_free"], original_bits))
    ids = dict(gate["free_var_ids"])
    return sum(
        verify_model(CNFFormula(gate["n"], gate["clauses"]),
                     {i+1: bool(bit) for i, bit in enumerate(model)})
        for model in product((0, 1), repeat=gate["n"])
        if all(model[var_id-1] == env[name] for name, var_id in ids.items())
    )


class TestAcafTseitinExporter(unittest.TestCase):
    def assertUniqueExtension(self, term, label):
        rec = export_tseitin_case(term, label)
        for row in rec["source"]["truth_rows"]:
            self.assertEqual(count_gate_extensions(rec, row["bits"]), row["truth"],
                             (label, row))
        source_count = sum(row["truth"] for row in rec["source"]["truth_rows"])
        cnf_count = sum(verify_model(
            CNFFormula(rec["gate"]["n"], rec["gate"]["clauses"]),
            {i+1: bool(bit) for i, bit in enumerate(bits)})
            for bits in product((0,1), repeat=rec["gate"]["n"]))
        delta=len(rec["source"]["original_free"])-len(rec["source"]["normal_free"])
        self.assertEqual(source_count,cnf_count*(1<<delta))
        return rec

    def test_beta_erases_original_free_y(self):
        r=self.assertUniqueExtension(App(Lam("x",BConst(True)),BVar("y")),"erased")
        self.assertEqual(r["source"]["original_free"],["y"])
        self.assertEqual(r["source"]["normal_free"],[])
        self.assertEqual(sum(q["truth"] for q in r["source"]["truth_rows"]),2)
        self.assertEqual(r["gate"]["n"],1)

    def test_alpha_capture_avoidance_nested(self):
        term=App(App(Lam("x",Lam("y",BVar("x"))),BVar("y")),BVar("z"))
        r=self.assertUniqueExtension(term,"alpha")
        self.assertEqual(r["source"]["original_free"],["y","z"])
        self.assertEqual(r["source"]["normal_free"],["y"])

    def test_repeated_subformula(self):
        e=BOr(BVar("a"),BVar("b"))
        self.assertUniqueExtension(BAnd(e,e),"reuse")

    def test_nested_boolean_xor_and_negation(self):
        e=BAnd(BXor(BVar("a"),BVar("b")),BOr(BNot(BVar("a")),BVar("b")))
        self.assertUniqueExtension(e,"xor")

    def test_constant_false_contradiction(self):
        self.assertUniqueExtension(BConst(False),"false")

    def test_multiple_erased_vars(self):
        e=App(Lam("x",BVar("a")),BOr(BVar("z"),BVar("w")))
        r=self.assertUniqueExtension(e,"drop-argument")
        self.assertEqual(r["source"]["original_free"],["a","w","z"])
        self.assertEqual(r["source"]["normal_free"],["a"])

    def test_beta_timeout_is_not_a_semantic_counterexample(self):
        omega_lam=Lam("x",App(BVar("x"),BVar("x")))
        with self.assertRaises(RuntimeError):
            export_tseitin_case(App(omega_lam,omega_lam),
                                "omega",max_beta_steps=8)

    def test_open_abstraction_not_boolean(self):
        with self.assertRaises(ValueError):
            export_tseitin_case(Lam("x",BVar("x")),"function")

    def test_json_safe(self):
        import json
        r=export_tseitin_case(BVar("x"),"literal")
        self.assertEqual(json.loads(json.dumps(r))["source"]["original_free"],["x"])


if __name__=="__main__":
    unittest.main()
