// Stats block as a component: a grid of cards (label, value, optional change).
const ARROWS = { up: '▲', down: '▼', flat: '▬' };
const SIGNS = ['+', '-', '−'];
const GOOD_TONE = { true: 'success', false: 'risk' };

export function deltaDirection(item) {
  if (typeof item.direction === 'string') return item.direction;
  const delta = item.delta;
  if (typeof delta === 'number') return delta === 0 ? 'flat' : delta > 0 ? 'up' : 'down';
  const sign = typeof delta === 'string' ? delta.trim()[0] : undefined;
  if (sign === '+') return 'up';
  return SIGNS.includes(sign) ? 'down' : null;
}

function valueText(c, item) {
  return typeof item.value === 'string' ? item.value : c.shared.formatNumber(item.value, item.decimals);
}

// The delta without its sign: the direction word carries the sign.
function deltaText(c, item) {
  if (typeof item.delta === 'string') return item.delta.trim().replace(/^[+\-−]+/, '').trim();
  return c.shared.formatNumber(Math.abs(item.delta), item.decimals);
}

function itemTone(item, direction) {
  if (typeof item.tone === 'string') return item.tone;
  if (item.good === undefined || item.good === null || !direction || direction === 'flat') return 'neutral';
  return GOOD_TONE[direction === item.good];
}

function spokenDelta(c, item) {
  return `${deltaDirection(item) || 'flat'} ${deltaText(c, item)}`.trim();
}

function cardName(c, item) {
  const delta = 'delta' in item ? `, ${spokenDelta(c, item)}` : '';
  return `${item.label}: ${valueText(c, item)}${delta}`;
}

function copyText(c, items) {
  return items
    .map((item) => `${item.label}: ${valueText(c, item)}${'delta' in item ? ` (${spokenDelta(c, item)})` : ''}`)
    .join('\n');
}

function delta(m, c, item) {
  if (!('delta' in item)) return null;
  const direction = deltaDirection(item) || 'flat';
  return m('dd.vd-stats-delta', [
    m('span.vd-stats-mark', [m('span.vd-stats-glyph', { 'aria-hidden': 'true' }, ARROWS[direction]), ' ', m('span.vd-stats-word', direction)]),
    ' ',
    m('span.vd-stats-number', deltaText(c, item))
  ]);
}

function card(m, c, item) {
  const tone = itemTone(item, deltaDirection(item));
  return m(`div.vd-stats-card.vd-stats-${tone}`, { role: 'group', 'aria-label': cardName(c, item) }, [
    m('dl.vd-stats-body', [
      m('dt.vd-stats-label', item.label),
      m('dd.vd-stats-value', valueText(c, item)),
      delta(m, c, item),
      'note' in item ? m('dd.vd-stats-note', c.shared.inline(m, String(item.note))) : null
    ])
  ]);
}

export function view(m, props, c) {
  const items = c.shared.objects(props.item);
  const count = items.length;
  return m('section.vb.stats.vd-stats', { 'aria-label': 'Stats', 'data-copy': copyText(c, items) }, [
    m('p.vb-alt.vd-stats-summary', `${count} ${count === 1 ? 'stat' : 'stats'}`),
    m(`div.vd-stats-grid.vd-stats-n${count}`, items.map((item) => card(m, c, item)))
  ]);
}
