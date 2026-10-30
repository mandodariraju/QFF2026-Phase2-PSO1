import json
from pathlib import Path

import pandas as pd

from src.problem import load_edges, reduce_fix_vertex
from src.processors import load_processor
from src.qaoa_circuit import build_qaoa_circuit
from src.routing import seed_study

params = json.loads(Path("results/tables/best_params.json").read_text())
all_edges = load_edges("data/raw/instance_seed42.txt")
red_edges, linear, kept = reduce_fix_vertex(all_edges, 6, fixed=4)

procs = [load_processor("processors/processor_A.json"),
         load_processor("processors/processor_B.json")]

circuits = {
    "full_6q": build_qaoa_circuit(params["full"]["gamma"], params["full"]["beta"],
                                  all_edges, {}, 6),
    "reduced_5q": build_qaoa_circuit(params["reduced"]["gamma"], params["reduced"]["beta"],
                                     red_edges, linear, 5),
}

frames, notes = [], []
for pname, qc in circuits.items():
    for proc in procs:
        try:
            df = seed_study(qc, proc)   # 20 seeds, same optimization level
            df["problem"] = pname
            frames.append(df)
        except Exception as e:
            notes.append(f"{pname} on {proc['name']}: cannot be transpiled "
                         f"({type(e).__name__}: {e})")

Path("results/tables").mkdir(parents=True, exist_ok=True)
out = pd.concat(frames)
out.to_csv("results/tables/transpile_summary.csv", index=False)
Path("results/tables/feasibility_notes.txt").write_text("\n".join(notes))

cols = ["depth", "cx", "swap", "effective_cx", "qubits_used"]
print(out.groupby(["problem", "processor"])[cols].agg(["mean", "std"]).round(2))
print("\n".join(notes))
