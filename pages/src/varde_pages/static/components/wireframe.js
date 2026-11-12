// Wireframe: each frame is an SVG the server drew (frame.svg), a notes list and a region table.
// Props: heading, compare, unit, frames ({caption, title, svg, notes, summary, alt, rows}), copy.
// static/wireframe.js adds pan, zoom and region selection on the mounted DOM.
const HEAD = ['Region', 'Kind', 'Position', 'Notes'];

function notesList(m, notes) {
  if (!notes.length) return null;
  return m('ol.vw-notes', { 'aria-label': 'Notes' }, notes.map((n) => m('li.vw-note', { value: String(n.n), 'data-region': n.region }, [
    m('strong', n.name),
    `: ${n.text}`
  ])));
}

function regionTable(m, c, frame) {
  const grid = m('table.vb-data-grid', [
    m('thead', m('tr', HEAD.map((h) => m('th', h)))),
    m('tbody', frame.rows.map((row) => m('tr', row.map((cell) => m('td', c.shared.pyStr(cell))))))
  ]);
  return m('details.vb-data', [
    m('summary', frame.summary),
    m('p.vb-alt', frame.alt),
    c.shared.dataScroll(m, grid, frame.summary)
  ]);
}

function figure(m, c, frame) {
  const view = m('div.vw-view', { role: 'region', tabindex: '0', 'aria-label': `${frame.title} (scrollable)` }, c.shared.scene(m, [frame.svg]));
  return m('figure.vw-fig', [
    frame.caption ? m('figcaption', frame.caption) : null,
    view,
    notesList(m, frame.notes),
    regionTable(m, c, frame)
  ]);
}

export function view(m, props, c) {
  const frames = m(`div.vw-frames${props.compare ? '.vw-compare' : ''}`, { 'data-min-unit': props.unit }, props.frames.map((f) => figure(m, c, f)));
  return m('div.vb.wireframe', { 'data-copy': props.copy }, c.shared.card(m, props.heading, frames));
}
