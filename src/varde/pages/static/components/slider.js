// Slider block as a component: a native range input, its end labels and the chosen value.
// inputs_ordered.js reads `data-props` (min, max, step) and writes the value into the output.
function ticks(m, count) {
  if (!count) return null;
  return m('div.slider-ticks', { 'aria-hidden': 'true' }, Array.from({ length: count }, () => m('span')));
}

export function view(m, props, c, blockId) {
  const id = c.shared.pyStr(blockId);
  const field = `slider-input-${id}`;
  // A range clamps its value when its type is set, and Mithril sets `type` before every other
  // attribute; setting it once min, max and step are in makes the unmoved thumb sit mid-scale.
  const setRange = (vnode) => vnode.dom.setAttribute('type', 'range');
  const input = m('input.slider-input', {
    id: field, 'aria-label': props.label, 'aria-valuetext': 'Not chosen yet', min: props.minText, max: props.maxText, step: props.stepText, oncreate: setRange
  });
  const form = m('form.slider-item', { 'data-item': id, novalidate: true }, [
    m('fieldset.slider-group', [
      m('legend.slider-label', props.label),
      m('div.slider-track', [input, ticks(m, props.ticks)]),
      m('div.slider-ends', props.ends.map((end) => m('span.slider-end', end))),
      m('output.slider-value', { for: field }, 'Not chosen yet')
    ]),
    c.shared.inputFooter(m, 'slider', 'Send', id)
  ]);
  return c.shared.inputRoot(m, 'slider', { min: props.min, max: props.max, step: props.step }, '', form);
}
