"""Baselines: DFS greedy, one path per arc, McCabe basis paths."""
from .graph import edges_of


def dfs_greedy(a):
    """Greedy cover: every new path maximises the number of uncovered arcs, by dynamic
    programming over a DFS-based topological order.  O(m) per path."""
    n = len(a) - 1
    s, t = 1, n
    adj = {i: sorted(v for v in (a[i][1], a[i][2]) if v > 0) for i in range(1, n + 1)}
    order, seen = [], {s}
    stack = [(s, iter(adj[s]))]
    while stack:
        u, it = stack[-1]
        for v in it:
            if v not in seen:
                seen.add(v)
                stack.append((v, iter(adj[v])))
                break
        else:
            order.append(u)
            stack.pop()
    topo = order[::-1]
    uncovered = {(u, v) for u in adj for v in adj[u]}
    paths = []
    while uncovered:
        gain = {t: 0}
        nxt = {}
        for v in reversed(topo):
            for u in adj[v]:
                if u in gain:
                    val = gain[u] + ((v, u) in uncovered)
                    if val > gain.get(v, -1):
                        gain[v], nxt[v] = val, u
        p = [s]
        while p[-1] != t:
            v = p[-1]
            uncovered.discard((v, nxt[v]))
            p.append(nxt[v])
        paths.append(p)
    return paths


def one_path_per_arc(a):
    """For every arc (u, v): a BFS-tree path s ~> u, the arc, and a path v ~> t."""
    n = len(a) - 1
    adj = {i: [v for v in (a[i][1], a[i][2]) if v > 0] for i in range(1, n + 1)}
    parent = {1: None}
    queue = [1]
    for u in queue:
        for v in adj[u]:
            if v not in parent:
                parent[v] = u
                queue.append(v)
    to_t = {n: None}
    for u in range(n - 1, 0, -1):
        for v in adj[u]:
            if v in to_t:
                to_t[u] = v
                break

    def path_s(u):
        p = []
        while u is not None:
            p.append(u)
            u = parent[u]
        return p[::-1]

    def path_t(v):
        p = []
        while v is not None:
            p.append(v)
            v = to_t[v]
        return p

    return [path_s(u) + path_t(v) for u, v in edges_of(a)]


def mccabe_basis(a):
    """McCabe baseline method: a baseline path takes the first successor at every node;
    then every decision outcome not yet used is flipped once and the path continues along
    first successors.  Returns V(G) = m - n + 2 paths that cover all arcs."""
    n = len(a) - 1

    def cont(p):
        while p[-1] != n:
            p.append(a[p[-1]][1] if a[p[-1]][1] > 0 else a[p[-1]][2])
        return p

    base = cont([1])
    paths = [base]
    used = set(zip(base, base[1:]))
    k = 0
    while k < len(paths):
        P = paths[k]
        k += 1
        for idx in range(len(P) - 1):
            v = P[idx]
            for w in (a[v][1], a[v][2]):
                if w > 0 and (v, w) not in used:
                    q = cont(P[:idx + 1] + [w])
                    paths.append(q)
                    used.update(zip(q, q[1:]))
    return paths
