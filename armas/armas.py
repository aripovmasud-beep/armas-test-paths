"""Algorithm 1 of the paper: ARMAS.

One-pass heuristic for an edge path cover of a program DAG.  Each path follows the
successor with the largest index.  Covered arcs are removed from a working copy of
the successor array by three degree rules:

* g-arc (d+(i) > 1 and d-(j) > 1): removed at once; stops watching any h-arc;
* h-arc (d+(i) > 1 and d-(j) = 1): only watched;
* safe h-rule: when a path reaches a merge node while watching an h-arc, the watched
  h-arc is removed.
"""


def armas(a0):
    """Return a list of s-t paths (lists of node numbers) that covers every arc.

    ``a0`` is the PAM of the graph; it is not modified.  Runs in O(k' * n) time and
    returns at most V(G) = m - n + 2 paths (Theorem 1).
    """
    a = [row[:] for row in a0]
    n = len(a) - 1
    vix = [0] * (n + 1)          # out-degrees d+
    w = [0] * (n + 1)            # in-degrees d-
    for i in range(1, n + 1):
        for c in (1, 2):
            if a[i][c] > 0:
                vix[i] += 1
                w[a[i][c]] += 1
    m = sum(vix)
    paths = []
    g = 1
    guard = 0
    while g != 0:
        guard += 1
        if guard > m + 5:                      # cannot happen by Theorem 1
            raise RuntimeError("ARMAS did not terminate")
        g = 0
        path = [1]
        i = 1
        watched = None                          # the watched h-arc
        while i != n:
            j = max(a[i][1], a[i][2])
            path.append(j)
            branching = vix[i] > 1              # evaluated before any update
            if branching and w[j] > 1:          # g-arc
                _remove(a, i, j)
                vix[i] -= 1
                w[j] -= 1
                g = 1
                watched = None
            elif branching and w[j] == 1:       # h-arc: start watching
                watched = (i, j)
            elif watched is not None and w[j] > 1:      # safe h-rule
                ci, cj = watched
                _remove(a, ci, cj)
                vix[ci] -= 1
                w[cj] -= 1
                w[j] -= 1
                g = 1
                watched = None
            i = j
        paths.append(path)
    return paths


def _remove(a, i, j):
    a[i][1 if a[i][1] == j else 2] = 0
