"""RQ1 and Table 8: 150 random DAGs (seed 2026) and 150 baseline structured DAGs (seed 2027),
n = 50..1,000, 30 graphs per size.  Counts decreasing paths needed by the reduction phase
for three starting covers.
Usage: python experiments/rq1_random_baseline.py [--out results/reduction_work.csv]"""
import argparse
import random

from common import write_csv
from armas import armas, dfs_greedy, is_cover, lp_min, one_path_per_arc
from armas.flow import unit_push_reduce
from armas.generators import random_dag, structured

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="results/reduction_work.csv")
args = ap.parse_args()

rows = []
for family, seed in (("random", 2026), ("structured", 2027)):
    rng = random.Random(seed)
    for n in (50, 100, 200, 500, 1000):
        for _ in range(30):
            a = (random_dag(n, rng) if family == "random"
                                                         else structured(n, rng))
            N = len(a) - 1
            k = lp_min(a)
            row = dict(family=family, n_target=n, n=N, k_min=k)
            for name, heuristic in (("armas", armas), ("dfs", dfs_greedy),
                                    ("one_path_per_arc", one_path_per_arc)):
                P = heuristic(a)
                assert is_cover(P, a)
                Q, pushes, _ = unit_push_reduce(P, N)
                assert len(Q) == k
                row["k_" + name] = len(P)
                row["pushes_" + name] = pushes
            rows.append(row)
    print("done:", family, flush=True)
write_csv(args.out, rows)
for fam in ("random", "structured"):
    r = [x for x in rows if x["family"] == fam]
    print(fam, "ARMAS optimal", sum(x["k_armas"] == x["k_min"] for x in r), "/", len(r),
          "| DFS optimal", sum(x["k_dfs"] == x["k_min"] for x in r),
          "| pushes: one path per arc", sum(x["pushes_one_path_per_arc"] for x in r),
          "DFS", sum(x["pushes_dfs"] for x in r), "ARMAS", sum(x["pushes_armas"] for x in r))
