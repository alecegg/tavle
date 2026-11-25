"""Cycle and layer order of a directed edge list over named nodes. Pure functions."""

from __future__ import annotations


def _dfs_from(
    root: str,
    out: dict[str, list[tuple[str, int]]],
    state: dict[str, int],
    found: set[int],
) -> None:
    """Depth-first walk from `root`, adding each edge that returns to the stack."""
    state[root] = 1
    stack = [(root, iter(out[root]))]
    while stack:
        here, pending = stack[-1]
        step = next(pending, None)
        if step is None:
            state[here] = 2
            stack.pop()
            continue
        target, index = step
        if state.get(target) == 1:
            found.add(index)
        elif target not in state:
            state[target] = 1
            stack.append((target, iter(out[target])))


def back_edges(ids: list[str], pairs: list[tuple[str, str]]) -> set[int]:
    """Indexes of edges that close a cycle in a DFS over `ids` in order."""
    out: dict[str, list[tuple[str, int]]] = {i: [] for i in ids}
    for index, (source, target) in enumerate(pairs):
        out[source].append((target, index))
    state: dict[str, int] = {}  # 1 on the stack, 2 finished
    found: set[int] = set()
    for root in ids:
        if root not in state:
            _dfs_from(root, out, state, found)
    return found


def assign_layers(ids: list[str], dag: list[tuple[str, str]]) -> dict[str, int]:
    """Longest-path layers of an acyclic edge list; the order of `ids` breaks ties."""
    incoming = dict.fromkeys(ids, 0)
    out: dict[str, list[str]] = {i: [] for i in ids}
    for source, target in dag:
        out[source].append(target)
        incoming[target] += 1
    layer = dict.fromkeys(ids, 0)
    ready = [i for i in ids if incoming[i] == 0]
    while ready:
        here = ready.pop(0)
        for target in out[here]:
            layer[target] = max(layer[target], layer[here] + 1)
            incoming[target] -= 1
            if incoming[target] == 0:
                ready.append(target)
    return layer
