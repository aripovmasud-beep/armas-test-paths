"""Graph helpers.

A program DAG is stored as a successor array (PAM) ``a`` of size (n + 1) x 3:
row ``a[i] = [0, adj1, adj2]`` holds the successors of node ``i`` (0 = no arc).
Nodes are numbered 1..n in topological order, s = 1 and t = n.
"""


def edges_of(a):
    """All arcs (i, j) of the PAM ``a``."""
    return [(i, a[i][c]) for i in range(1, len(a)) for c in (1, 2) if a[i][c] > 0]


def cyclomatic_complexity(a):
    """V(G) = m - n + 2."""
    return len(edges_of(a)) - (len(a) - 1) + 2


def is_cover(paths, a):
    """True if every path runs s -> t over arcs of G and the paths cover every arc."""
    n = len(a) - 1
    edges = set(edges_of(a))
    covered = set(e for p in paths for e in zip(p, p[1:]))
    return covered == edges and all(p[0] == 1 and p[-1] == n for p in paths)


def is_valid_program_dag(a):
    """Every node lies on some s-t path (forward and backward reachability)."""
    n = len(a) - 1
    edges = edges_of(a)
    forward = {1}
    for i in range(1, n + 1):
        if i in forward:
            forward |= {v for u, v in edges if u == i}
    backward = {n}
    for i in range(n, 0, -1):
        if any(u == i and v in backward for u, v in edges):
            backward.add(i)
    return forward == set(range(1, n + 1)) and backward == set(range(1, n + 1))
