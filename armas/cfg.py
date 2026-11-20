"""Build acyclic CFGs (PAM form) of Python functions, following Section 7.2."""
import ast, heapq

class B:
    def __init__(s): s.succ = []
    def new(s): s.succ.append([]); return len(s.succ) - 1
    def edge(s, u, v): s.succ[u].append(v)
    def link(s, preds, v):
        for u in preds: s.edge(u, v)

def build(g, stmts, preds, ctx):
    """returns dangling nodes after the block"""
    for st in stmts:
        preds = stmt(g, st, preds, ctx)
    return preds

def stmt(g, st, preds, ctx):
    T = ctx['T']
    if isinstance(st, ast.If):
        t = g.new(); g.link(preds, t)
        d1 = build(g, st.body, [t], ctx)
        d2 = build(g, st.orelse, [t], ctx) if st.orelse else [t]
        return d1 + d2
    if isinstance(st, (ast.For, ast.AsyncFor, ast.While)):
        t = g.new(); g.link(preds, t)
        sub = dict(ctx, brk=[], cont=[])
        d = build(g, st.body, [t], sub)
        normal = [t] + d + sub['cont']
        if st.orelse: normal = build(g, st.orelse, normal, ctx)
        return normal + sub['brk']
    if isinstance(st, (ast.Try, getattr(ast, 'TryStar', ast.Try))):
        ts = g.new(); g.link(preds, ts)
        d = build(g, st.body, [ts], ctx)
        if st.orelse: d = build(g, st.orelse, d, ctx)
        hs = st.handlers; prev = ts; out = list(d)
        for k, h in enumerate(hs):
            if k < len(hs) - 1:
                disp = g.new(); g.edge(prev, disp)   # dispatch node
                out += build(g, h.body, [disp], ctx); prev = disp
            else:
                out += build(g, h.body, [prev], ctx)
        if st.finalbody: out = build(g, st.finalbody, out, ctx)
        return out
    if isinstance(st, (ast.With, ast.AsyncWith)):
        w = g.new(); g.link(preds, w)
        return build(g, st.body, [w], ctx)
    if isinstance(st, ast.Match):
        s0 = g.new(); g.link(preds, s0); prev = s0; out = []
        for k, c in enumerate(st.cases):
            ct = g.new(); g.edge(prev, ct)
            out += build(g, c.body, [ct], ctx); prev = ct
        wild = isinstance(st.cases[-1].pattern, ast.MatchAs) and st.cases[-1].pattern.pattern is None and st.cases[-1].guard is None
        if not wild: out.append(prev)
        return out
    if isinstance(st, (ast.Return, ast.Raise)):
        r = g.new(); g.link(preds, r); g.edge(r, T); return []
    if isinstance(st, ast.Break):
        b = g.new(); g.link(preds, b); ctx['brk'].append(b); return []
    if isinstance(st, ast.Continue):
        c = g.new(); g.link(preds, c); ctx['cont'].append(c); return []
    x = g.new(); g.link(preds, x); return [x]

def function_pam(fn):
    g = B(); s = g.new(); T = g.new()
    ctx = dict(T=T, brk=[], cont=[])
    d = build(g, fn.body, [s], ctx); g.link(d, T)
    # reachable from s
    seen = {s}; st = [s]
    while st:
        u = st.pop()
        for v in g.succ[u]:
            if v not in seen: seen.add(v); st.append(v)
    succ = {u: [v for v in g.succ[u] if v in seen] for u in seen}
    # parallel arcs -> insert a node on the second copy
    nxt = max(succ) + 1
    for u in list(succ):
        vs = succ[u]
        if len(vs) == 2 and vs[0] == vs[1]:
            succ[nxt] = [vs[1]]; succ[u] = [vs[0], nxt]; nxt += 1
    for u, vs in succ.items():
        assert len(vs) <= 2, ("deg", vs)
    # topological numbering, creation order as tie-break; s first, T last
    indeg = {u: 0 for u in succ}
    for u in succ:
        for v in succ[u]: indeg[v] += 1
    h = [s]; order = []
    while h:
        u = heapq.heappop(h); order.append(u)
        for v in succ[u]:
            indeg[v] -= 1
            if indeg[v] == 0 and v != T: heapq.heappush(h, v)
    order.append(T)
    assert len(order) == len(succ) and order[0] == s and order[-1] == T, "order"
    lab = {u: i + 1 for i, u in enumerate(order)}; n = len(order)
    a = [[0, 0, 0] for _ in range(n + 1)]
    for u in succ:
        vs = sorted((lab[v] for v in succ[u]), reverse=True)
        a[lab[u]] = [0] + vs + [0] * (2 - len(vs))
    return a

def is_sp(a):
    """two-terminal series-parallel test by series/parallel reductions"""
    n = len(a) - 1
    E = {}
    for i in range(1, n + 1):
        for j in (1, 2):
            v = a[i][j]
            if v: E[(i, v)] = E.get((i, v), 0) + 1
    changed = True
    while changed:
        changed = False
        for k in list(E):
            if E[k] > 1: E[k] = 1; changed = True
        ins = {}; outs = {}
        for (u, v) in E:
            outs.setdefault(u, []).append(v); ins.setdefault(v, []).append(u)
        for x in range(2, n):
            if len(ins.get(x, [])) == 1 and len(outs.get(x, [])) == 1:
                u = ins[x][0]; v = outs[x][0]
                del E[(u, x)]; del E[(x, v)]
                E[(u, v)] = E.get((u, v), 0) + 1; changed = True; break
    return list(E) == [(1, n)]

def functions(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node
