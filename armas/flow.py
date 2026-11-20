"""Minimum-flow methods: ARMAS-MF (Algorithm 2), Classical MF (Ntafos-Hakimi) and the
same reduction started from any heuristic cover.

Two implementations of Phase 2 are given (Section 6.5 of the paper):

* ``unit_push_reduce``: one BFS per decreasing path, Algorithm 2 as written, with the
  certificate set S of Theorem 2;
* ``Dinic`` engine (``reduce_dinic``): Phase 2 as a maximum flow from t to s.  All
  timing experiments use this engine for every method.
"""
from collections import deque

from .armas import armas
from .graph import edges_of

INF = 10 ** 9


# --------------------------------------------------------------------------- unit pushes
def unit_push_reduce(paths, n):
    """Algorithm 2: reduce the covering flow of ``paths`` to a minimum flow.

    Returns ``(min_paths, pushes, S)``: a minimum edge path cover, the number of
    decreasing paths used, and the certificate set S of Theorem 2 (nodes not reached by
    the last, failing search)."""
    s, t = 1, n
    f = {}
    out = {i: [] for i in range(1, n + 1)}
    inn = {i: [] for i in range(1, n + 1)}
    for p in paths:
        for e in zip(p, p[1:]):
            if e not in f:
                f[e] = 0
                out[e[0]].append(e[1])
                inn[e[1]].append(e[0])
            f[e] += 1
    pushes = 0
    while True:
        prev = {t: None}
        q = [t]
        qi = 0
        while qi < len(q) and s not in prev:
            u = q[qi]
            qi += 1
            for y in out[u]:                     # u -> y along arc (u, y): f + 1
                if y not in prev:
                    prev[y] = (u, y, +1)
                    q.append(y)
            for x in inn[u]:                     # u -> x against arc (x, u): f - 1
                if f[(x, u)] > 1 and x not in prev:
                    prev[x] = (x, u, -1)
                    q.append(x)
        if s not in prev:
            break
        v = s
        while v != t:
            x, y, z = prev[v]
            f[(x, y)] += z
            v = x if z == +1 else y
        pushes += 1
    S = set(range(1, n + 1)) - set(prev)
    return _decompose(n, f, out), pushes, S


def verify_certificate(a, paths, S):
    """Check Theorem 2 in O(m): s in S, t not in S, no arc enters S, |delta+(S)| = |paths|."""
    n = len(a) - 1
    edges = edges_of(a)
    if 1 not in S or n in S:
        return False
    if any(u not in S and v in S for u, v in edges):
        return False
    return sum(1 for u, v in edges if u in S and v not in S) == len(paths)


def _decompose(n, flow_on, out):
    s, t = 1, n
    flow_on = dict(flow_on)
    res = []
    total = sum(flow_on[(s, y)] for y in out[s])
    for _ in range(total):
        p = [s]
        while p[-1] != t:
            u = p[-1]
            v = next(y for y in out[u] if flow_on[(u, y)] > 0)
            flow_on[(u, v)] -= 1
            p.append(v)
        res.append(p)
    return res


