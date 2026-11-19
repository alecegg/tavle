// State machine: the drawing (props.drawing, shapes from the server), the states and the transitions as text.
// Props: title, name, desc, counts, drawing ({box, width, height, shapes}), states, moves (texts), copy.
export function view(m, props, c) {
  const d = props.drawing;
  const svg = c.shared.svgRoot(m, props.name, props.desc, d.box, 'vd-state-svg', c.shared.scene(m, d.shapes), { width: d.width, height: d.height });
  const region = m('div.vd-state-view', { role: 'region', tabindex: '0', 'aria-label': `${props.name} (scrollable)` }, svg);
  return m('div.vb.state.vd-state', { 'data-copy': props.copy }, [
    props.title ? m('h4.vb-title.vd-state-title', props.title) : null,
    m('p.vb-alt.vd-state-summary', `${props.desc} (${props.counts})`),
    region,
    m('ul.vd-state-states', { 'aria-label': 'States' }, props.states.map((text) => m('li.vd-state-item', text))),
    props.moves.length ? m('ol.vd-state-moves', { 'aria-label': 'Transitions' }, props.moves.map((text) => m('li.vd-state-item', text))) : null
  ]);
}
