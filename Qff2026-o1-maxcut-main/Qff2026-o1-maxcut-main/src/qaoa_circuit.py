from qiskit import QuantumCircuit


def build_qaoa_circuit(gamma: float, beta: float, edges, linear, n: int) -> QuantumCircuit:
    """p=1 QAOA circuit for weighted Max-Cut.
    edges  : list of (i, j, weight)
    linear : dict {qubit: coefficient}  (use {} for the full problem)
    n      : number of qubits
    """
    qc = QuantumCircuit(n)

    # Step 1: Initial Hadamard Layer (Superposition)
    qc.h(range(n))

    # Step 2: Cost Layer (RZZ for edges, RZ for linear terms)
    for u, v, w in edges:
        qc.rzz(2 * gamma * w, u, v)
    for q, coeff in linear.items():
        if coeff != 0:
            qc.rz(2 * gamma * coeff, q)

    # Step 3: Mixer Layer (RX gates)
    for q in range(n):
        qc.rx(2 * beta, q)

    return qc
