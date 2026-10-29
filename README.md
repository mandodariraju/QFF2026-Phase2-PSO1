# QFF 2026 Phase 2: PS-O1 Max-Cut with QAOA

**Team:** GARUDA
**Problem statement:** PS-O1, Quantum Optimization of Network Partitioning Using QAOA
(same team and same problem statement as Phase 1)

## Summary

We formulate Max-Cut on the locked 6-vertex weighted graph (9 edges, total weight 27) as a QUBO,
solve it with QAOA (p = 1, five seeded initializations), and benchmark it on Processor A, Processor B
and our custom Processor D, ideal and noisy, against the exact classical optimum C* = 22.
Processor D is a problem-matched 6-qubit topology whose 9 coupling edges equal the 9 graph edges.
On D the QAOA circuit needs 0 SWAPs (B needs 1), 18 CX (B: 21) and depth 29 (B: 37) at equal solution quality.

## How to run

Tested with Python 3.14.2, qiskit 2.6.1, qiskit-aer 0.18.2 (the kit lists Python 3.10 to 3.12).

```bash
git clone https://github.com/mandodariraju/QFF2026-Phase2-PSO1
cd QFF2026-Phase2-PSO1
python -m venv opt-env
source opt-env/bin/activate        # Windows: opt-env\Scripts\activate
pip install -r requirements.txt
jupyter notebook main.ipynb        # Run All, top to bottom (about 1 to 3 minutes)
```

Or from the terminal: `jupyter nbconvert --to notebook --execute main.ipynb --output /tmp/run.ipynb`.
The whole notebook is fast, so no `RECOMPUTE` flag is needed.

## Repository layout

| Path | Content |
|---|---|
| `main.ipynb` | Full pipeline: formulation, QUBO, QAOA, benchmarks, seeds, p = 2, Bell state |
| `qff_phase2.py` | Organizer starter module (unchanged) |
| `instances.json` | Organizer locked instances (unchanged) |
| `data/instance.json` | Locked PS-O1 instance (copy of our section) |
| `processors/` | `processor_A.json`, `processor_B.json`, and our frozen `processor_D.json` |
| `results/tables/` | `results.csv`, `bell.csv`, plus `results_detail.csv`, `seeds.csv`, `results_p2_additional.csv` |
| `results/figures/` | Figures used in the report |
| `report.md` | Final report |

## Official settings (not changed)

Basis gates rz, sx, x, cx. Transpiler optimization_level 1 with SABRE, seed_transpiler 42.
AerSimulator seed 42. 4096 shots. Noise: 1-qubit depolarizing 0.001, 2-qubit depolarizing 0.005,
readout flip 0.01. Initialization seeds 0, 1, 2, 3, 4 (angles uniform in [0, pi]).
Optimizer: COBYLA, maxiter 200, cost from the exact statevector (ideal).
Angles are optimized once in ideal simulation and then evaluated on A, B and D, ideal and noisy.

## Key results (p = 1, best seed = 3)

C* = 22. Optimal partitions: (0,0,1,0,1,1) and its complement (1,1,0,1,0,0).
Uniform-random baseline: r = 0.614, P_opt = 0.031.

| Processor | Condition | Best cut | r | r_best | P_opt | CX | Depth | 2q depth | SWAPs |
|---|---|---|---|---|---|---|---|---|---|
| A | ideal / noisy | not executable (needs 6 qubits, has 5) | - | - | - | - | - | - | - |
| B | ideal | 22 | 0.8074 | 1.000 | 0.1396 | 21 | 37 | 17 | 1 |
| B | noisy | 22 | 0.7874 | 1.000 | 0.1260 | 21 | 37 | 17 | 1 |
| D | ideal | 22 | 0.8052 | 1.000 | 0.1384 | 18 | 29 | 14 | 0 |
| D | noisy | 22 | 0.7862 | 1.000 | 0.1250 | 18 | 29 | 14 | 0 |

Logical CX = 18 on every processor. Consistency over the 5 seeds (exact r after optimization):
0.726 ± 0.044 (mean ± sample std). Four seeds reach a local optimum near r = 0.707, one (seed 3) reaches r = 0.805.

Additional experiment, p = 2 (best seed 3): D noisy r = 0.8428, B noisy r = 0.8408; D uses 36 CX and 0 SWAPs, B uses 42 CX and 2 SWAPs.

## Bell state (Processor D, 4096 shots per basis)

| Pair | Distance | Condition | CX | F ± SE |
|---|---|---|---|---|
| 0-2 | 1 | ideal | 1 | 1.0000 ± 0.0000 |
| 0-2 | 1 | noisy | 1 | 0.9633 ± 0.0021 |
| 0-1 | 2 | ideal | 4 | 1.0000 ± 0.0000 |
| 0-1 | 2 | noisy | 4 | 0.9542 ± 0.0023 |

Full table with the XX, YY, ZZ correlations: `results/tables/bell.csv`.

## Processor D

6 qubits, 9 coupling edges identical to the Max-Cut graph (maximum degree 4, connected, gate set rz, sx, x, cx,
official noise rates). It contains the K4 on qubits 0, 2, 3, 4, which Processor B cannot embed, so every RZZ of the
cost layer is native. Trade-off: it is tailored to this one graph, has no spare qubits for routing, and degree 4
means higher crosstalk risk on real hardware. Full justification is in `report.md`.

## Report

See [`report.md`](report.md).

## AI tools disclosure

[EDIT THIS TO BE TRUE.] Example: We used Claude (Anthropic) to help read the challenge kit, structure the repository,
draft the notebook and write the report text. We ran the notebook ourselves, checked the numbers against the generated
CSV files, and take responsibility for the correctness of the work.
