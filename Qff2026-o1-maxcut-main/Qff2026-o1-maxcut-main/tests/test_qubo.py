import itertools
import numpy as np
from src.problem import load_edges, cut_value, maxcut_qubo

edges = load_edges("data/raw/instance_seed42.txt")
n = 6
Q = maxcut_qubo(edges, n)
assert np.allclose(Q, Q.T), "Q symmetric kaadu"

vals = []
for combo in itertools.product("01", repeat=n):
    bits = "".join(combo)
    x = np.array([int(b) for b in bits])
    e = x @ Q @ x
    assert abs(e + cut_value(edges, bits)) < 1e-9, f"mismatch at {bits}"
    vals.append(e)

print("QUBO OK: 64/64 match, min x^T Q x =", min(vals))
