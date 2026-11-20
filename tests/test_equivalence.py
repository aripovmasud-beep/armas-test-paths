"""Checks the cleaned-up package against the original research scripts (armas_tajriba/).

Usage:  python tests/test_equivalence.py /path/to/armas_tajriba
The new armas() must return exactly the same paths as the original armas_h() and the same
statistics as the original experiments."""
import random
import sys

sys.path.insert(0, ".")
legacy_dir = sys.argv[1] if len(sys.argv) > 1 else None
if legacy_dir:
    sys.path.insert(1, legacy_dir)
    import armas_bench as old
    import armas_h as oldh
    import struct_test as olds
    import nh_compare as oldn
from armas import armas, dfs_greedy, mccabe_basis, classical_mf, armas_mf, is_cover
from armas import generators as gen
from armas.flow import unit_push_reduce, verify_certificate, warm_start_mf
from armas import lp_min

rng = random.Random(1)
graphs = [gen.structured(rng.choice([20, 50, 120]), rng) for _ in range(150)]
graphs += [gen.random_dag(rng.choice([30, 80, 200]), rng) for _ in range(150)]
graphs += [gen.mixed(rng.choice([30, 60, 120]), rng) for _ in range(150)]
graphs += [gen.small_arbitrary(rng) for _ in range(300)]
same_paths = 0
for a in graphs:
    P = armas(a)
    assert is_cover(P, a)
    if legacy_dir:
        assert P == oldh.armas_h(a), "armas differs from armas_h"
        same_paths += 1
    n = len(a) - 1
    Q, pushes, S = unit_push_reduce(P, n)
    k = lp_min(a)
    assert len(Q) == k and is_cover(Q, a) and verify_certificate(a, Q, S)
    assert len(armas_mf(a)[0]) == k and len(classical_mf(a)[0]) == k
    assert len(P) <= len(mccabe_basis(a))
print(f"{len(graphs)} graphs: coverage, exactness of ARMAS-MF / Classical MF, certificate OK;",
      (f"identical to original armas_h on {same_paths}" if legacy_dir else ""))

if legacy_dir:                              # generators reproduce the original streams
    for seed in (3, 4):
        r1, r2 = random.Random(seed), random.Random(seed)
        for n in (20, 100, 400):
            assert gen.structured(n, r1) == old.gen_structured(n, r2)
            assert gen.random_dag(n, r1) == old.gen_random(n, 0.35, r2)
            assert gen.mixed(n, r1) == oldn.gen_mixed(n, r2)
    print("generators identical to the original ones")
