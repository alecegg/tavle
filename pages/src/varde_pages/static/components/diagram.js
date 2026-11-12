// Diagram: one SVG per collapse state (props.views, drawn as shapes by the server), a text
// alternative listing every node and edge. static/diagram.js shows one view and toggles `hidden`.
// Props: heading, title, desc, unit, views ({mask, box, width, height, shapes}),
// alt ({summary, nodes: {id, label, tags, detail}, edges: {from, to, text}}), copy.
// One collapse state: a scrollable region around the svg (the flow block draws one too).
export function stateView(m, c, v, title, desc) {
  const attrs = { 'data-mask': String(v.mask), role: 'region', tabindex: '0', 'aria-label': `${title} (scrollable)` };
  if (v.mask) attrs.hidden = true;
  const svg = c.shared.svgRoot(m, title, desc, v.box, 'vd-svg', c.shared.scene(m, v.shapes), { width: v.width, height: v.height });
  return m('div.vd-view', attrs, svg);
}

function alternative(m, alt) {
  const nodes = alt.nodes.map((n) => m('li', { 'data-node': n.id }, [
    m('strong', n.label),
    ` (${n.tags})`,
    n.detail ? [': ', m('span.vd-detail-text', n.detail)] : null
  ]));
  const edges = alt.edges.map((e) => m('li', { 'data-from': e.from, 'data-to': e.to }, e.text));
  return m('details.vb-data', [
    m('summary', 'Nodes and edges as text'),
    m('p.vb-alt', alt.summary),
    m('h5', 'Nodes'),
    m('ul', nodes),
    edges.length ? [m('h5', 'Edges'), m('ul', edges)] : null
  ]);
}

export function view(m, props, c) {
  const body = [m('div.vd-views', { 'data-min-unit': props.unit }, props.views.map((v) => stateView(m, c, v, props.title, props.desc))), alternative(m, props.alt)];
  return m('div.vb.diagram', { 'data-copy': props.copy }, c.shared.card(m, props.heading, body));
}
