// Sequence diagram: the drawing (props.drawing, shapes from the server) and every step as text.
// Props: title, name, desc, counts, drawing ({width, height, shapes}), steps (texts), copy.
// static/sequence.js links each step item to the drawing's row through `data-step`.
export function view(m, props, c) {
  const d = props.drawing;
  const svg = c.shared.svgRoot(m, props.name, props.desc, `0 0 ${d.width} ${d.height}`, 'vd-sequence-svg', c.shared.scene(m, d.shapes), {
    width: String(d.width),
    height: String(d.height),
    focusable: 'false'
  });
  const region = m('div.vd-sequence-view', { role: 'region', tabindex: '0', 'aria-label': `${props.name} (scrollable)` }, svg);
  return m('div.vb.sequence.vd-sequence', { 'data-copy': props.copy }, [
    props.title ? m('h4.vb-title.vd-sequence-title', props.title) : null,
    m('p.vb-alt.vd-sequence-summary', `${props.desc} (${props.counts})`),
    region,
    m('ol.vd-sequence-steps', { 'aria-label': 'Steps' }, props.steps.map((text, n) => m('li.vd-sequence-step', { 'data-step': String(n) }, text)))
  ]);
}
