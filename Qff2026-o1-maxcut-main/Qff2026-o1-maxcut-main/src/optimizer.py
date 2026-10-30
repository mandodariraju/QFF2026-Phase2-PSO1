import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from qiskit.quantum_info import Statevector

from src.problem import (load_edges, reduce_fix_vertex, reduced_cut_value,
                         brute_force_optimum, key_to_bits)
from src.qaoa_circuit import build_qaoa_circuit


def compute_expected_cut(params, edges, linear, n):
    gamma, beta = params
    qc = build_qaoa_circuit(gamma, beta, edges, linear, n)
    probs = Statevector(qc).probabilities_dict()

    total_cut = 0.0
    for bitstr, prob in probs.items():
        bits = key_to_bits(bitstr)  # Qiskit keys: qubit 0 is the RIGHTMOST char
        total_cut += prob * reduced_cut_value(edges, linear, bits)
    return -total_cut  # negative because COBYLA minimizes


def optimize(edges, linear, n, restarts=10, history=None, label=""):
    """Returns (best expected cut, best params). If history is a list, one dict
    per restart (initial angles, final angles, expected cut) is appended."""
    best_val, best_x = 0.0, None
    for seed in range(restarts):
        rng = np.random.default_rng(seed)
        init_params = rng.uniform(0, 2 * np.pi, 2)
        res = minimize(compute_expected_cut, init_params, args=(edges, linear, n),
                       method="COBYLA", options={"maxiter": 200})
        if history is not None:
            history.append(dict(problem=label, restart=seed,
                                init_gamma=float(init_params[0]),
                                init_beta=float(init_params[1]),
                                final_gamma=float(res.x[0]),
                                final_beta=float(res.x[1]),
                                expected_cut=float(-res.fun),
                                n_evals=int(res.nfev)))
        if -res.fun > best_val:
            best_val, best_x = -res.fun, res.x
    return best_val, best_x


if __name__ == "__main__":
    all_edges = load_edges("data/raw/instance_seed42.txt")
    optimum, _ = brute_force_optimum(all_edges, 6)
    history = []

    out = {"optimum": optimum, "random_baseline": sum(w for _, _, w in all_edges) / 2}

    # Main benchmark: full 6-vertex problem
    val, x = optimize(all_edges, {}, 6, history=history, label="full_6q")
    out["full"] = {"gamma": float(x[0]), "beta": float(x[1]),
                   "expected_cut": val, "ratio": val / optimum}
    print(f"FULL (6 qubits): expected cut {val:.3f}, ratio {val / optimum:.3f}, "
          f"gamma={x[0]:.3f}, beta={x[1]:.3f}")

    # Supplementary: team's own 5-variable reduction (vertex 4 fixed)
    red_edges, linear, kept = reduce_fix_vertex(all_edges, 6, fixed=4)
    val_r, x_r = optimize(red_edges, linear, 5, history=history, label="reduced_5q")
    out["reduced"] = {"fixed_vertex": 4, "kept": kept,
                      "gamma": float(x_r[0]), "beta": float(x_r[1]),
                      "expected_cut": val_r, "ratio": val_r / optimum}
    print(f"REDUCED (5 qubits): expected cut {val_r:.3f}, ratio {val_r / optimum:.3f}, "
          f"gamma={x_r[0]:.3f}, beta={x_r[1]:.3f}")

    Path("results/tables").mkdir(parents=True, exist_ok=True)
    Path("results/tables/best_params.json").write_text(json.dumps(out, indent=2))

    df = pd.DataFrame(history)
    df.to_csv("results/tables/restarts.csv", index=False)
    summary = df.groupby("problem")["expected_cut"].agg(["mean", "min", "max"])
    summary["ratio_of_max"] = summary["max"] / optimum
    summary.to_csv("results/tables/restarts_summary.csv")
    print(summary.round(3).to_string())
    print("random baseline:", out["random_baseline"], "| optimum:", optimum)
