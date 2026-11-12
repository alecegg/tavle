// Comment block as a component: a labelled box with a character counter and a send row.
export function view(m, props, c, blockId) {
  const id = c.shared.pyStr(blockId);
  const field = m('div.comment-field', [
    m('label.comment-note', { for: `comment-text-${id}` }, props.label),
    m('textarea.comment-text', { id: `comment-text-${id}`, rows: '4', maxlength: props.maxNote, 'aria-describedby': `comment-count-${id}` }),
    m('span.comment-count', { id: `comment-count-${id}` }, `0 / ${props.maxNote}`),
    m('span.comment-announce', { 'aria-live': 'polite' })
  ]);
  const form = m('form.comment-item', { 'data-item': id, novalidate: true }, [field, c.shared.inputFooter(m, 'comment', props.submit, id)]);
  return c.shared.inputRoot(m, 'comment', {}, 'Comment', form);
}
