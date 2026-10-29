# QFF 2026 Phase 2 Report: PS-O1 Max-Cut with QAOA

Team GARUDA. All numbers below are produced by `main.ipynb` and stored in `results/tables/`.
Everything is simulated (Qiskit Aer), nothing ran on real hardware.

## 1. Problem and formulation

The locked graph has 6 vertices and 9 weighted edges (total weight 27): (0,2,1), (0,3,4), (0,4,4), (1,4,3), (1,5,3),
(2,3,5), (2,4,1), (3,4,4), (3,5,2). Variable x_i in {0,1} is the group of vertex i, and vertex i is qubit i.

Cut weight: C(x) = sum over edges of w_ij (x_i + x_j - 2 x_i x_j). We minimise -C(x).

QUBO: -C(x) = x^T Q x with Q_ii = -(weighted degree of i) and Q_ij = Q_ji = w_ij. The notebook checks this identity on all 64 bitstrings.

Cost Hamiltonian: with x_i = (1 - Z_i)/2, H_C = sum over edges of (w_ij / 2) Z_i Z_j, and -C = H_C - 27/2.

QAOA with p = 1: start from |+>^6, apply exp(-i gamma H_C) (one RZZ(gamma * w) per edge), then exp(-i beta sum X_i) (RX(2 beta) per qubit).

Classical benchmark (brute force over 64 bitstrings): C* = 22, with exactly two optimal bitstrings, (0,0,1,0,1,1) and its complement (1,1,0,1,0,0).
A uniformly random bitstring gives r = 0.614 and P_opt = 2/64 = 0.031.

Optimiser: COBYLA, maxiter 200, cost from the exact statevector (ideal). Initial angles: `numpy.random.default_rng(seed).uniform(0, pi)` for seeds 0 to 4.
Angles are optimised once (ideal) and the same angles are evaluated on every processor, ideal and noisy, with 4096 shots.

## 2. Bell-state results (Objective 1)

State |Phi+> on Processor D, measured in ZZ, XX, YY (4096 shots each). F = (1 + <XX> - <YY> + <ZZ>) / 4.
The adjacent pair is physical qubits (0,2). The farthest pair is (0,1), distance 2, which is the diameter of D.

| Pair | Dist. | Cond. | CX | <XX> | <YY> | <ZZ> | F |
|---|---|---|---|---|---|---|---|
| 0-2 | 1 | ideal | 1 | 1.0000 | -1.0000 | 1.0000 | 1.0000 ± 0.0000 |
| 0-2 | 1 | noisy | 1 | 0.9458 ± 0.0051 | -0.9521 ± 0.0048 | 0.9551 ± 0.0046 | 0.9633 ± 0.0021 |
| 0-1 | 2 | ideal | 4 | 1.0000 | -1.0000 | 1.0000 | 1.0000 ± 0.0000 |
| 0-1 | 2 | noisy | 4 | 0.9443 ± 0.0051 | -0.9341 ± 0.0056 | 0.9385 ± 0.0054 | 0.9542 ± 0.0023 |

Interpretation. Ideal runs give the exact values, so the circuits and bases are correct. In the noisy runs three error sources act:
readout flips (1% per qubit), depolarizing error on the CX (0.5%) and on the single-qubit gates (0.1%).
Readout error alone would scale every correlation by (1 - 2 * 0.01)^2 = 0.9604 and give F of about 0.970,
so the remaining drop to 0.9633 comes from the gate errors. The distant pair needs one SWAP, which adds 3 CX (1 CX becomes 4).
Its fidelity is lower by 0.0091, with a combined standard error of 0.0031, so the gap is about 3 standard errors.
More CX gates means more depolarizing error, which explains why the farther pair is worse.
Because D has diameter 2, the routing cost on D is small (one SWAP at most for a pair).

## 3. Processor D design and justification (Objective 2)

Coupling graph (also drawn in `results/figures/processors_coupling_graphs.png`, right panel): 6 qubits and the 9 edges
0-2, 0-3, 0-4, 1-4, 1-5, 2-3, 2-4, 3-4, 3-5. Rules: connected, maximum degree 4 (qubits 3 and 4), gate set rz, sx, x, cx,
official noise rates (not better than official), `validate_processor_d` returns no violations. The file is frozen at the final commit.

Bottleneck on B. The Max-Cut graph contains a K4 on qubits {0,2,3,4} (all 6 pairs are edges). Processor B has no K4,
so at least one SWAP is unavoidable. Measured on B: 1 SWAP, 21 CX against 18 logical CX (3 extra CX), depth 37, two-qubit depth 17.
Processor A has only 5 qubits and cannot run the 6-qubit circuit at all.

Effect of D (measured, p = 1): 0 SWAPs, 18 CX (overhead 0), depth 29, two-qubit depth 14.
That is 3 fewer CX (exactly one SWAP), 8 fewer depth layers and 3 fewer two-qubit layers than B.
The expected effect was zero SWAPs and no CX overhead, and the measurement confirms it.
At p = 2, B uses 42 CX, depth 68, 2 SWAPs, while D uses 36 CX, depth 52, 0 SWAPs.

