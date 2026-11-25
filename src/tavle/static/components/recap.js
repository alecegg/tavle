// Recap block as a component: a docs recap (changes and drift) given as block data.
// static/recap.js wires the judgment buttons by class and `data-item`.
const VERDICTS = { accepted: 'Accept', rejected: 'Reject', open: 'Open' };
const RANGES = [['+', 'added'], ['-', 'removed']];

const list = (value) => (Array.isArray(value) ? value : []);
const dict = (value) => (value !== null && typeof value === 'object' && !Array.isArray(value) ? value : {});
const rowsOf = (props) => list(props.rows).map(dict);
const anchor = (prefix, index) => `${prefix}-f${index}`;

// [item key, label] for each drift flag, in a stable order.
function driftItems(props) {
  const items = rowsOf(props)
    .filter((row) => list(row.drift).includes('unplanned'))
    .map((row) => [`unplanned:${row.file}`, `unplanned change: ${row.file}`]);
  for (const raw of list(props.untouched)) {
    const { task = '', owns = '' } = dict(raw);
    items.push([`untouched:${task}:${owns}`, `untouched: ${task} owns ${owns}`]);
  }
  for (const block of list(props.unverified)) items.push([`unverified:${block}`, `unverified block: ${block}`]);
  return items;
}

function mapping(m, props, prefix) {
  const byBlock = new Map();
  rowsOf(props).forEach((row, index) => {
    for (const block of list(row.blocks)) {
      const links = byBlock.get(String(block)) || [];
      links.push(m('a', { href: `#${anchor(prefix, index)}` }, row.file));
      byBlock.set(String(block), links);
    }
  });
  const rows = [...byBlock].sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)).map(([block, links]) => [block, links.flatMap((link, i) => (i ? [', ', link] : [link]))]);
  for (const block of list(props.unverified)) {
    if (!byBlock.has(String(block))) rows.push([String(block), 'no changed file']);
  }
  if (!rows.length) return m('p', 'No plan block is linked to a change.');
  return m('table.vb-table', [
    m('thead', m('tr', [m('th', 'Plan block'), m('th', 'Changed files')])),
    m('tbody', rows.map(([block, cell]) => m('tr', [m('td', block), m('td', cell)])))
  ]);
}

function drift(m, props) {
  const items = driftItems(props);
  if (!items.length) return m('p', 'No drift flagged.');
  const buttons = Object.entries(VERDICTS).map(([verdict, label]) => m('button.recap-verdict', { type: 'button', 'data-verdict': verdict }, label));
  return [
    m('ul.recap-drift', items.map(([key, label]) => m('li.recap-item', { 'data-item': key }, [`${label} `, m('span.recap-buttons', buttons), m('span.recap-state', { 'aria-live': 'polite' })]))),
    m('p.recap-error', { role: 'alert' })
  ];
}

function ranges(m, c, prefix, index, row) {
  const links = [];
  for (const [sign, key] of RANGES) {
    for (const pair of list(row[key])) {
      if (!(Array.isArray(pair) && pair.length === 2)) continue;
      const name = `${anchor(prefix, index)}-${key[0]}${pair[0]}-${pair[1]}`;
      links.push(m('a.recap-range', { id: name, href: `#${name}` }, `${sign}${pair[0]}-${pair[1]}`));
    }
  }
  return links.flatMap((link, i) => (i ? [' ', link] : [link]));
}

function file(m, c, prefix, index, row) {
  const tasks = list(row.tasks).map(String).join(', ') || (row.shared ? 'shared' : 'unplanned');
  const flags = list(row.drift).map(String).join(' ');
  const head = `${row.file} (${row.status}; ${tasks}${flags ? `; ${flags}` : ''})`;
  return m('details.recap-file', { id: anchor(prefix, index) }, [
    m('summary', head + (row.truncated ? ' (truncated)' : '')),
    m('p.recap-ranges', ranges(m, c, prefix, index, row)),
    m('pre', m('code', row.binary ? 'binary file' : String(row.hunk)))
  ]);
}

export function view(m, props, c, blockId) {
  const prefix = blockId ? `recap-${blockId}` : 'recap';
  const counts = Object.entries(dict(props.summary)).map(([key, value]) => `${key} ${c.shared.pyStr(value)}`).join(', ');
  const heading = `${props.plan ?? ''} ${props.base ?? ''}..${props.head ?? ''}`;
  return m('div.vb.recap', [
    m('section.vb-card', [
      m('h4.vb-title', heading),
      m('p', counts),
      m('h5', 'Plan blocks to changes'),
      mapping(m, props, prefix),
      m('h5', 'Drift'),
      drift(m, props),
      m('h5', 'Files'),
      rowsOf(props).map((row, index) => file(m, c, prefix, index, row))
    ])
  ]);
}
