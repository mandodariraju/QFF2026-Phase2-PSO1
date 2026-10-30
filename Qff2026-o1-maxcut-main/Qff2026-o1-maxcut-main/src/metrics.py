def circuit_metrics(qc):
    ops = qc.count_ops()
    two_q = {"cx", "cz", "ecr", "swap", "rxx", "ryy", "rzz"}
    return {
        "depth": qc.depth(),
        "num_qubits_used": len([q for q in qc.qubits if any(
            q in inst.qubits for inst in qc.data)]),
        "total_ops": sum(ops.values()),
        "two_qubit_gates": sum(n for g, n in ops.items() if g.lower() in two_q),
        "swap_count": ops.get("swap", 0),
        "ops": dict(ops),
    }
