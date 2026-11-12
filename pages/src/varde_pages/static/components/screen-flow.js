// Screen flow: wireframe screens joined by arrows, drawn by the server as two SVGs (across and down),
// then an ordered list of the screens as the text alternative.
// Props: title, name, summary, views ({way, svg}), items ({id, title, lane, regions, next, notes}), copy.
// static/screen_flow.js adds pan, zoom, selection and the notes panel on the mounted DOM.
function notes(m, list) {
  if (!list.length) return null;
  return m('ol.vd-sf-notes', { 'aria-label': 'Notes' }, list.map((n) => m('li.vd-sf-note', { value: String(n.n) }, [m('strong', n.name), `: ${n.text}`])));
}

function item(m, it) {
  return m('li.vd-sf-item', { 'data-screen': it.id }, [
    m('strong.vd-sf-name', it.title),
    `${it.lane}: `,
    m('span.vd-sf-regions', it.regions),
    '; ',
    m('span.vd-sf-next', it.next),
    notes(m, it.notes)
  ]);
}

function viewOf(m, c, props, v) {
  const attrs = { role: 'region', tabindex: '0', 'aria-label': `${props.name} (scrollable)` };
  return m(`div.vd-sf-view.vd-sf-${v.way}`, attrs, c.shared.scene(m, [v.svg]));
}

export function view(m, props, c) {
  return m('div.vb.screen-flow.vd-sf', { 'data-copy': props.copy }, [
    props.title ? m('h4.vb-title.vd-sf-title', props.title) : null,
    m('p.vb-alt.vd-sf-summary', props.summary),
    m('p.vd-sf-scroll-hint', 'Scroll to explore the flow; screen details follow.'),
    m('div.vd-sf-views', props.views.map((v) => viewOf(m, c, props, v))),
    m('ol.vd-sf-list', { 'aria-label': 'Screens in order' }, props.items.map((it) => item(m, it)))
  ]);
}
