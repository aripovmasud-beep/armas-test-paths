"""Graph generators of Section 7.1 (all use an explicit ``random.Random`` for seeds)."""
import random

from .graph import is_valid_program_dag

# Table 10: (p_if_else, p_if, max_depth)
STRUCTURED_CONFIGS = {
    "baseline": (0.35, 0.25, 6),
    "if-else only": (0.60, 0.0, 6),
    "if-then only": (0.0, 0.60, 6),
    "deep nesting": (0.35, 0.25, 12),
    "shallow sequences": (0.35, 0.25, 2),
    "dense branching": (0.50, 0.40, 8),
}


def _to_pam(successors):
    n = len(successors)
    a = [[0, 0, 0] for _ in range(n + 1)]
    for i, succ in enumerate(successors, 1):
        s = sorted(set(succ), reverse=True)
        a[i] = [0] + s + [0] * (2 - len(s))
    return a


def structured(n_target, rng, p_ifelse=0.35, p_if=0.25, max_depth=6):
    """Structured DAG: recursive sequence of statements, if and if-else blocks."""
    nodes = []

    def new():
        nodes.append([])
        return len(nodes)

    def block(budget, depth):
        first = cur = new()
        budget -= 1
        while budget > 0:
            r = rng.random()
            if depth < max_depth and budget > 4 and r < p_ifelse:       # if-else
                b1 = rng.randint(1, max(1, budget // 3))
                b2 = rng.randint(1, max(1, budget // 3))
                cond = cur
                e1, x1 = block(b1, depth + 1)
                e2, x2 = block(b2, depth + 1)
                join = new()
                nodes[cond - 1] += [e1, e2]
                nodes[x1 - 1].append(join)
                nodes[x2 - 1].append(join)
                cur = join
                budget -= b1 + b2 + 1
            elif depth < max_depth and budget > 2 and r < p_ifelse + p_if:    # if
                b1 = rng.randint(1, max(1, budget // 3))
                cond = cur
                e1, x1 = block(b1, depth + 1)
                join = new()
                nodes[cond - 1] += [e1, join]
                nodes[x1 - 1].append(join)
                cur = join
                budget -= b1 + 1
            else:                                                       # statement
                nxt = new()
                nodes[cur - 1].append(nxt)
                cur = nxt
                budget -= 1
        return first, cur

    block(n_target, 0)
    return _to_pam(nodes)


def random_dag(n, rng, p_jump=0.35):
    """Chain 1 -> 2 -> ... -> n plus, with probability p_jump per node, a forward jump of
    length 2 + floor(Exp(mean 6))."""
    a = [[0, 0, 0] for _ in range(n + 1)]
    for i in range(1, n):
        succ = {i + 1}
        if i + 2 <= n and rng.random() < p_jump:
            span = max(2, int(rng.expovariate(1 / 6)) + 2)
            succ.add(min(n, i + span))
        s = sorted(succ, reverse=True)
        a[i] = [0] + s + [0] * (2 - len(s))
    return a


def mixed(n_target, rng, p_jump=0.08):
    """Baseline structured graph; each single-successor node gets a forward jump of
    length 2-12 with probability p_jump (like break or an early return)."""
    a = structured(n_target, rng)
    n = len(a) - 1
    for i in range(1, n - 1):
        succ = [x for x in a[i][1:] if x > 0]
        if len(succ) == 1 and rng.random() < p_jump:
            t = min(n, i + rng.randint(2, 12))
            if t not in succ:
                a[i] = [0] + sorted(succ + [t], reverse=True)
    return a


def small_arbitrary(rng):
    """Small arbitrary DAG: n in 6..14, 1 or 2 random later successors (1 with
    probability 2/3); kept only if every node lies on an s-t path."""
    while True:
        n = rng.randint(6, 14)
        rows = [[0, 0, 0] for _ in range(n + 1)]
        for i in range(1, n):
            k = rng.choice([1, 1, 2])
            succ = set(rng.sample(range(i + 1, n + 1), min(k, n - i)))
            sl = sorted(succ, reverse=True)
            rows[i] = [0] + sl + [0] * (2 - len(sl))
        if is_valid_program_dag(rows):
            return rows


def renumber(a, rng):
    """Random topological renumbering (s stays 1, t stays n) and random column order."""
    n = len(a) - 1
    succ = {i: [x for x in a[i][1:] if x > 0] for i in range(1, n + 1)}
    indeg = {i: 0 for i in succ}
    for i in succ:
        for v in succ[i]:
            indeg[v] += 1
    ready = [1]
    order = []
    while ready:
        u = ready.pop(rng.randrange(len(ready)))
        order.append(u)
        for v in succ[u]:
            indeg[v] -= 1
            if indeg[v] == 0 and v != n:
                ready.append(v)
    order.append(n)
    assert len(order) == n and order[0] == 1 and order[-1] == n
    lab = {u: i + 1 for i, u in enumerate(order)}
    b = [[0, 0, 0] for _ in range(n + 1)]
    for u in succ:
        vs = [lab[v] for v in succ[u]]
        rng.shuffle(vs)
        b[lab[u]] = [0] + vs + [0] * (2 - len(vs))
    return b
