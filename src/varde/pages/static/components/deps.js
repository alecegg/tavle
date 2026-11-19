// Task dependency graph: the server lays the nodes out; this draws them as inline SVG.
// Props: empty, or width, height, truncated, edges ({d, back}) and nodes ({known, title, label, x, y, tx, ty, w, h}).
function node(m, n) {
  return m('g', { class: n.known ? 'node' : 'node missing' }, [
    m('title', n.title),
    m('rect', { x: n.x, y: n.y, width: String(n.w), height: String(n.h), rx: '4' }),
    m('text', { x: n.tx, y: n.ty, 'text-anchor': 'middle' }, n.label)
  ]);
}

export function view(m, props) {
  if (props.empty) return m('p.graph-empty', 'No dependencies listed.');
  const arrow = m('marker', { id: 'dep-arrow', viewBox: '0 0 8 8', refX: '7', refY: '4', markerWidth: '8', markerHeight: '8', orient: 'auto' },
    m('path.arrow', { d: 'M0 0L8 4L0 8z' }));
  const graph = m('svg', {
    class: 'dep-graph',
    viewBox: `0 0 ${props.width} ${props.height}`,
    role: 'img',
    'aria-label': 'Task dependency graph',
    width: String(props.width),
    height: String(props.height),
    preserveAspectRatio: 'xMidYMin meet',
    xmlns: 'http://www.w3.org/2000/svg'
  }, [
    m('defs', arrow),
    props.edges.map((edge) => m('path', { class: edge.back ? 'edge back' : 'edge', d: edge.d, 'marker-end': 'url(#dep-arrow)' })),
    props.nodes.map((n) => node(m, n))
  ]);
  return [
    m('div.scroll', graph),
    props.truncated ? m('p.graph-note', 'Graph truncated: too many tasks or dependencies.') : null
  ];
}
