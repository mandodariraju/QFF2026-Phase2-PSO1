from collections import Counter
import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd
from qiskit import transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from src.problem import (load_edges, reduce_fix_vertex, reduced_cut_value,
                         brute_force_optimum, brute_force_reduced, key_to_bits)
from src.processors import load_processor, build_noise_model, build_coupling_map
from src.qaoa_circuit import build_qaoa_circuit

SHOTS = 4096
TRANSPILE_SEEDS = range(5)
TWO_Q_ERRORS = [0.005, 0.01]  # both appear in organizer material; neither is official

params = json.loads(Path("results/tables/best_params.json").read_text())
all_edges = load_edges("data/raw/instance_seed42.txt")
red_edges, linear, kept = reduce_fix_vertex(all_edges, 6, fixed=4)
opt_full, bits_full = brute_force_optimum(all_edges, 6)
opt_red, bits_red = brute_force_reduced(red_edges, linear, 5)

problems = {
    "full_6q": dict(edges=all_edges, linear={}, n=6, p=params["full"],
                    optimum=opt_full, opt_bits=set(bits_full)),
    "reduced_5q": dict(edges=red_edges, linear=linear, n=5, p=params["reduced"],
                       optimum=opt_red, opt_bits=set(bits_red)),
}
procs = [load_processor("processors/processor_A.json"),
         load_processor("processors/processor_B.json")]


def evaluate(counts, pr):
    total = sum(counts.values())
    exp_cut = p_opt = 0.0
    best, best_bits, best_c = -1, None, -1
    for key, c in counts.items():
        bits = key_to_bits(key)
        cut = reduced_cut_value(pr["edges"], pr["linear"], bits)
        exp_cut += cut * c / total
        if bits in pr["opt_bits"]:
            p_opt += c / total
        if cut > best or (cut == best and c > best_c):
            best, best_bits, best_c = cut, bits, c
    return exp_cut, p_opt, best, best_bits


rows = []
for name, pr in problems.items():
    qc = build_qaoa_circuit(pr["p"]["gamma"], pr["p"]["beta"],
                            pr["edges"], pr["linear"], pr["n"])

    # Ideal reference: exact statevector, independent of processor topology
    probs = Statevector(qc).probabilities_dict()
    e = sum(p * reduced_cut_value(pr["edges"], pr["linear"], key_to_bits(k))
            for k, p in probs.items())
    po = sum(p for k, p in probs.items() if key_to_bits(k) in pr["opt_bits"])
    rows.append(dict(problem=name, case="ideal", processor="topology-independent",
                     two_qubit_error=0.0, expected_cut=e, expected_cut_std=0.0,
                     ratio=e / pr["optimum"], p_optimal=po, p_optimal_std=0.0,
                     best_sampled_cut=None, status="ok"))

    qm = qc.copy()
    qm.measure_all()
    for proc in procs:
        if pr["n"] > proc["num_qubits"]:
            rows.append(dict(problem=name, case="noisy", processor=proc["name"],
                             status=f"cannot_host ({pr['n']} qubits > {proc['num_qubits']})"))
            continue
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
                vals.append(evaluate(counts, pr))
            arr = np.array([v[:3] for v in vals], dtype=float)
            top_bits = Counter(v[3] for v in vals).most_common(1)[0][0]
            rows.append(dict(problem=name, case="noisy", processor=proc["name"],
                             two_qubit_error=p2,
                             expected_cut=arr[:, 0].mean(), expected_cut_std=arr[:, 0].std(),
                             ratio=arr[:, 0].mean() / pr["optimum"],
                             p_optimal=arr[:, 1].mean(), p_optimal_std=arr[:, 1].std(),
                             best_sampled_cut=arr[:, 2].mean(),
                             best_sampled_bits=top_bits, status="ok"))

df = pd.DataFrame(rows)
df.to_csv("results/tables/quality_summary.csv", index=False)
print(df.round(3).to_string())
