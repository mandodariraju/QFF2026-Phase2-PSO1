# QFF 2026 Phase 2: PS-O1 Max-Cut with QAOA

**Team:** [GARUDA]
**Problem statement:** PS-O1, Quantum Optimization of Network Partitioning Using QAOA
(same team and same problem statement as Phase 1)

## Summary

We formulate Max-Cut on the locked 6-vertex weighted graph (9 edges, total weight 27)
as a QUBO, solve it with QAOA (p = 1, 5 seeded initializations), and benchmark it on
Processor A, Processor B and our custom Processor D, ideal and noisy, against the
exact classical optimum (C* = 22).

## How to run

Python 3.10 to 3.12.

```bash
git clone [REPO URL]
cd [REPO FOLDER]
python -m venv opt-env
source opt-env/bin/activate        # Windows: opt-env\Scripts\activate
pip install -r requirements.txt
jupyter notebook main.ipynb        # Run All, runs top to bottom (about [X] minutes)
```

`RECOMPUTE = False` in the notebook reloads saved slow outputs from `results/`.
Set it to `True` to recompute everything.

## Repository layout

| Path | Content |
|---|---|
| `main.ipynb` | Full pipeline: formulation, QUBO, QAOA, benchmarks, Bell state |
| `qff_phase2.py` | Organizer starter module (unchanged) |
| `data/instance.json` | Locked PS-O1 instance |
| `processors/` | Processor A, B and our frozen Processor D |
| `results/tables/` | `results.csv` (benchmarks), `bell.csv` (Bell state) |
| `results/figures/` | Figures used in the report |
| `report.md` | Final report |

## Official settings (not changed)

Basis gates rz, sx, x, cx. Transpiler optimization_level 1 with SABRE, seed_transpiler 42.
AerSimulator seed 42. 4096 shots. Noise: 1-qubit depolarizing 0.001, 2-qubit depolarizing
0.005, readout flip 0.01. Initialization seeds 0, 1, 2, 3, 4.

## Key results

C* = 22. Optimal partitions: (0,0,1,0,1,1) and its complement (1,1,0,1,0,0).
Random baseline: r = 0.614, P_opt = 0.031.

| Processor | Condition | Best cut | r | r_best | P_opt | CX | Depth | SWAPs |
|---|---|---|---|---|---|---|---|---|
| A | ideal / noisy | not executable (needs 6 qubits, has 5) | - | - | - | - | - | - |
| B | ideal | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| B | noisy | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| D | ideal | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| D | noisy | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

Consistency over 5 seeds: r = [mean] ± [std].

## Bell state (Processor D)

| Pair | Distance | Condition | F ± SE |
|---|---|---|---|
| [adjacent pair] | 1 | ideal / noisy | [ ] |
| [farthest pair] | [ ] | ideal / noisy | [ ] |

Full table: `results/tables/bell.csv`.

## Processor D

[2 to 3 lines: topology, which A/B bottleneck it fixes, one trade-off.]
Full justification is in `report.md`.

## Report

See [`report.md`](report.md).

## AI tools disclosure

[Example: "We used Claude (Anthropic) to help understand the problem statement, structure
the repository and review code. We verified all results and take responsibility for
the correctness of the work."] Meeru actually vaadina tools, edi kosam vaadaro vrayandi.
