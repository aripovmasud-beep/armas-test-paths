"""RQ3 (Tables 16, 17): control-flow graphs of real Python functions.
Downloads the pinned PyPI releases of six projects (only parsed, never imported or run)
and uses six CPython 3.13 standard-library modules.
Usage: python experiments/rq3_real.py [--src real_src] [--out results/real_cfg.csv]"""
import argparse
import ast
import glob
import os
import subprocess
import sys
import sysconfig
import zipfile

from common import timed, write_csv
from armas import (armas, armas_mf, classical_mf, dfs_greedy, edges_of, is_cover,
                   is_valid_program_dag, lp_min, mccabe_basis, warm_start_mf)
from armas import cfg

PROJECTS = {"requests 2.32.3": "requests==2.32.3", "Flask 3.1.0": "flask==3.1.0",
            "Click 8.1.8": "click==8.1.8", "Jinja2 3.1.5": "jinja2==3.1.5",
            "Werkzeug 3.1.3": "werkzeug==3.1.3", "Rich 13.9.4": "rich==13.9.4"}
STDLIB_MODULES = ["argparse.py", "email", "http", "json", "logging", "urllib"]

ap = argparse.ArgumentParser()
ap.add_argument("--src", default="real_src")
ap.add_argument("--out", default="results/real_cfg.csv")
ap.add_argument("--only", default=None, help="run one project (substring of its name)")
args = ap.parse_args()

corpus = {}
os.makedirs(args.src, exist_ok=True)
for name, spec in PROJECTS.items():
    if args.only and args.only.lower() not in name.lower():
        continue
    d = os.path.join(args.src, spec.replace("==", "-"))
    if not os.path.isdir(d):
        os.makedirs(d)
        subprocess.check_call([sys.executable, "-m", "pip", "download", spec, "--no-deps",
                               "--only-binary", ":all:", "-d", d, "-q"])
        for whl in glob.glob(os.path.join(d, "*.whl")):
            zipfile.ZipFile(whl).extractall(d)
    corpus[name] = glob.glob(os.path.join(d, "**", "*.py"), recursive=True)
std = sysconfig.get_paths()["stdlib"]
if not args.only or args.only.lower() in "cpython":
    files = []
    for mod in STDLIB_MODULES:
        p = os.path.join(std, mod)
        files += [p] if mod.endswith(".py") else glob.glob(os.path.join(p, "**", "*.py"), recursive=True)
    corpus["CPython 3.13 stdlib (selected)"] = files

rows, skipped, total = [], 0, 0
for project, files in corpus.items():
    for f in sorted(files):
        try:
            tree = ast.parse(open(f, encoding="utf-8").read())
        except Exception:
            continue
        for fn in cfg.functions(tree):
            total += 1
            a = cfg.function_pam(fn)
            n = len(a) - 1
            m = len(edges_of(a))
            V = m - n + 2
            if V == 1:
                skipped += 1
                continue
            assert is_valid_program_dag(a), (f, fn.name)
            k = lp_min(a)
            A, D, M = armas(a), dfs_greedy(a), mccabe_basis(a)
            assert is_cover(A, a) and is_cover(D, a) and is_cover(M, a)
            (Pa, ph_a, _), t_a = timed(armas_mf, a)
            (Pd, ph_d, _), t_d = timed(warm_start_mf, a, dfs_greedy)
            (Pc, ph_c), t_c = timed(classical_mf, a)
            _, t_m = timed(mccabe_basis, a)
            for P in (Pa, Pd, Pc):
                assert is_cover(P, a) and len(P) == k
            rows.append(dict(project=project, file=os.path.basename(f), func=fn.name, n=n, m=m,
                             V=V, k_min=k, k_armas=len(A), k_dfs=len(D),
                             series_parallel=int(cfg.is_sp(a)),
                             phases_armas_mf=ph_a, phases_classical=ph_c, phases_dfs_mf=ph_d,
                             us_armas_mf=1e6 * t_a, us_classical=1e6 * t_c,
                             us_dfs_mf=1e6 * t_d, us_mccabe=1e6 * t_m))
    print(project, len(rows), flush=True)
print("functions total", total, "| without branching (V=1) excluded", skipped, "| kept", len(rows))
write_csv(args.out, rows)
print("ARMAS optimal", sum(r["k_armas"] == r["k_min"] for r in rows), "of", len(rows),
      "| not series-parallel", sum(1 - r["series_parallel"] for r in rows))
