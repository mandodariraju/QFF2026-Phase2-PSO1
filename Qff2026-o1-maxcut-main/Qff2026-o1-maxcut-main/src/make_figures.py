from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIG = Path("results/figures")
TAB = Path("results/tables")
FIG.mkdir(parents=True, exist_ok=True)


def need(df, cols, name):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise SystemExit(f"{name} lo columns missing: {missing}. Found: {list(df.columns)}")


def fig_architecture():
    df = pd.read_csv(TAB / "transpile_summary.csv")
    metrics = ["depth", "cx", "swap", "effective_cx"]
    need(df, ["problem", "processor"] + metrics, "transpile_summary.csv")
    g = df.groupby(["problem", "processor"])[metrics].agg(["mean", "std"])
    labels = [f"{p}\n{q}" for p, q in g.index]
    fig, axes = plt.subplots(1, 4, figsize=(15, 4))
    for ax, m in zip(axes, metrics):
        mean, std = g[(m, "mean")].values, g[(m, "std")].fillna(0).values
        ax.bar(range(len(labels)), mean, yerr=std, capsize=3, color="#7fa8d9")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=8)
        ax.set_title(m + " (mean +/- std, 20 seeds)", fontsize=9)
        for i, v in enumerate(mean):
            ax.text(i, v, f"{v:.1f}", ha="center", va="bottom", fontsize=8)
    fig.suptitle("Routing cost: Processor A vs B (full_6q on A cannot be transpiled)")
    fig.tight_layout()
    fig.savefig(FIG / "AB_architecture_metrics.png", dpi=200)
    plt.close(fig)


def fig_performance():
    df = pd.read_csv(TAB / "quality_summary.csv")
    need(df, ["problem", "case", "processor", "two_qubit_error", "expected_cut",
              "expected_cut_std", "ratio", "p_optimal", "p_optimal_std", "status"],
         "quality_summary.csv")
    df = df[df["status"] == "ok"]
    bars = []  # (label, ratio, ratio_std, p_opt, p_std, color)
    for prob in ["full_6q", "reduced_5q"]:
        sub = df[df["problem"] == prob]
        ideal = sub[sub["case"] == "ideal"]
        if len(ideal):
            r = ideal.iloc[0]
            bars.append((f"{prob}\nideal", r["ratio"], 0, r["p_optimal"], 0, "#999999"))
        noisy = sub[sub["case"] == "noisy"].sort_values(["processor", "two_qubit_error"])
        for _, r in noisy.iterrows():
            short = r["processor"].replace("processor_", "")
            color = "#4c78a8" if short == "A" else "#f58518"
            opt = float(df[(df["problem"] == prob) & (df["case"] == "ideal")]["expected_cut"].iloc[0]
                        / df[(df["problem"] == prob) & (df["case"] == "ideal")]["ratio"].iloc[0])
            bars.append((f"{prob}\n{short} p2={r['two_qubit_error']}", r["ratio"],
                         r["expected_cut_std"] / opt, r["p_optimal"], r["p_optimal_std"], color))
    x = np.arange(len(bars))
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
    axes[0].bar(x, [b[1] for b in bars], yerr=[b[2] for b in bars], capsize=3,
                color=[b[5] for b in bars])
    axes[0].set_title("Approximation ratio (expected cut / optimum 29)")
    axes[0].set_ylim(0.7, 0.9)
    axes[1].bar(x, [b[3] for b in bars], yerr=[b[4] for b in bars], capsize=3,
                color=[b[5] for b in bars])
    axes[1].set_title("Probability of an optimal bitstring (incl. complement)")
    for ax, idx in zip(axes, [1, 3]):
        ax.set_xticks(x)
        ax.set_xticklabels([b[0] for b in bars], fontsize=7)
        for i, b in enumerate(bars):
            ax.text(i, b[idx], f"{b[idx]:.3f}", ha="center", va="bottom", fontsize=7)
    fig.suptitle("Solution quality (grey=ideal, blue=A, orange=B; provisional noise)")
    fig.tight_layout()
    fig.savefig(FIG / "AB_performance.png", dpi=200)
    plt.close(fig)


def fig_restarts():
    path = TAB / "restarts.csv"
    if not path.exists():
        print("restarts.csv ledu, skipping restarts figure")
        return
    df = pd.read_csv(path)
    need(df, ["problem", "restart", "expected_cut"], "restarts.csv")
    fig, ax = plt.subplots(figsize=(6, 4))
    for prob, sub in df.groupby("problem"):
        ax.plot(sub["restart"], sub["expected_cut"], "o-", label=prob)
    ax.axhline(19.5, color="gray", ls="--", label="random baseline 19.5")
    ax.axhline(29, color="green", ls=":", label="classical optimum 29")
    ax.set_xlabel("restart (seed)")
    ax.set_ylabel("expected cut")
    ax.set_title("QAOA p=1, COBYLA: 10 random restarts")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "restarts.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    fig_architecture()
    fig_performance()
    fig_restarts()
    print("figures saved:", sorted(p.name for p in FIG.glob("*.png")))
