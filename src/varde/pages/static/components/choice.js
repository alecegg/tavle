// Choice block as a component: a question, its options, an optional note and a send row.
// recap.js hydrates the `data-component` root and reads `input` values by name.
function option(m, o, type, group, index) {
  const recId = `${group}-rec-${index}`;
  // Mithril skips a `value` equal to the control's default ("on"); the attribute is the answer, so set it.
  const keepValue = (vnode) => vnode.dom.setAttribute('value', o.value);
  const input = m('input', { type, name: group, oncreate: keepValue, 'aria-required': 'true', 'aria-describedby': o.recommended ? recId : undefined });
  const body = m('span.choice-body', [
    m('span.choice-label', o.label),
    o.recommended ? m('span.choice-rec', { id: recId }, 'Recommended') : null,
    o.detail ? m('span.choice-detail', o.detail) : null
  ]);
  return m('label.choice-option', [input, body]);
}

function note(m, maxNote) {
  return m('label.choice-note', [m('span', 'Comment'), m('textarea.choice-text', { rows: '3', maxlength: maxNote })]);
}

export function view(m, props, c, blockId) {
  const id = c.shared.pyStr(blockId);
  const group = `choice-${blockId ?? ''}`;
  const type = props.multiple ? 'checkbox' : 'radio';
  const options = props.options.map((o, i) => option(m, o, type, group, i + 1));
  const form = m('form.choice-item', { 'data-item': id, novalidate: true }, [
    m('fieldset.choice-group', { 'aria-describedby': `choice-error-${id}` }, [
      m('legend.choice-question', props.question),
      m('div.choice-options', m('div.choice-grid', options))
    ]),
    props.comment ? note(m, props.maxNote) : null,
    c.shared.inputFooter(m, 'choice', 'Send', id)
  ]);
  return c.shared.inputRoot(m, 'choice', { multiple: props.multiple, comment: props.comment }, '', form);
}
