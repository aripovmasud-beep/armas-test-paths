"""RQ1/RQ4: 3,000 small arbitrary DAGs (seed 7) and 600 mixed graphs (seed 11).
Usage: python experiments/rq1_small_mixed.py [--out results/small_mixed.csv]"""
import argparse
import random

from common import write_csv
from armas import armas, dfs_greedy, edges_of, is_cover, lp_min
from armas.generators import mixed, small_arbitrary

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="results/small_mixed.csv")
args = ap.parse_args()

rng = random.Random(7)
small = [small_arbitrary(rng) for _ in range(3000)]
rng = random.Random(11)
mix = []
for _ in range(600):
    n_target = rng.choice([30, 60, 120, 250])
    mix.append(mixed(n_target, rng))

rows = []
for family, graphs in (("small", small), ("mixed", mix)):
    for a in graphs:
        k = lp_min(a)
        A = armas(a)
        D = dfs_greedy(a)
        assert is_cover(A, a)
        rows.append(dict(family=family, n=len(a) - 1, m=len(edges_of(a)), k_min=k,
                         k_armas=len(A), k_dfs=len(D)))
write_csv(args.out, rows)
for fam in ("small", "mixed"):
    r = [x for x in rows if x["family"] == fam]
    print(fam, "ARMAS optimal", sum(x["k_armas"] == x["k_min"] for x in r), "/", len(r),
          "| DFS optimal", sum(x["k_dfs"] == x["k_min"] for x in r))
print("ARMAS failures:")
for x in rows:
    if x["k_armas"] > x["k_min"]:
        print("  ", x)