# --------------------------------------------------------------------------- Dinic engine
class Dinic:
    def __init__(self, n):
        self.n = n
        self.g = [[] for _ in range(n)]          # g[u] = list of edge ids
        self.to = []
        self.cap = []

    def add(self, u, v, c):
        self.g[u].append(len(self.to)); self.to.append(v); self.cap.append(c)
        self.g[v].append(len(self.to)); self.to.append(u); self.cap.append(0)
        return len(self.to) - 2

    def maxflow(self, s, t):
        """Returns (flow value, number of phases = level graphs built)."""
        flow = 0
        phases = 0
        while True:
            lvl = [-1] * self.n
            lvl[s] = 0
            q = deque([s])
            while q:
                u = q.popleft()
                for e in self.g[u]:
                    if self.cap[e] > 0 and lvl[self.to[e]] < 0:
                        lvl[self.to[e]] = lvl[u] + 1
                        q.append(self.to[e])
            if lvl[t] < 0:
                return flow, phases
            phases += 1
            it = [0] * self.n
            while True:                          # iterative blocking flow
                stack = [s]
                path = []
                while stack:
                    u = stack[-1]
                    if u == t:
                        break
                    advanced = False
                    while it[u] < len(self.g[u]):
                        e = self.g[u][it[u]]
                        v = self.to[e]
                        if self.cap[e] > 0 and lvl[v] == lvl[u] + 1:
                            stack.append(v)
                            path.append(e)
                            advanced = True
                            break
                        it[u] += 1
                    if not advanced:
                        stack.pop()
                        if path:
                            path.pop()
                            if stack:
                                it[stack[-1]] += 1
                        if not stack:
                            break
                if not stack or stack[-1] != t:
                    break
                f = min(self.cap[e] for e in path)
                for e in path:
                    self.cap[e] -= f
                    self.cap[e ^ 1] += f
                flow += f


def reduce_dinic(n, E, f0):
    """Phase 2 on the Dinic engine.  ``f0[(u, v)]`` is a covering flow; returns the
    minimum covering flow and the number of Dinic phases."""
    s, t = 1, n
    D = Dinic(n + 1)
    eid = {}
    for (u, v) in E:
        e = D.add(u, v, INF)                     # residual u -> v: unbounded
        D.cap[e ^ 1] = f0[(u, v)] - 1            # residual v -> u: f - lower bound
        eid[(u, v)] = e
    _, phases = D.maxflow(t, s)
    flow = {(u, v): 1 + D.cap[eid[(u, v)] ^ 1] for (u, v) in E}
    return flow, phases


def flow_from_paths(paths):
    f = {}
    for p in paths:
        for e in zip(p, p[1:]):
            f[e] = f.get(e, 0) + 1
    return f


def _paths_of(n, E, flow):
    out = {i: [] for i in range(1, n + 1)}
    for (u, v) in E:
        out[u].append(v)
    return _decompose(n, flow, out)


def warm_start_mf(a, heuristic):
    """Heuristic cover, then the Dinic reduction.  Returns (paths, dinic phases, k')."""
    n = len(a) - 1
    E = edges_of(a)
    P = heuristic(a)
    flow, phases = reduce_dinic(n, E, flow_from_paths(P))
    return _paths_of(n, E, flow), phases, len(P)


def armas_mf(a):
    """ARMAS-MF (Algorithm 2) on the Dinic engine.  Returns (paths, phases, k')."""
    return warm_start_mf(a, armas)


def classical_mf(a):
    """Classical minimum flow (Ntafos-Hakimi, lower bound 1): feasible flow from the lower
    bounds with a super-source, a super-sink and a circulation arc t -> s, then the same
    reduction.  Returns (paths, dinic phases)."""
    n = len(a) - 1
    E = edges_of(a)
    s, t = 1, n
    bal = [0] * (n + 3)
    SS, TT = n + 1, n + 2
    D = Dinic(n + 3)
    eid = {}
    for (u, v) in E:
        eid[(u, v)] = D.add(u, v, INF)           # part above the lower bound
        bal[v] += 1
        bal[u] -= 1
    D.add(t, s, INF)                              # circulation arc
    need = 0
    for v in range(1, n + 1):
        if bal[v] > 0:
            D.add(SS, v, bal[v])
            need += bal[v]
        elif bal[v] < 0:
            D.add(v, TT, -bal[v])
    f1, ph1 = D.maxflow(SS, TT)
    assert f1 == need, "no feasible covering flow"
    f0 = {(u, v): 1 + (INF - D.cap[eid[(u, v)]]) for (u, v) in E}
    flow, ph2 = reduce_dinic(n, E, f0)
    return _paths_of(n, E, flow), ph1 + ph2
