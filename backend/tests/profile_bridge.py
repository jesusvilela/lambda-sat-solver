import time
import sys
from pathlib import Path
from backend.cnf_utils import parse_dimacs_file
import tribridge

def profile_bridge(cnf_path):
    print(f"Loading {cnf_path}...")
    t0 = time.perf_counter()
    formula = parse_dimacs_file(Path(cnf_path))
    t1 = time.perf_counter()
    print(f"Loaded in {t1 - t0:.4f}s")
    
    print("Routing via Cython...")
    t2 = time.perf_counter()
    res = tribridge.route_instance_topology(formula.clauses, formula.num_vars)
    t3 = time.perf_counter()
    print(f"Routed in {t3 - t2:.4f}s")
    print(res)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        profile_bridge(sys.argv[1])
    else:
        print("Usage: python profile_bridge.py <path_to_cnf>")
