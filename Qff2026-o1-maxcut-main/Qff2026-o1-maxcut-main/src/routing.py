"""Transpilation study: same circuit, same settings, many seeds,
Processor A vs Processor B."""
import pandas as pd
from qiskit import transpile

from .metrics import circuit_metrics
from .processors import build_coupling_map

# 'swap' stays in the basis so routing SWAPs remain visible and countable.
STUDY_BASIS = ["rz", "sx", "x", "cx", "swap"]


def transpile_for_study(qc, proc, seed, optimization_level=1):
    return transpile(
        qc,
        coupling_map=build_coupling_map(proc),
        basis_gates=STUDY_BASIS,
        optimization_level=optimization_level,
        seed_transpiler=seed,
    )


def seed_study(qc, proc, seeds=range(20), optimization_level=1):
    """Transpile qc for one processor with many seeds; one row per seed.
    effective_cx = cx + 3*swap (each SWAP becomes 3 CX in the native basis)."""
    rows = []
    for seed in seeds:
        tqc = transpile_for_study(qc, proc, seed, optimization_level)
        m = circuit_metrics(tqc)
        cx_only = m["two_qubit_gates"] - m["swap_count"]
        rows.append({
            "processor": proc["name"],
            "seed": seed,
            "depth": m["depth"],
            "cx": cx_only,
            "swap": m["swap_count"],
            "effective_cx": cx_only + 3 * m["swap_count"],
            "qubits_used": m["num_qubits_used"],
        })
    return pd.DataFrame(rows)


def summarize(df):
    cols = ["depth", "cx", "swap", "effective_cx", "qubits_used"]
    return df.groupby("processor")[cols].agg(["mean", "std"])
