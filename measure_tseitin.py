import sys
import time
import pycosat

sys.path.append("H:\\LANGTOLANGBIDIRECTIONALTRAINBRIDGE\\lambda-sat-solver")
from backend.cnf_utils import TseitinTransformer

def create_complex_formula(depth=5):
    def build_tree(d, start_var):
        if d == 0:
            return {'type': 'LITERAL', 'value': start_var}, start_var + 1
        left, next_var = build_tree(d - 1, start_var)
        right, next_var = build_tree(d - 1, next_var)
        op = 'XOR' if d % 2 == 0 else 'AND'
        return {'type': op, 'left': left, 'right': right} if op == 'XOR' else {'type': op, 'children': [left, right]}, next_var

    formula, _ = build_tree(depth, 1)
    return {
        'type': 'AND',
        'children': [
            formula,
            {'type': 'NOT', 'child': formula}
        ]
    }

print("Building Tseitin Instance...")
raw_formula = create_complex_formula(10)
transformer = TseitinTransformer()
cnf = transformer.transform(raw_formula)
print(f"Generated CNF with {cnf.num_vars} variables and {cnf.num_clauses} clauses.")

print("Executing PycoSAT (as a holonomy proxy)...")
start_time = time.time()
res = pycosat.solve(cnf.clauses)
end_time = time.time()
print(f"Time taken: {end_time - start_time:.4f} seconds")
print(f"Result: {res}")
