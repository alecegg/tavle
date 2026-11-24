// Timeline block as a component: an ordered list with a rail and one node per item.
const ICONS = { done: 'check', active: 'dot', planned: 'ring', blocked: 'cross' };
const WORDS = { done: 'Done', active: 'Active', planned: 'Planned', blocked: 'Blocked' };

// `4 milestones: 2 done, 1 active, 1 planned`; counts of zero are left out.
function summaryText(c, items) {
  const parts = Object.keys(ICONS)
    .map((status) => [items.filter((item) => item.status === status).length, status])
    .filter(([n]) => n)
    .map(([n, status]) => `${n} ${status}`);
  return `${c.shared.countNoun(items.length, 'milestone', 'milestones')}: ${parts.join(', ')}`;
}

function item(m, c, entry, current) {
  return m(`li.vd-timeline-item.vd-timeline-${entry.status}`, { 'aria-current': current ? 'step' : null }, [
    m('span.vd-timeline-node', { 'aria-hidden': 'true' }, c.icons.icon(m, ICONS[entry.status], 'vd-timeline-glyph')),
    m('div.vd-timeline-body', [
      m('p.vd-timeline-when', entry.when),
      m('p.vd-timeline-label', entry.label),
      m('p.vd-timeline-status', WORDS[entry.status]),
      'note' in entry ? m('p.vd-timeline-note', c.shared.inline(m, String(entry.note))) : null,
      'owner' in entry ? m('p.vd-timeline-owner', `Owner: ${entry.owner}`) : null
    ])
  ]);
}

export function view(m, props, c) {
  const items = c.shared.objects(props.item);
  const horizontal = props.orientation === 'horizontal';
  const title = props.title || 'Timeline';
  const current = items.findIndex((entry) => entry.status === 'active');
  const list = m('ol.vd-timeline-list', { role: 'list', 'aria-label': title }, items.map((entry, n) => item(m, c, entry, n === current)));
  const copy = items.map((entry) => `${entry.when}: ${entry.label} (${entry.status})`).join('\n');
  return m(`section.vb.timeline.vd-timeline.vd-timeline-${horizontal ? 'horizontal' : 'vertical'}`, { 'aria-label': title, 'data-copy': copy }, [
    props.title ? m('p.vd-timeline-title', props.title) : null,
    m('p.vb-alt.vd-timeline-summary', summaryText(c, items)),
    horizontal ? m('div.vd-timeline-scroll', { role: 'region', 'aria-label': `${title}, scrollable`, tabindex: '0' }, list) : list
  ]);
}
