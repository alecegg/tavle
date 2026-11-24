// Decision block as a component: a question, its evidence and verdict buttons.
// app.js and recap.js wire the buttons by `.decision-*` class and `data-item`.
const OPTIONS = ['approve', 'deny', 'comment'];
const VERDICT_OF = { approve: 'approved', deny: 'denied', comment: 'commented' };
const LABELS = { approve: 'Approve', deny: 'Deny', comment: 'Comment' };
// A glyph beside each label, so approve and deny differ without colour.
const ICONS = { approve: 'check', deny: 'cross', comment: 'pencil' };

function evidence(m, props) {
  const rows = Array.isArray(props.evidence) ? props.evidence : [];
  if (!rows.length) return null;
  return m('ul.decision-evidence', rows.map((row) => m('li', [m('strong.decision-label', row.label), ' ', m('span.decision-text-line', row.text)])));
}

// `decision-comment` names the comment field; the comment button must not share it.
function button(m, c, option) {
  const tone = option === 'comment' ? '' : `.decision-${option}`;
  return m(`button.decision-verdict${tone}`, { type: 'button', 'data-verdict': VERDICT_OF[option] }, [
    c.icons.icon(m, ICONS[option], 'decision-glyph'),
    m('span', LABELS[option])
  ]);
}

function commentField(m, options, id) {
  if (!options.includes('comment')) return null;
  return m('div.decision-comment', { hidden: true }, [
    m('label.decision-note', { for: `decision-text-${id}` }, 'Comment'),
    m('textarea.decision-text', { id: `decision-text-${id}`, rows: '3' }),
    m('button.decision-send.primary', { type: 'button' }, 'Send')
  ]);
}

export function view(m, props, c, blockId) {
  const options = Array.isArray(props.options) ? props.options.map(String) : OPTIONS;
  const id = c.shared.pyStr(blockId);
  return m('div.vb.decision', [
    m('section.vb-card', [
      m('h4.vb-title', 'Decision'),
      m('p.decision-question', props.question),
      evidence(m, props),
      props.diff ? m('pre.decision-diff', { tabindex: '0' }, m('code', props.diff)) : null,
      m('div.decision-item', { 'data-item': id }, [
        m('div.decision-buttons', { role: 'group', 'aria-label': 'Verdict' }, options.map((option) => button(m, c, option))),
        commentField(m, options, id),
        m('p.decision-status', ['Status: ', m('span.decision-state', { 'aria-live': 'polite' }, 'Undecided')])
      ]),
      m('p.decision-error', { role: 'alert' })
    ])
  ]);
}
