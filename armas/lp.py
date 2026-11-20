"""Exact minimum edge path cover by linear programming (ground truth)."""
from .graph import edges_of


def lp_min(a):
    """k* by the minimum-flow LP with f(e) >= 1, solved by HiGHS through SciPy.

    The constraint matrix is a node-arc incidence matrix, hence totally unimodular, so
    the LP optimum is integral and equals k*.  The LP shares no code with the
    heuristics, so it checks them independently."""
    import numpy as np
    from scipy.optimize import linprog
    from scipy.sparse import lil_matrix
    E = edges_of(a)
    n = len(a) - 1
    m = len(E)
    A = lil_matrix((n - 2, m))
    row = {v: k for k, v in enumerate(range(2, n))}
    for k, (u, v) in enumerate(E):
        if u in row:
            A[row[u], k] += 1
        if v in row:
            A[row[v], k] -= 1
    c = np.array([1.0 if u == 1 else 0.0 for u, v in E])
    r = linprog(c, A_eq=A.tocsr(), b_eq=np.zeros(n - 2), bounds=[(1, None)] * m, method="highs")
    return int(round(r.fun))
