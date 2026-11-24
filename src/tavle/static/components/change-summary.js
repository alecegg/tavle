// Change summary: an info-toned panel holding one sentence (`text`, filled by the page).
export function view(m, props) {
  const title = props.title || '';
  const copy = [title, props.text].filter((part) => part).join('\n');
  return m('aside.vb.change-summary.vd-change-summary', { 'aria-label': 'Change summary', 'data-copy': copy }, [
    m('p.vd-change-summary-label', [m('span.vd-change-summary-glyph', { 'aria-hidden': 'true' }, '~'), ' Changes']),
    title ? m('p.vd-change-summary-title', title) : null,
    m('p.vb-alt.vd-change-summary-text', props.text)
  ]);
}
