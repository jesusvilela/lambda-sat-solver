import sys
import os

# Add the directory containing tribridge.cp311-win_amd64.pyd to PYTHONPATH
sys.path.insert(0, os.path.abspath('build/lib.win-amd64-cpython-311'))
sys.path.insert(0, os.path.abspath('.'))

try:
    import tribridge
    print("Successfully imported tribridge Cython module")
except ImportError as e:
    print(f"Failed to import tribridge: {e}")
    sys.exit(1)

# Test the router
route1 = tribridge.route_instance(1.0)
print(f"Route for 1.0 fraction: {route1}")

route2 = tribridge.route_instance(0.2)
print(f"Route for 0.2 fraction: {route2}")

route3 = tribridge.route_instance(0.0)
print(f"Route for 0.0 fraction: {route3}")

# Test the GF2 Oracle
xors_list = [
    ([1, 2, 3], 1),
    ([2, 3, 4], 0),
    ([1, 4], 0),   # 1^2^3 = 1; 2^3^4 = 0; 1^4 = 1. So 1^4=0 contradicts 1^4=1. Refuted.
]
num_vars = 4
xor_fraction = 1.0

print("Running GF2 Oracle test...")
result = tribridge.run_gf2_oracle(xors_list, num_vars, xor_fraction)
print(f"GF2 Oracle Result: {result}")
