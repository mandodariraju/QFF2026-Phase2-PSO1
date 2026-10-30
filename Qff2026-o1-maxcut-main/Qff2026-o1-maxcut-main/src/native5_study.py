"""Supplementary study: custom 5-vertex instance that fits Processor A natively
(no vertex fixing). Same circuit and same settings on A and B."""
import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd
from qiskit import transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from src.optimizer import optimize
from src.problem import (make_graph, brute_force_optimum, reduced_cut_value,
                         key_to_bits)
from src.processors import load_processor, build_noise_model, build_coupling_map
from src.qaoa_circuit import build_qaoa_circuit
from src.routing import seed_study

N, SEED = 5, 42
SHOTS = 4096
TRANSPILE_SEEDS = range(5)
TWO_Q_ERRORS = [0.005, 0.01]  # both appear in organizer material; neither is official
TAB = Path("results/tables")


def evaluate(counts, edges, opt_bits):
    total = sum(counts.values())
    exp_cut = p_opt = 0.0
    for key, c in counts.items():
        bits = key_to_bits(key)
        exp_cut += reduced_cut_value(edges, {}, bits) * c / total
        if bits in opt_bits:
            p_opt += c / total
    return exp_cut, p_opt


if __name__ == "__main__":
    TAB.mkdir(parents=True, exist_ok=True)
    Path("data/raw").mkdir(parents=True, exist_ok=True)

    edges = make_graph(N, seed=SEED)
    with open("data/raw/instance5_seed42.txt", "w") as f:
        f.write("# i j w  (5-vertex supplementary instance, seed 42)\n")
        for i, j, w in edges:
            f.write(f"{i} {j} {w}\n")
    optimum, opt_list = brute_force_optimum(edges, N)
    opt_bits = set(opt_list)
    print("edges:", edges, "| total weight:", sum(w for _, _, w in edges))
    print("optimum cut:", optimum, "| optimal bitstrings:", opt_list,
          "| random baseline:", sum(w for _, _, w in edges) / 2)

    # QAOA p=1, COBYLA, 10 restarts (same optimizer as the main benchmark)
    history = []
    val, x = optimize(edges, {}, N, history=history, label="native_5q")
    pd.DataFrame(history).to_csv(TAB / "native5_restarts.csv", index=False)
    (TAB / "native5_params.json").write_text(json.dumps(
        {"optimum": optimum, "gamma": float(x[0]), "beta": float(x[1]),
         "expected_cut": val, "ratio": val / optimum}, indent=2))
    print(f"ideal expected cut {val:.3f}, ratio {val / optimum:.3f}")

    qc = build_qaoa_circuit(x[0], x[1], edges, {}, N)
    probs = Statevector(qc).probabilities_dict()
    p_ideal = sum(p for k, p in probs.items() if key_to_bits(k) in opt_bits)

    procs = [load_processor("processors/processor_A.json"),
             load_processor("processors/processor_B.json")]

    # Routing study (20 seeds, same settings as the main study)
    frames = [seed_study(qc, proc) for proc in procs]
    tdf = pd.concat(frames)
    tdf["problem"] = "native_5q"
    tdf.to_csv(TAB / "native5_transpile_summary.csv", index=False)
    cols = ["depth", "cx", "swap", "effective_cx", "qubits_used"]
    print(tdf.groupby("processor")[cols].agg(["mean", "std"]).round(2))

    # Noisy runs on A and B (same conditions)
    qm = qc.copy()
    qm.measure_all()
    rows = [dict(case="ideal", processor="topology-independent", two_qubit_error=0.0,
                 expected_cut=val, expected_cut_std=0.0, ratio=val / optimum,
                 p_optimal=p_ideal, p_optimal_std=0.0)]
    for proc in procs:
        for p2 in TWO_Q_ERRORS:
            noisy = copy.deepcopy(proc)
            noisy["noise"]["two_qubit_depolarizing"] = p2
            sim = AerSimulator(noise_model=build_noise_model(noisy))
            vals = []
            for s in TRANSPILE_SEEDS:
                tqc = transpile(qm, coupling_map=build_coupling_map(proc),
                                basis_gates=proc["basis_gates"],
                                optimization_level=1, seed_transpiler=s)
                counts = sim.run(tqc, shots=SHOTS, seed_simulator=s).result().get_counts()
                vals.append(evaluate(counts, edges, opt_bits))
            arr = np.array(vals)
            rows.append(dict(case="noisy", processor=proc["name"], two_qubit_error=p2,
                             expected_cut=arr[:, 0].mean(), expected_cut_std=arr[:, 0].std(),
                             ratio=arr[:, 0].mean() / optimum,
                             p_optimal=arr[:, 1].mean(), p_optimal_std=arr[:, 1].std()))
    qdf = pd.DataFrame(rows)
    qdf.to_csv(TAB / "native5_quality_summary.csv", index=False)
    print(qdf.round(3).to_string())
