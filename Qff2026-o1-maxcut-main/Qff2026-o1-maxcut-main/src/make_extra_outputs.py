"""Extra Phase 1 outputs built from the existing result tables:
guide-named CSVs, logical-vs-transpiled and trade-off figures, transpiled circuit text."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from qiskit import transpile

from src.metrics import circuit_metrics
from src.problem import load_edges
from src.processors import load_processor
from src.qaoa_circuit import build_qaoa_circuit
from src.routing import STUDY_BASIS, transpile_for_study

TAB, FIG, CIRC = Path("results/tables"), Path("results/figures"), Path("results/circuits")
for d in (TAB, FIG, CIRC):
    d.mkdir(parents=True, exist_ok=True)

procs = {p["name"]: p for p in (load_processor("processors/processor_A.json"),
                                load_processor("processors/processor_B.json"))}
best = json.loads((TAB / "best_params.json").read_text())
n5 = json.loads((TAB / "native5_params.json").read_text())
circuits = {
    "full_6q": build_qaoa_circuit(best["full"]["gamma"], best["full"]["beta"],
                                  load_edges("data/raw/instance_seed42.txt"), {}, 6),
    "native_5q": build_qaoa_circuit(n5["gamma"], n5["beta"],
                                    load_edges("data/raw/instance5_seed42.txt"), {}, 5),
}

# 1) transpiled circuits as text (seed 0): logical vs Processor A vs Processor B
for name, qc in circuits.items():
    (CIRC / f"{name}_logical.txt").write_text(str(qc.draw(output="text", fold=140)))
    for pn, proc in procs.items():
        if qc.num_qubits <= proc["num_qubits"]:
            tqc = transpile_for_study(qc, proc, seed=0)
            (CIRC / f"{name}_{pn}_seed0.txt").write_text(str(tqc.draw(output="text", fold=140)))

# 2) guide-named tables
cols = ["depth", "cx", "swap", "effective_cx", "qubits_used"]
tr = pd.concat([pd.read_csv(TAB / "transpile_summary.csv"),
                pd.read_csv(TAB / "native5_transpile_summary.csv")])
agg = tr.groupby(["problem", "processor"])[cols].agg(["mean", "std"])
agg.columns = [f"{a}_{b}" for a, b in agg.columns]
agg = agg.reset_index()
for pn in procs:
    agg[agg["processor"] == pn].to_csv(TAB / f"{pn}_metrics.csv", index=False)

a = agg[agg["processor"] == "processor_A"].set_index("problem")
b = agg[agg["processor"] == "processor_B"].set_index("problem")
common = a.index.intersection(b.index)
comp = pd.DataFrame(index=common)
for c in cols:
    comp[f"{c}_A"] = a.loc[common, f"{c}_mean"]
    comp[f"{c}_B"] = b.loc[common, f"{c}_mean"]
    comp[f"{c}_B_minus_A"] = comp[f"{c}_B"] - comp[f"{c}_A"]
comp.round(3).reset_index().to_csv(TAB / "AB_comparison.csv", index=False)

q1 = pd.read_csv(TAB / "quality_summary.csv")
q1 = q1[q1["status"] == "ok"]
q2 = pd.read_csv(TAB / "native5_quality_summary.csv")
q2.insert(0, "problem", "native_5q")
keep = ["problem", "case", "processor", "two_qubit_error", "expected_cut",
        "expected_cut_std", "ratio", "p_optimal", "p_optimal_std"]
fin = pd.concat([q1[keep], q2[keep]])
fin.to_csv(TAB / "final_comparison.csv", index=False)

# 3) logical_vs_transpiled.png: all-to-all (no routing) vs A vs B
rows = []
for name, qc in circuits.items():
    t = transpile(qc, basis_gates=STUDY_BASIS, optimization_level=1, seed_transpiler=0)
    m = circuit_metrics(t)
    rows.append((name, "all-to-all", m["depth"], m["two_qubit_gates"]))
    for pn in procs:
        s = agg[(agg["problem"] == name) & (agg["processor"] == pn)]
        if len(s):
            rows.append((name, pn.replace("processor_", ""),
                         s["depth_mean"].iloc[0], s["effective_cx_mean"].iloc[0]))
colors = {"all-to-all": "#999999", "A": "#4c78a8", "B": "#f58518"}
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
for ax, idx, title in [(axes[0], 2, "Depth"), (axes[1], 3, "Effective CX (cx + 3 swap)")]:
    ax.bar(range(len(rows)), [r[idx] for r in rows], color=[colors[r[1]] for r in rows])
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels([f"{r[0]}\n{r[1]}" for r in rows], fontsize=7)
    ax.set_title(title)
    for i, r in enumerate(rows):
        ax.text(i, r[idx], f"{r[idx]:.1f}", ha="center", va="bottom", fontsize=7)
fig.suptitle("Logical (all-to-all) vs transpiled on A and B (mean of 20 seeds)")
fig.tight_layout()
fig.savefig(FIG / "logical_vs_transpiled.png", dpi=200)
plt.close(fig)

# 4) architecture_tradeoffs.png: quality loss vs routing cost
ideal = fin[fin["case"] == "ideal"].set_index("problem")["ratio"]
noisy = fin[fin["case"] == "noisy"].copy()
noisy["loss"] = noisy["problem"].map(ideal) - noisy["ratio"]
noisy = noisy.merge(agg[["problem", "processor", "effective_cx_mean"]],
                    on=["problem", "processor"])
marks = {"full_6q": "s", "reduced_5q": "o", "native_5q": "^"}
fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
for ax, p2 in zip(axes, [0.005, 0.01]):
    sub = noisy[noisy["two_qubit_error"] == p2]
    for _, r in sub.iterrows():
        col = "#4c78a8" if r["processor"] == "processor_A" else "#f58518"
        ax.scatter(r["effective_cx_mean"], r["loss"], marker=marks[r["problem"]],
                   color=col, s=70)
        ax.annotate(f'{r["problem"]} {r["processor"][-1]}',
                    (r["effective_cx_mean"], r["loss"]), fontsize=7,
                    xytext=(4, 4), textcoords="offset points")
    ax.set_title(f"2q error {p2} (provisional)")
    ax.set_xlabel("effective CX after routing")
axes[0].set_ylabel("ratio loss vs ideal")
fig.suptitle("Routing cost vs quality loss (blue = A, orange = B)")
fig.tight_layout()
fig.savefig(FIG / "architecture_tradeoffs.png", dpi=200)
plt.close(fig)

print("saved tables:", sorted(p.name for p in TAB.glob("*.csv")))
print("saved figures:", sorted(p.name for p in FIG.glob("*.png")))
print("saved circuits:", sorted(p.name for p in CIRC.glob("*.txt")))

# 5) Benchmark rows in the organizers' column naming, incl. the 6-vertex row for Processor A
NOT_RUN = "not run: needs N > 5 qubits"
ids = {"full_6q": "ps_o1_seed42", "reduced_5q": "ps_o1_seed42_reduced5_NOT_APPROVED",
       "native_5q": "native5_seed42_extra"}
nq = {"full_6q": 6, "reduced_5q": 5, "native_5q": 5}
brow = []
for prob in ["full_6q", "reduced_5q", "native_5q"]:
    for pn in ["processor_A", "processor_B"]:
        s = agg[(agg["problem"] == prob) & (agg["processor"] == pn)]
        base = dict(instance_id=ids[prob], processor=pn, logical_qubits=nq[prob])
        if len(s):
            r = s.iloc[0]
            brow.append({**base, "cx_count": r["cx_mean"], "depth": r["depth_mean"],
                         "swap_count": r["swap_mean"], "effective_cx": r["effective_cx_mean"],
                         "noise_model": "transpile only (20 seeds, swap kept in basis)", "note": ""})
        else:
            brow.append({**base, "cx_count": "", "depth": "", "swap_count": "", "effective_cx": "",
                         "noise_model": NOT_RUN,
                         "note": "full problem runs on B only; A is a capacity reference"})
pd.DataFrame(brow).to_csv(TAB / "benchmark_rows.csv", index=False)

fin2 = pd.read_csv(TAB / "final_comparison.csv")
fin2["logical_qubits"] = fin2["problem"].map(nq)
fin2["noise_model"] = fin2["case"].map({"ideal": "ideal statevector",
                                        "noisy": "depolarizing + readout (provisional)"})
extra = pd.DataFrame([dict(problem="full_6q", case="noisy", processor="processor_A",
                           logical_qubits=6, noise_model=NOT_RUN)])
pd.concat([fin2, extra], ignore_index=True).to_csv(TAB / "final_comparison.csv", index=False)
print("saved benchmark_rows.csv and A row in final_comparison.csv")
