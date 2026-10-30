"""Classical side of PS-O1: graph instance, cut value, brute-force baseline,
and the 5-variable reduction (fix one vertex) used for Processor A."""
import itertools
import random
from pathlib import Path

import networkx as nx
import numpy as np

def make_graph(n=6, seed=42, edge_prob=0.7, w_min=1, w_max=5):
    """Random connected weighted graph. Returns a list of (i, j, w)."""
    rng = random.Random(seed)
    pairs = list(itertools.combinations(range(n), 2))
    while True:
        edges = [(i, j, rng.randint(w_min, w_max))
                 for i, j in pairs if rng.random() < edge_prob]
        g = nx.Graph()
        g.add_nodes_from(range(n))
        g.add_edges_from((i, j) for i, j, _ in edges)
        if nx.is_connected(g):
            return edges


def load_edges(path):
    """Read an edge-list file with lines 'i j w' (commas also accepted)."""
    edges = []
    for line in Path(path).read_text().splitlines():
        line = line.strip().replace(",", " ")
        if not line or line.startswith("#"):
            continue
        i, j, w = line.split()[:3]
        edges.append((int(i), int(j), int(w)))
    return edges


def cut_value(edges, bits):
    """bits is a string like '010110'; bits[i] is the side of node i."""
    return sum(w for i, j, w in edges if bits[i] != bits[j])


def brute_force_optimum(edges, n):
    """Classical baseline: best cut value and ALL optimal bitstrings
    (a bitstring and its complement always give the same cut)."""
    best, best_bits = -1, []
    for combo in itertools.product("01", repeat=n):
        bits = "".join(combo)
        val = cut_value(edges, bits)
        if val > best:
            best, best_bits = val, [bits]
        elif val == best:
            best_bits.append(bits)
    return best, best_bits


def key_to_bits(key):
    """Qiskit count keys are little-endian (qubit 0 is the RIGHTMOST
    character). This returns bits[i] = outcome of qubit/node i."""
    return key.replace(" ", "")[::-1]


def maxcut_qubo(edges, n):
    """QUBO matrix Q for Max-Cut, x in {0,1}^n.
    cut(x) = sum w_ij (x_i + x_j - 2 x_i x_j), so x^T Q x = -cut(x).
    Maximizing the cut = minimizing x^T Q x."""
    Q = np.zeros((n, n))
    for i, j, w in edges:
        Q[i, i] -= w
        Q[j, j] -= w
        Q[i, j] += w
        Q[j, i] += w
    return Q
def reduce_fix_vertex(edges, n, fixed=None):
    """Fix one vertex to side 0. Valid because flipping every vertex keeps the
    cut value. Returns (reduced_edges, linear, kept):
      kept[k] = original node of reduced node k
      reduced cut = sum w*(x_i != x_j) over reduced_edges + sum linear[k]*x_k
    Edges touching the fixed vertex become single-qubit terms (no 2-qubit gate)."""
    if fixed is None:
        fixed = n - 1
    kept = [v for v in range(n) if v != fixed]
    new_id = {v: k for k, v in enumerate(kept)}
    reduced_edges, linear = [], {k: 0 for k in range(len(kept))}
    for i, j, w in edges:
        if fixed in (i, j):
            other = j if i == fixed else i
            linear[new_id[other]] += w
        else:
            reduced_edges.append((new_id[i], new_id[j], w))
    return reduced_edges, linear, kept


def reduced_cut_value(reduced_edges, linear, bits):
    val = sum(w for i, j, w in reduced_edges if bits[i] != bits[j])
    val += sum(c for k, c in linear.items() if bits[k] == "1")
    return val


def brute_force_reduced(reduced_edges, linear, m):
    best, best_bits = -1, []
    for combo in itertools.product("01", repeat=m):
        bits = "".join(combo)
        val = reduced_cut_value(reduced_edges, linear, bits)
        if val > best:
            best, best_bits = val, [bits]
        elif val == best:
            best_bits.append(bits)
    return best, best_bits


if __name__ == "__main__":
    n = 6
    edges = make_graph(n)
    print("edges:", edges)
    best, opt = brute_force_optimum(edges, n)
    print("optimum cut:", best, "bitstrings:", opt)
    red_edges, linear, kept = reduce_fix_vertex(edges, n)
    best_r, opt_r = brute_force_reduced(red_edges, linear, n - 1)
    print("reduced optimum:", best_r, "| matches full:", best_r == best)
