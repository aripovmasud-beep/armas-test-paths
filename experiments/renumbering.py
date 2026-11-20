"""Section 10.1: sensitivity to node numbering.  Fresh graphs are renumbered with a random
topological order and a random column order, then ARMAS is rerun.
Usage: python experiments/renumbering.py [--seed 31]"""
import argparse
import random

from common import write_csv
from armas import armas, is_cover, lp_min
from armas.generators import mixed, random_dag, renumber, structured

ap = argparse.ArgumentParser()
ap.add_argument("--seed", type=int, default=31)
ap.add_argument("--out", default="results/renumbering.csv")
args = ap.parse_args()

rng = random.Random(args.seed)
sets = {
    "structured": [structured(rng.choice([30, 60, 120, 250]), rng) for _ in range(300)],
    "random": [random_dag(rng.choice([50, 100, 200]), rng) for _ in range(150)],
    "mixed": [mixed(rng.choice([30, 60, 120, 250]), rng) for _ in range(300)],
}
rows = []
for family, graphs in sets.items():
    for a in graphs:
        b = renumber(a, rng)
        k = lp_min(b)
        P0, P = armas(a), armas(b)
        assert is_cover(P, b)
        rows.append(dict(family=family, k_min=k, k_original=len(P0), k_renumbered=len(P),
                         optimal_original=int(len(P0) == lp_min(a)), optimal_renumbered=int(len(P) == k)))
write_csv(args.out, rows)
for fam in sets:
    r = [x for x in rows if x["family"] == fam]
    print(fam, "optimal after renumbering", sum(x["optimal_renumbered"] for x in r), "/", len(r),
          "| original numbering", sum(x["optimal_original"] for x in r))
