// Ranking block as a component: a list the reader reorders with buttons or by dragging.
// inputs_ordered.js moves the `li` rows in place and reads `data-id` in order.
function move(m, direction, name) {
  const [word, arrow] = direction < 0 ? ['up', '↑'] : ['down', '↓'];
  return m('button.ranking-move', { type: 'button', 'data-dir': String(direction), 'aria-label': `Move ${name} ${word}` }, arrow);
}

function row(m, item) {
  const text = [m('span.choice-label', item.label), item.detail ? m('span.choice-detail', item.detail) : null];
  return m('li.ranking-row', { 'data-id': item.value, 'data-label': item.label }, m('div.ranking-line', [
    m('span.ranking-grip', { 'aria-hidden': 'true' }),
    m('span.ranking-text', text),
    m('span.ranking-buttons', [move(m, -1, item.name), move(m, 1, item.name)])
  ]));
}

export function view(m, props, c, blockId) {
  const id = c.shared.pyStr(blockId);
  const hintId = `ranking-hint-${id}`;
  const form = m('form.ranking-item', { 'data-item': id, novalidate: true }, [
    m('fieldset.ranking-group', [
      m('legend.ranking-question', props.question),
      m('p.ranking-hint', { id: hintId }, "The list starts in the order given. Use an item's up and down buttons, or drag it with a mouse."),
      m('ol.ranking-list', { role: 'list', 'aria-describedby': hintId }, props.items.map((item) => row(m, item)))
    ]),
    m('span.ranking-live', { role: 'status', 'aria-live': 'polite' }),
    c.shared.inputFooter(m, 'ranking', 'Send', id)
  ]);
  return c.shared.inputRoot(m, 'ranking', {}, 'Ranking', form);
}
