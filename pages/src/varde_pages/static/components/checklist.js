// Checklist block as a component: state glyph and word per item, progress bar and count.
const STATES = { done: ['✓', 'Done'], open: ['○', 'Open'], blocked: ['✕', 'Blocked'] };

function itemState(item) {
  if (typeof item.status === 'string') return item.status;
  return item.checked === true ? 'done' : 'open';
}

function item(m, c, entry) {
  const state = itemState(entry);
  const [glyph, word] = STATES[state];
  return m(`li.vd-checklist-item.vd-checklist-${state}`, [
    m('span.vd-checklist-state', [m('span.vd-checklist-glyph', { 'aria-hidden': 'true' }, glyph), ` ${word}`]),
    m('span.vd-checklist-text', [
      m('span.vd-checklist-label', c.shared.inline(m, String(entry.label))),
      'note' in entry ? m('span.vd-checklist-note', c.shared.inline(m, String(entry.note))) : null
    ])
  ]);
}

function copyText(props, items) {
  const title = 'title' in props ? String(props.title) : '';
  const lines = items.map((entry) => `- [${itemState(entry) === 'done' ? 'x' : ' '}] ${entry.label}`);
  return [title, ...lines].filter((part) => part).join('\n');
}

export function view(m, props, c) {
  const items = c.shared.objects(props.items);
  const done = items.filter((entry) => itemState(entry) === 'done').length;
  const count = `${done} of ${items.length} done`;
  return m('section.vb.checklist.vd-checklist', { 'aria-label': 'Checklist', 'data-copy': copyText(props, items) }, [
    'title' in props ? m('p.vd-checklist-title', props.title) : null,
    m('div.vd-checklist-progress', [
      m('progress.vd-checklist-bar', { value: String(done), max: String(Math.max(items.length, 1)), 'aria-label': 'Progress' }, count),
      m('p.vb-alt.vd-checklist-count', count)
    ]),
    items.length
      ? m('ul.vd-checklist-list', { 'aria-label': `Checklist, ${count}` }, items.map((entry) => item(m, c, entry)))
      : m('p.vd-checklist-empty', 'No items.')
  ]);
}
