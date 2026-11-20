"""RQ1, structured graphs (Tables 9, 10, 13): 1,560 graphs, six configurations, seed 2028.
Usage: python experiments/rq1_structured.py [--quick] [--out results/structured_configs.csv]"""
import argparse
import random

from common import timed, write_csv
from armas import armas, dfs_greedy, edges_of, is_cover, lp_min
from armas.generators import STRUCTURED_CONFIGS, structured

ap = argparse.ArgumentParser()
ap.add_argument("--quick", action="store_true", help="only n <= 200, 5 graphs per size")
ap.add_argument("--out", default="results/structured_configs.csv")
args = ap.parse_args()

sizes = [20, 50, 100, 200, 500, 1000, 2000, 5000]
rows = []
rng = random.Random(2028)
for name, (pe, pi, depth) in STRUCTURED_CONFIGS.items():
    for n in sizes:
        reps = 40 if n <= 1000 else 10
        for r in range(reps):
            a = structured(n, rng, pe, pi, depth)            # same random stream as full run
            if args.quick and (n > 200 or r >= 5):
                continue
            k = lp_min(a)
            A, tA = timed(armas, a)
            assert is_cover(A, a)
            D, tD = timed(dfs_greedy, a)
            rows.append(dict(config=name, n_target=n, n=len(a) - 1, m=len(edges_of(a)),
                             k_min=k, k_armas=len(A), k_dfs=len(D), t_armas=tA, t_dfs=tD))
    print("done:", name, flush=True)
write_csv(args.out, rows)
print("ARMAS optimal:", sum(r["k_armas"] == r["k_min"] for r in rows), "of", len(rows))
print("DFS optimal:  ", sum(r["k_dfs"] == r["k_min"] for r in rows), "of", len(rows))
