import json
from pathlib import Path

from qiskit.transpiler import CouplingMap
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error


def load_processor(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def build_coupling_map(proc):
    return CouplingMap(proc["coupling_map"])


def build_noise_model(proc):
    n = proc["noise"]
    model = NoiseModel()
    model.add_all_qubit_quantum_error(
        depolarizing_error(n["one_qubit_depolarizing"], 1), ["sx", "x"]
    )
    model.add_all_qubit_quantum_error(
        depolarizing_error(n["two_qubit_depolarizing"], 2), ["cx"]
    )
    model.add_all_qubit_readout_error(ReadoutError(n["readout_error"]))
    return model
