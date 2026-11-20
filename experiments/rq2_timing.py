"""RQ2 (Tables 14, 15, 18): 348 timing graphs, seed 2029 (structured, random, mixed; sizes
50..5,000).  Every method runs on the same Dinic engine; best of 3 runs per method.
Usage: python experiments/rq2_timing.py [--max-n 5000] [--out results/timing.csv]"""
import argparse
import random

from common import timed, write_csv
from armas import (armas, armas_mf, classical_mf, dfs_greedy, edges_of, is_cover, lp_min,
                   mccabe_basis, warm_start_mf)
from armas.generators import mixed, random_dag, structured

ap = argparse.ArgumentParser()
ap.add_argument("--max-n", type=int, default=5000, help="skip sizes above this (quick check)")
ap.add_argument("--out", default="results/timing.csv")
args = ap.parse_args()

families = [("structured", lambda n, r: structured(n, r)),
            ("random", lambda n, r: random_dag(n, r)),
            ("mixed", lambda n, r: mixed(n, r))]
rng = random.Random(2029)
rows = []
for family, gen in families:
    for n in (50, 100, 200, 500, 1000, 2000, 5000):
        for _ in range(20 if n <= 1000 else 8):
            a = gen(n, rng)                                  # always generate: keeps the stream
            if n > args.max_n:
                continue
            N = len(a) - 1
            m = len(edges_of(a))
            k = lp_min(a)
            (Pc, ph_c), t_c = timed(classical_mf, a)
            (Pa, ph_a, ka), t_a = timed(armas_mf, a)
            (Pd, ph_d, kd), t_d = timed(warm_start_mf, a, dfs_greedy)
            M, t_m = timed(mccabe_basis, a)
            for P in (Pc, Pa, Pd):
                assert is_cover(P, a) and len(P) == k
            assert is_cover(M, a) and len(M) == m - N + 2
            rows.append(dict(family=family, n_target=n, n=N, m=m, V=m - N + 2, k_min=k,
                             k_armas=ka, k_dfs=kd, k_mccabe=len(M),
                             phases_classical=ph_c, phases_dfs_mf=ph_d, phases_armas_mf=ph_a,
                             ms_classical=1000 * t_c, ms_dfs_mf=1000 * t_d,
                             ms_armas_mf=1000 * t_a, ms_mccabe=1000 * t_m))
        print(family, n, "ok", flush=True)
write_csv(args.out, rows)
