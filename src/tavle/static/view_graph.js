// Adjacency of a rendered graph: the ids each edge leaves (`out`) and enters (`into`), read from `.vd-edge` data.
export function readAdjacency(view) {
  const out = new Map();
  const into = new Map();
  for (const edge of view.querySelectorAll('.vd-edge')) {
    const { from, to } = edge.dataset;
    if (!out.has(from)) out.set(from, []);
    if (!into.has(to)) into.set(to, []);
    out.get(from).push(to);
    into.get(to).push(from);
  }
  return { out, into };
}
