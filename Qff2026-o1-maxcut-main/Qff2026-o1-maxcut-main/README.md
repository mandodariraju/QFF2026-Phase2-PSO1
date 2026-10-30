# Qff2026-o1-maxcut

Project Q (IBM Qiskit Fall Fest 2026, SRM University-AP), Phase 1, **PS-O1: Weighted Max-Cut with QAOA**, benchmarked on Processor A (5 qubits) and Processor B (9 qubits) with SWAP and routing analysis. Team: Garuda.

## Selected problem statement
PS-O1: Max-Cut on a weighted graph with 6 vertices and integer weights 1-5. We build the QUBO / Z_iZ_j cost Hamiltonian, run QAOA (p = 1) with a classical optimizer from several random starts, compare with the brute-force optimum, and compare Processor A vs Processor B (circuit depth, CX count, SWAP count, solution quality).

## PS specification sheet
| Item | Our value |
|---|---|
| PS code | O1 |
| PS name | Max-Cut (weighted Max-Cut with QAOA) |
| Track | Quantum Optimization |
| Input / instance | Custom seeded 6-vertex weighted graph (seed 42, 12 edges, weights 1-5, total weight 39), `data/raw/instance_seed42.txt`. No official graph was provided. |
| Core algorithm | QAOA, p = 1, COBYLA, 10 random restarts, exact statevector for the parameter search |
| Required output | Best cut, its weight, distance to the brute-force optimum, weighted-graph plot, coupling diagrams of A and B |
| Primary metric | Approximation ratio = expected cut / classical optimum (29); probability of the optimal bitstring |
| Reference / classical baseline | Brute force over 64 bitstrings: optimum 29; random-guess baseline 19.5 |
| Processor A requirements | 5 qubits, 4 couplings; cannot host the 6-qubit problem |
| Processor B requirements | 9 qubits, 12 couplings; hosts the 6-qubit problem |
| Architecture metrics | Depth, CX count, SWAP count, effective CX (cx + 3 swap), physical qubits used |

## Setup
Python 3.14.2 (GitHub Codespaces). Versions are pinned in `requirements.txt` (the pins that matter are qiskit==2.5.2 and qiskit-aer==0.17.2). Other Python versions, for example 3.12, were not tested by us.
```
pip install -r requirements.txt
```

## How to run
1. Open `main.ipynb` and run all cells top to bottom (Restart Kernel and Run All). It regenerates every table in `results/tables` and every figure in `results/figures`.
2. Or run the modules one by one from the repo root:
```
python -m tests.test_qubo         # QUBO check on all 64 bitstrings
python -m src.optimizer           # QAOA parameters, restarts table
python -m src.transpile_study     # routing cost on A vs B (20 seeds)
python -m src.noisy_simulation    # solution quality, ideal vs noisy
python -m src.make_figures        # comparison figures
python -m src.native5_study       # supplementary 5-vertex instance, native on A and B
python -m src.make_extra_outputs  # extra figures, comparison tables, circuit text
```

