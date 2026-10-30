# Report: PS-O1 Max-Cut with QAOA on Processor A vs B

## 1. Problem
Weighted Max-Cut on a 6-vertex graph (12 edges, weights 1-5, total weight 39, seed 42). Objective: maximize the cut weight. Brute force gives optimum **29** (bitstrings 001001 and 110110). A random assignment cuts 19.5 on average.

## 2. Method
- QUBO: x^T Q x = -cut(x), verified on all 64 bitstrings. Cost Hamiltonian from Z_iZ_j terms.
- QAOA depth p = 1, COBYLA, 10 random restarts, exact statevector expected cut. Restarts (expected cut): full mean 22.789, min 19.987, max 24.784; reduced mean 21.317, min 19.5, max 24.546. A minimum of 19.5 equals the random baseline, so some restarts got stuck; we therefore report the best of 10.
- Main benchmark: the full 6-qubit problem. Supplementary: our own 5-variable reduction (vertex 4 fixed to side 0, which keeps the optimum 29). The reduction is not organizer-approved and is reported separately.

## 3. Assumptions and setup
- Processor map set: Set 1 (Benchmark Configuration, slide-4 drawings) for both A and B. A is T-shaped, B has 9 qubits and 12 edges. Maps from the Challenge Kit (Set 2) were not mixed in.
- Processors built from the organizer slide-4 diagrams. A: 5 qubits, edges (0,1),(1,2),(1,3),(3,4). B: 9 qubits, 12 edges. Processor A's slide-4 drawing is T-shaped (qubit 1 has three neighbours), not a linear chain. The deck label "7 qubits" for B is wrong according to the organizers' written reply; the drawing has 9 nodes and the organizers confirmed 9. B contains cycles (for example the triangle 1-2-6), so it is not a bipartite heavy-hex layout. Both maps are in `processors/*.json`.
- Noise (provisional, not official): 1q depolarizing 0.001 on sx and x, 2q depolarizing on cx 0.005 and 0.01, symmetric readout error 0.01, basis rz, sx, x, cx (fixed basis in the noisy runs; the transpiler decomposes SWAPs into 3 CX). A and B use the same values, so differences come from topology only.
- Transpiler: optimization_level 1, 20 seeds (routing study), 5 seeds (noisy runs), 4096 shots (the Kit's fixed value).
- Custom instance because no official graph was provided.

## 4. Results

### 4.1 Solution quality (expected cut / optimum 29)
All noisy runs: 4096 shots, 5 transpiler seeds, symmetric readout error 0.01, fixed basis rz, sx, x, cx. Rows marked "vertex-fixed, NOT approved" are the supplementary reduction; they are not the PS-O1 benchmark.
| Problem | Processor | CX error | Expected cut (mean ± std over 5 seeds) | Ratio | P(optimal) |
|---|---|---|---|---|---|
| Full 6q | ideal | n/a | 24.784 | 0.855 | 0.098 |
| Full 6q | A | n/a | not run: needs N > 5 qubits (logical_qubits = 6) | n/a | n/a |
| Full 6q | B | 0.005 | 24.207 ± 0.105 | 0.835 | 0.090 |
| Full 6q | B | 0.01 | 23.907 ± 0.118 | 0.824 | 0.086 |
| Reduced 5q (vertex-fixed, NOT approved) | ideal | n/a | 24.546 | 0.846 | 0.089 |
| Reduced 5q (vertex-fixed, NOT approved) | A | 0.005 | 23.954 ± 0.044 | 0.826 | 0.080 |
| Reduced 5q (vertex-fixed, NOT approved) | A | 0.01 | 23.640 ± 0.039 | 0.815 | 0.076 |
| Reduced 5q (vertex-fixed, NOT approved) | B | 0.005 | 24.117 ± 0.056 | 0.832 | 0.080 |
| Reduced 5q (vertex-fixed, NOT approved) | B | 0.01 | 23.906 ± 0.087 | 0.824 | 0.078 |

Best sampled cut is 29 (the optimum) in all noisy runs (bitstring 001001 for the full problem, 00101 for the reduced one), so it does not separate the cases.

### 4.2 Architecture metrics (mean ± std over 20 transpiler seeds)
| Problem | Processor | Depth | CX | SWAP | Effective CX (cx + 3 swap) | Qubits used |
|---|---|---|---|---|---|---|
| Full 6q | A | cannot be transpiled | n/a | n/a | n/a | n/a |
| Full 6q | B | 45.5 ± 7.47 | 24 ± 0 | 2.3 ± 0.47 | 30.9 ± 1.41 | 6 |
| Reduced 5q (vertex-fixed, NOT approved) | A | 43.4 ± 5.51 | 18 ± 0 | 4.0 ± 0.00 | 30.0 ± 0.00 | 5 |
| Reduced 5q (vertex-fixed, NOT approved) | B | 35.2 ± 4.91 | 18 ± 0 | 1.5 ± 0.51 | 22.5 ± 1.54 | 5 |

Minimum CX before routing: 24 (full), 18 (reduced). The CX column is the CX count after transpilation, with routing SWAPs counted separately; effective CX adds 3 CX per SWAP. On Processor A every seed gave exactly 4 SWAPs for the reduced problem. Depth varies a lot between seeds (std 5 to 7), so the depth difference between A and B is less clear than the SWAP and effective-CX differences.

Minimum CX before routing: 24 (full), 18 (reduced). The CX column for the reduced problem is derived from effective CX minus 3 x SWAP. Standard deviations are in `results/tables/transpile_summary.csv` and in `main.ipynb` section 5.

**Basis gates:** the transpilation study keeps `swap` in the basis (rz, sx, x, cx, swap) so routing SWAPs stay visible and countable; effective CX = cx + 3 swap converts them to the fixed basis rz, sx, x, cx. Raw CX and depth in the 4.2 table therefore differ from a run with the fixed basis only and are not directly comparable with other teams' counts. The noisy runs in 4.1 use the fixed basis.

### 4.3 Supplementary: native 5-vertex instance (no vertex fixing)
Custom 5-vertex instance (seed 42, edges (0,1,1),(0,3,2),(1,2,5),(1,3,4),(1,4,1),(2,3,5),(2,4,5),(3,4,5), total weight 28). Optimum cut 21 (bitstrings 00110 and 11001), random baseline 14. QAOA p = 1, 10 restarts: expected cut mean 16.569, min 15.161, max 17.526 (ratio 0.835). It fits Processor A and B natively, so no reduction is needed. This instance has 5 vertices and is an additional study; the 6-vertex problem is the main benchmark.

| Metric | Processor A | Processor B | B minus A |
|---|---|---|---|
| Depth | 43.25 ± 4.25 | 34.45 ± 3.85 | -8.8 |
| CX after routing (16 before routing) | 16 | 16 | 0 |
| SWAP | 3.00 ± 0.00 | 1.45 ± 0.51 | -1.55 |
| Effective CX (cx + 3 swap) | 25.00 ± 0.00 | 20.35 ± 1.53 | -4.65 |
| Qubits used | 5.0 | 5.1 ± 0.31 | +0.1 |
| Expected cut, CX error 0.005 | 17.162 ± 0.048 | 17.211 ± 0.034 | +0.049 |
| Expected cut, CX error 0.01 | 16.955 ± 0.054 | 17.061 ± 0.032 | +0.106 |
| Ratio, 0.005 / 0.01 | 0.817 / 0.807 | 0.820 / 0.812 | +0.002 / +0.005 |
| P(optimal), 0.005 / 0.01 | 0.154 / 0.147 | 0.156 / 0.151 | +0.002 / +0.005 |

Ideal reference: expected cut 17.526, P(optimal) 0.166. B uses 5.1 qubits on average because some transpiler seeds placed the circuit on a sixth physical qubit.

## 5. Interpretation
1. **What changed between A and B?** The full problem does not fit on A at all (6 qubits > 5). This is a qubit-count limit, not a connectivity limit. For the supplementary 5-qubit problem, B needed fewer SWAPs (1.5 vs 4.0), less depth (35.2 vs 43.4) and less effective CX (22.5 vs 30.0).
2. **Architectural property:** Processor A is a tree with 4 edges, so many pairs of qubits that interact in the problem (9 two-qubit edges on 5 nodes) are not adjacent and need SWAPs. Processor B has 12 edges, cycles and a hub qubit with 5 neighbors (qubit 6), so more problem edges map to neighbors directly. This is our explanation from the coupling graphs; we did not run a separate experiment isolating each property.
3. **Extra operations from routing:** on the reduced problem, A added 4.0 SWAPs (about 12 extra CX) and B 1.5 SWAPs (about 4.5 extra CX) on top of 18 CX. For the full problem on B, 2.3 SWAPs added about 6.9 CX on top of 24.
4. **Effect on quality:** B is slightly better than A on the reduced problem: expected cut higher by 0.163 (CX error 0.005) and 0.266 (0.01), same direction in both runs. These gaps are small compared with the ideal-to-noisy drop (about 0.4 to 0.9) and only about 2 to 3 times the combined seed std over 5 seeds, so we do not make a strong claim. The approximation ratio stays well above the random baseline ratio (19.5 / 29 = 0.672) in all cases.
5. **Gate-set / noise confounds:** A and B use the same provisional noise and basis gates, so topology is the only intended difference. But the noise is not official, depolarizing noise on cx only affects the CX and SWAP-as-3-CX count, and SWAP-heavy routing is penalized by exactly this assumption. Results may change with the official noise and basis gates.
6. **Uncertain:** transpiler routing is stochastic (we average over seeds), 5 seeds is small for the noisy runs, p = 1 only, one instance, and the reduction is not an approved method.
7. **Second instance:** the native 5-vertex instance (no reduction) shows the same pattern as the reduced 6-vertex problem: fewer SWAPs on B (1.45 vs 3.00), less depth (34.45 vs 43.25), less effective CX (20.35 vs 25.0) and a small quality advantage for B (+0.049 and +0.106 expected cut, within about 1 to 2 combined seed std over 5 seeds, so not clearly distinguishable from noise). Two instances, one processor pair, p = 1 and provisional noise do not support a general claim.

## 6. Limitations
- Simulated, provisional noise only; two graph instances (6-vertex main benchmark, 5-vertex supplementary); p = 1; finite topologies. No universal claim.
- Runtime was not measured.
- Full 6-qubit problem could not be run on Processor A, so the A-vs-B comparison on quality uses the supplementary problems (vertex-fixed reduction, not organizer-approved, and the native 5-vertex instance).
- Best sampled cut is not informative (always 29).

## 7. Conclusion
QAOA (p = 1) reaches an expected cut of 24.784 on the full problem (ratio 0.855 vs optimum 29), and the best sampled cut finds the optimum in every run. Processor B can host the full problem; Processor A cannot. On the supplementary 5-qubit problem, B's richer connectivity cut routing overhead (SWAP 1.5 vs 4.0, effective CX 22.5 vs 30.0) and gave a small, consistent quality advantage under our provisional noise model.

The same direction appears on a second, native 5-vertex instance that needs no vertex fixing (SWAP 1.45 vs 3.00, effective CX 20.35 vs 25.0, expected cut +0.049 / +0.106 for B).

## 8. Problem faced and proposed Processor D (design proposal, not benchmarked)
This section is design reasoning built on the measured A/B results above. No Processor D run is reported here.

### 8.1 Problems faced when running PS-O1 on Processors A and B
1. **Qubit count:** PS-O1 has 6 vertices, so the circuit needs 6 qubits; Processor A has 5. Transpilation fails with CircuitTooWideForTarget (`results/tables/feasibility_notes.txt`). Vertex fixing is not an approved method, so the full problem runs on B only.
2. **Connectivity:** Processor A has 4 couplings (a tree). The reduced problem has 9 and the native 5-vertex problem has 8 interacting pairs, so at least 5 of the 9 (reduced) and at least 4 of the 8 (native) interacting pairs are not adjacent on A. Measured SWAPs on A vs B: 4.0 vs 1.5 (reduced), 3.0 vs 1.45 (native). Effective CX: 30.0 vs 22.5 and 25.0 vs 20.35.
3. **Cost floor:** each RZZ costs 2 CX, so the full problem needs at least 24 CX before routing. On B routing added about 2.3 SWAPs (about 6.9 CX).
4. **Quality under noise:** more CX gave a lower expected cut under the provisional noise, with small gaps between B and A (+0.163 / +0.266 reduced, +0.049 / +0.106 native).

### 8.2 Design goals for Processor D
- At least 6 qubits, so PS-O1 fits natively without any reduction.
- Dense connectivity among the qubits that are used. Our instance has 12 of the 15 possible vertex pairs and two vertices of degree 5. B has 9 qubits but only 12 couplings, and its used qubits still needed 2.3 SWAPs on average, so spare qubits alone do not remove routing.
- Cycles and a high-degree hub. B's lower SWAP count came from cycles and a degree-5 hub, not from qubit count (A and B both used about 5 qubits on the 5-vertex problems).
- Same basis gates (rz, sx, x, cx) and the same noise as A and B, so only the topology differs and connectivity effects are not mixed with gate-set effects.

### 8.3 Proposal
Processor D: 6 physical qubits, two hub qubits (0 and 1) coupled to each other and to the four rim qubits (2, 3, 4, 5), and the rim qubits form a ring 2-3-4-5-2. That is 13 couplings out of the 15 possible; only (2,4) and (3,5) are missing.

**Hypothesis (not yet verified by transpilation):** our seed-42 instance is the complete graph on 6 vertices minus the three pairs (0,2), (0,4), (3,4). Two of those missing pairs, (0,2) and (3,4), are disjoint, so a layout exists where all 12 interacting pairs are direct couplings. We therefore expect 0 SWAPs and 24 CX on D (B: 24 CX plus about 2.3 SWAPs). A different dense 6-vertex instance may still need a SWAP.

**Trade-offs and uncertainty:** D has no spare qubits, 13 couplers are more hardware than B's 12 for 6 usable qubits, and the idea may not scale to larger graphs because the coupler count grows quickly. The expectation above must be tested with the same `seed_study` used for A and B before it counts as evidence.
