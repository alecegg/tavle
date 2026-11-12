// UI states: one tile per named state of a screen, each showing something or marked n/a.
// Props: heading, layout (or null), tiles ({name, na (or null), shows}), copy.
function tile(m, t) {
  const body = t.na === null
    ? m('p', t.shows)
    : [m('span.vb-badge.vb-na', 'n/a'), ' ', m('span', t.na)];
  return m(`div.vb-state.vb-state-${t.name}`, [m('h5', t.name), body]);
}

export function view(m, props, c) {
  const alt = m('p.vb-alt', `${props.tiles.length} states of the screen`);
  const attrs = props.layout === null ? {} : { 'data-layout': props.layout };
  const grid = m('div.vb-grid', attrs, props.tiles.map((t) => tile(m, t)));
  return m('div.vb.ui-states', { 'data-copy': props.copy }, c.shared.card(m, props.heading, [alt, grid]));
}