## Methodology
- **Instance:** custom seeded graph (`make_graph(6, seed=42)`, saved in `data/raw/instance_seed42.txt`): 6 vertices, 12 edges, total weight 39. Classical brute force over 2^6 = 64 bitstrings gives optimum cut **29** (bitstrings 001001 and 110110). Random-guess baseline: 19.5.
- **QUBO:** `maxcut_qubo` in `src/problem.py`. cut(x) = sum w_ij (x_i + x_j - 2 x_i x_j), so x^T Q x = -cut(x) with Q_ii = -sum_j w_ij and Q_ij = Q_ji = w_ij. Verified on all 64 bitstrings (`tests/test_qubo.py`); minimum x^T Q x = -29.
- **QAOA:** p = 1, cost layer from the Z_iZ_j terms, mixer RX. The cost-layer phase and sign were tested in `main.ipynb` (section 3).
- **Optimizer:** COBYLA, 10 random restarts, exact statevector expected cut. Angles are periodic and symmetric, so we report the expected cut and not gamma/beta. Every restart is saved in `results/tables/restarts.csv`.
- **Processors:** built from the slide-4 diagrams of the organizer deck and checked against them up to relabeling (`main.ipynb`, section 1). A: 5 qubits, 4 edges. B: 9 qubits, 12 edges (organizers confirmed 9 qubits, the "7 qubits" label in the deck is wrong).
- **Transpilation study:** same circuit, `optimization_level=1`, 20 transpiler seeds per processor, SWAP kept in the basis so routing SWAPs are visible, `effective_cx = cx + 3 * swap`. This basis (rz, sx, x, cx, swap) differs from the fixed basis rz, sx, x, cx, so raw CX and depth are not directly comparable with other teams; effective CX converts each SWAP to 3 CX.
- **Noisy simulation:** Aer, depolarizing noise on sx, x (0.001) and cx (0.005 and 0.01), symmetric readout error 0.01, 4096 shots (the Kit's fixed value), 5 transpiler seeds. The noisy runs use the fixed basis rz, sx, x, cx.
- **Metrics:** approximation ratio (expected cut / optimum), probability of an optimal bitstring (bitstring and its complement), depth, CX count, SWAP count.

## Assumptions
- **Processor map set:** Set 1 (Benchmark Configuration, the slide-4 drawings). A is T-shaped: (0,1),(1,2),(1,3),(3,4). B has 9 qubits and 12 edges: (0,1),(1,2),(1,6),(2,3),(2,6),(2,5),(3,4),(4,5),(5,6),(6,7),(6,8),(8,0). Maps from the Challenge Kit (Set 2) were not mixed in. The organizers confirmed that B has 9 qubits.
- No official PS-O1 graph was provided (organizer reply), so we use a custom seeded instance.
- Noise values and basis gates are **not official** until after Phase 1 shortlisting (organizer reply). Both CX errors 0.005 and 0.01 appear in the materials; neither is official. Our values in `processors/*.json` are provisional: 1q depolarizing 0.001, symmetric readout error 0.01 ([[0.99, 0.01], [0.01, 0.99]]), basis rz, sx, x, cx.
- Processor A has 5 qubits, so the full 6-qubit problem cannot be run on it (`results/tables/feasibility_notes.txt`). In the results tables the A row for the 6-vertex problem is kept with `logical_qubits = 6`, empty metrics and the note `not run: needs N > 5 qubits` (`results/tables/benchmark_rows.csv`).
- **Supplementary only:** fixing vertex 4 gives a 5-qubit problem that fits Processor A. Vertex fixing is **not an organizer-approved method**, so the main benchmark is the full 6-qubit problem and the reduction is reported separately and clearly labeled.

## Key results
Instance: optimum cut 29, random baseline 19.5. Ideal QAOA p = 1: expected cut 24.784 (ratio 0.855) for the full problem. Details and interpretation are in [`report.md`](report.md).

| Case | Expected cut | Ratio | P(optimal) |
|---|---|---|---|
| Full 6q, ideal | 24.784 | 0.855 | 0.098 |
| Full 6q on B, CX error 0.005 / 0.01 | 24.207 / 23.907 | 0.835 / 0.824 | 0.090 / 0.086 |
| Full 6q on A | not run: needs N > 5 qubits | n/a | n/a |
| Reduced 5q (vertex-fixed, NOT approved), ideal | 24.546 | 0.846 | 0.089 |
| Reduced 5q (vertex-fixed, NOT approved) on A, 0.005 / 0.01 | 23.954 / 23.640 | 0.826 / 0.815 | 0.080 / 0.076 |
| Reduced 5q (vertex-fixed, NOT approved) on B, 0.005 / 0.01 | 24.117 / 23.906 | 0.832 / 0.824 | 0.080 / 0.078 |

The best sampled cut equals the optimum (29) in every noisy run, so it is not a useful quality metric; we use expected cut and P(optimal) instead.

**Best cut found:** weight 29 (bitstring 001001 on Processor B, full 6-vertex problem), distance to the brute-force optimum 0. The average QAOA cut is lower: expected cut 24.784 in the ideal case, 4.216 below the optimum 29.

## Supplementary study: native 5-vertex instance (no vertex fixing)
The official problem has 6 vertices, which Processor A (5 qubits) cannot host, and vertex fixing is not an approved method. To still compare A and B under identical conditions, we added a second custom instance with 5 vertices (`make_graph(5, seed=42)`, `data/raw/instance5_seed42.txt`, 8 edges, total weight 28, optimum cut 21, random baseline 14) that fits both processors natively. Same circuit, same optimizer (p = 1, COBYLA, 10 restarts), same transpiler settings (20 seeds), same provisional noise (4096 shots, 5 seeds). The main benchmark remains the 6-vertex problem.

| Case | Expected cut | Ratio | P(optimal) |
|---|---|---|---|
| Native 5q, ideal | 17.526 | 0.835 | 0.166 |
| Native 5q on A, CX error 0.005 / 0.01 | 17.162 / 16.955 | 0.817 / 0.807 | 0.154 / 0.147 |
| Native 5q on B, CX error 0.005 / 0.01 | 17.211 / 17.061 | 0.820 / 0.812 | 0.156 / 0.151 |

Routing (mean of 20 seeds): depth A 43.25 vs B 34.45, SWAP 3.00 vs 1.45, effective CX 25.0 vs 20.35 (16 CX before routing on both). More in `report.md`.

## Repository structure
- `main.ipynb`: end-to-end run
- `src/`: problem, QUBO, QAOA circuit, optimizer, transpile study, noisy simulation, figures
- `tests/`: QUBO test
- `processors/`: Processor A and B definitions (JSON)
- `data/raw/`: the instance used; `data/processed/`: the QUBO matrix Q (x^T Q x = -cut)
- `results/tables`, `results/figures`, `results/circuits`: all outputs (CSV tables, figures, transpiled circuit text)
- `report.md`: analysis

## Limitations
- Two graph instances (6-vertex main benchmark, 5-vertex supplementary), p = 1, simulated provisional noise, finite topologies. No universal claim.
- The 6-vertex problem cannot run on Processor A (5 qubits), so the A-vs-B comparison uses the supplementary instances (5-vertex native instance; vertex-fixed reduction, not organizer-approved).
- Runtime was not measured. See `report.md`.

## AI assistance disclosure
An AI assistant (Claude) was used for planning, code review, debugging, documentation structure and some code: the classical helpers (`src/problem.py`, `src/routing.py`), the QUBO function and its test, the best-bitstring and restarts additions, `src/make_figures.py`, `src/native5_study.py`, `src/make_extra_outputs.py`, and the drafts of this README and `report.md`. All results were produced by running the code in this repository.
