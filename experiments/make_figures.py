"""Figures 2 and 3 of the paper from the timing CSV files.
Usage: python experiments/make_figures.py [--data data/paper] [--out figures]"""
import argparse
import csv
import os
import statistics as st
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="data/paper")
ap.add_argument("--out", default="figures")
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)

dinic = list(csv.DictReader(open(os.path.join(args.data, "timing_dinic.csv"))))
mc = list(csv.DictReader(open(os.path.join(args.data, "timing_mccabe.csv"))))
families = ["structured", "random", "mixed"]
sizes = sorted({int(r["n_target"]) for r in dinic})

# Figure 2: median per-graph speed-up of ARMAS-MF over Classical MF and over DFS + MF
fig, ax = plt.subplots(figsize=(7, 4))
for fam, ls in zip(families, ("-", "--", ":")):
    for base, color, label in (("ms_classical", "tab:blue", "Classical MF"),
                               ("ms_dfs_mf", "grey", "DFS + MF")):
        ys = []
        for n in sizes:
            ratios = [float(r[base]) / float(r["ms_armas_mf"]) for r in dinic
                      if r["family"] == fam and int(r["n_target"]) == n]
            ys.append(st.median(ratios))
        ax.plot(sizes, ys, ls, color=color, marker="o", ms=3, label=f"{fam}: vs {label}")
ax.set_xscale("log")
ax.set_xlabel("graph size n (nodes)")
ax.set_ylabel("median speed-up of ARMAS-MF")
ax.axhline(1, color="k", lw=0.5)
ax.legend(fontsize=7)
fig.tight_layout()
fig.savefig(os.path.join(args.out, "figure2_speedup.png"), dpi=200)

# Figure 3: median running time per family and size
fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
for ax, fam in zip(axes, families):
    for col, label, src in (("ms_classical", "Classical MF", dinic), ("ms_dfs_mf", "DFS + MF", dinic),
                            ("ms_armas_mf", "ARMAS-MF", dinic), ("ms_mccabe", "McCabe", mc)):
        ys = [st.median(float(r[col]) for r in src if r["family"] == fam and int(r["n_target"]) == n)
              for n in sizes]
        ax.plot(sizes, ys, marker="o", ms=3, label=label)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_title(fam); ax.set_xlabel("n")
axes[0].set_ylabel("median time, ms"); axes[0].legend(fontsize=7)
fig.tight_layout()
fig.savefig(os.path.join(args.out, "figure3_times.png"), dpi=200)
print("wrote figures to", args.out)