Trade-offs. (1) D is tailored to this one graph, so a different graph would need routing again.
(2) With exactly 6 qubits there are no spare qubits or extra paths for the router.
(3) Degree 4 on qubits 3 and 4 raises crosstalk risk on real hardware, which the official noise model does not capture.
(4) Diameter 2 limits how much distance the Bell test can probe.

## 4. Results on A, B and D (Objective 3)

Quality, p = 1, 4096 shots, best seed 3 (the optimised angles are printed in the notebook):

| Processor | Cond. | r | r_best | P_opt |
|---|---|---|---|---|
| A | ideal / noisy | not executable: needs 6 qubits, has 5 | | |
| B | ideal | 0.8074 | 1.000 | 0.1396 |
| B | noisy | 0.7874 | 1.000 | 0.1260 |
| D | ideal | 0.8052 | 1.000 | 0.1384 |
| D | noisy | 0.7862 | 1.000 | 0.1250 |
| random | | 0.6136 | | 0.0313 |

Resources (bound circuit with measurements, official transpilation):

| Processor | Logical CX | CX | CX overhead | Depth | 2q depth | SWAPs |
|---|---|---|---|---|---|---|
| B | 18 | 21 | 3 | 37 | 17 | 1 |
| D | 18 | 18 | 0 | 29 | 14 | 0 |

Findings.
- QAOA beats random guessing clearly. Noisy r is 0.79 against 0.61 for random, and noisy P_opt is about 0.125 against 0.031 (about 4 times higher).
- The best sampled cut equals C* = 22 on every executable run (r_best = 1.0).
- Noise lowers r by about 0.02 on both processors (B: 0.8074 to 0.7874, D: 0.8052 to 0.7862).
- B and D give the same quality within what we can resolve (noisy r 0.7874 versus 0.7862). D reaches it with fewer gates.
  The drop from ideal to noisy is slightly smaller on D (0.0190 against 0.0200 at p = 1, 0.0395 against 0.0432 at p = 2),
  which is the direction expected from fewer CX gates. We ran one 4096-shot sample per setting, so we do not claim this difference is statistically established.
- Capacity: A has 5 qubits, the circuit needs 6, so it is reported as not executable and the instance was not shrunk.
- Consistency over the 5 seeds (exact r after optimisation): 0.726 ± 0.044 (mean ± sample std).
  Seeds 0, 1, 2 and 4 end in a local optimum near r = 0.707, and seed 3 reaches r = 0.805. Evaluated with 4096 shots on D noisy, mean r over the seeds is 0.716 ± 0.039.
  So the quality depends strongly on the starting point, and the headline result uses the best seed, selected by the ideal exact expectation.
- Additional experiment, p = 2 (best seed 3): exact r = 0.883. Sampled r on D is 0.8823 ideal and 0.8428 noisy, P_opt is 0.231 ideal and 0.193 noisy.
  Going from p = 1 to p = 2 raises noisy r from 0.786 to 0.843 on D, even though the circuit has twice the CX gates (36 against 18).
  Within this noise model, the extra depth is paid for by the better ansatz.

Figures: `results/figures/maxcut_best_partition.png`, `quality_r_popt.png`, `resources_B_vs_D.png`, `seeds_exact_r.png`, `processors_coupling_graphs.png`.

## 5. Limitations and next steps (Objective 5)

Limitations.
- Single instance, simulation only. The noise model is a simple depolarizing and readout model without crosstalk or T1/T2.
- Angles are optimised in ideal simulation only, not under noise.
- COBYLA with 200 iterations and 5 random starts found the best optimum only once in 5 seeds.
- One shot sample per setting, so small differences (for example B against D noisy r) are within sampling noise.
- D is tailored to the graph, so the favourable D versus B comparison does not transfer to other graphs.
- The pipeline was tested with Python 3.14.2, qiskit 2.6.1 and qiskit-aer 0.18.2.

Evidence-based improvements.
- More restarts, since 4 of 5 starts stopped near r = 0.707 while one reached 0.805.
- Optimise the angles under the noisy model, since the ideal angles are only a starting point for noisy hardware.
- Use p = 2 on D. The 0.057 gain in noisy r (0.786 to 0.843) suggests it pays off even with 36 CX.
- Repeat the shot sampling with several simulator seeds to put error bars on the B versus D comparison.
- A less specialised D, for example the graph plus a few extra edges, to test how much of the benefit survives on other graphs.
- Readout-error mitigation, since readout alone costs about 0.03 of Bell fidelity.

## 6. Reproducibility

Run `main.ipynb` top to bottom (about 1 to 3 minutes). Seeds 0 to 4 are used for the initialisations, `seed_transpiler = 42`, `seed_simulator = 42`.
Official settings were not changed. AI use is disclosed in `README.md`.
