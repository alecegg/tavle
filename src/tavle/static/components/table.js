// Table block as a component: a scroll region around a typed, groupable table.
// `tableView` also draws the matrix block, which passes `extras`.
const GOOD = ['ok', 'pass', 'passed', 'done', 'success', 'healthy', 'yes', 'complete'];
const WARN = ['warn', 'warning', 'partial', 'pending', 'in progress', 'slow', 'degraded', 'at risk'];
const BAD = ['fail', 'failed', 'error', 'blocked', 'no', 'down', 'broken'];
const STATUS_HEADERS = ['status', 'state', 'health', 'result'];
const BAR_WIDTH = 100;
const BAR_HEIGHT = 8;
const SAFE_URL = /^(https?:\/\/[A-Za-z0-9\-._~:/?#[\]@!$&()*+,;=%]+|#[A-Za-z0-9\-._~:/?#%]*)$/;
const DATE = /(?<![\p{L}\p{N}_])(\p{Nd}{4}-\p{Nd}{2}-\p{Nd}{2})(?!\p{Nd})/gu;

function unescapeHtml(text) {
  const holder = document.createElement('textarea');
  holder.innerHTML = text;
  return holder.value;
}

// 'link' (http, https, #), 'relative', or 'text' (any other scheme).
export function classifyUrl(url) {
  const stripped = unescapeHtml(url).replace(/[\s\x00-\x1f\x7f]/g, '');
  if (SAFE_URL.test(url) && stripped === url) return 'link';
  if (!stripped || stripped.startsWith('//') || stripped.startsWith('\\') || stripped.includes('\\')) return 'text';
  const head = stripped.split(/[/?#]/)[0];
  return head.includes(':') || !/^[\x00-\x7f]*$/.test(stripped) ? 'text' : 'relative';
}

// The css modifier of a status word; the word itself always shows and the icon (see icons.js) is STATUS_ICONS[modifier].
export function statusKind(text) {
  const word = text.trim().toLowerCase();
  if (GOOD.includes(word)) return 'ok';
  if (WARN.includes(word)) return 'warn';
  if (BAD.includes(word)) return 'bad';
  return 'neutral';
}

const STATUS_ICONS = { ok: 'check', warn: 'triangle', bad: 'cross', neutral: 'dot' };

function linkParts(c, cell) {
  if (Array.isArray(cell) && cell.length === 2) return [c.shared.pyStr(cell[0]), c.shared.pyStr(cell[1])];
  return [c.shared.pyStr(cell), c.shared.pyStr(cell)];
}

function barPercent(value, top) {
  return top <= 0 ? 0 : Math.max(0, Math.min(100, (value / top) * 100));
}

function plainText(c, cell) {
  const [label, url] = Array.isArray(cell) ? linkParts(c, cell) : [c.shared.pyStr(cell), ''];
  return c.shared.words(url && url !== label ? `${label} (${url})` : label);
}

function copyText(c, columns, rows, groups) {
  const lines = [[...(groups.length ? ['group'] : []), ...columns.map((col) => plainText(c, col))]];
  rows.forEach((row, n) => lines.push([...(groups.length ? [plainText(c, groups[n])] : []), ...row.map((cell) => plainText(c, cell))]));
  return lines.map((line) => line.join('\t')).join('\n');
}

// One group label per row, empty when the table has no groups.
function groupLabels(props, rowCount) {
  const labels = [];
  for (const group of asList(props.groups)) {
    const label = String((group && group.label) ?? '');
    for (let n = 0; n < Number((group && group.rows) || 0); n += 1) labels.push(label);
  }
  return labels.length === rowCount ? labels : [];
}

function asList(value) {
  return Array.isArray(value) ? value : [];
}

function dated(m, c, cell) {
  return c.shared.pyStr(cell).split(DATE).map((part, i) => (i % 2 ? m('span.vd-date', part) : part));
}

function link(m, c, cell) {
  const [label, url] = linkParts(c, cell);
  const kind = classifyUrl(url);
  if (kind === 'link') return m('a', { href: url, rel: 'noopener noreferrer' }, label);
  if (kind === 'relative') return m('span.relative-link', { title: url }, label);
  return label;
}

function barGraphic(m, c, value, top) {
  const width = c.shared.fixed((barPercent(value, top) * BAR_WIDTH) / 100, 1);
  return m('svg.vb-bar-svg', { viewBox: `0 0 ${BAR_WIDTH} ${BAR_HEIGHT}`, 'aria-hidden': 'true', focusable: 'false' }, [
      m('rect.vb-bar-track', { width: String(BAR_WIDTH), height: String(BAR_HEIGHT) }),
      m('rect.vb-bar-fill', { width, height: String(BAR_HEIGHT) })
    ]);
}

function bar(m, c, cell, top) {
  return [barGraphic(m, c, Number(c.shared.pyStr(cell)), top), m('span.vb-bar-num', c.shared.pyStr(cell))];
}

function progress(m, c, cell) {
  const [done, total] = cell;
  return [barGraphic(m, c, done, total), m('span.vb-bar-num', `${done} of ${total}`)];
}

function status(m, c, cell, extras) {
  const text = c.shared.pyStr(cell);
  const kind = (extras.statusKind && extras.statusKind(text)) || statusKind(text);
  return m(`span.vb-status.vb-status-${kind}`, [c.icons.icon(m, STATUS_ICONS[kind] || STATUS_ICONS.neutral, 'vb-status-glyph'), text]);
}

function cellView(m, c, cell, kind, top, extras) {
  if (kind === 'link') return link(m, c, cell);
  if (kind === 'bar') return bar(m, c, cell, top);
  if (kind === 'progress') return progress(m, c, cell);
  if (kind === 'status') return status(m, c, cell, extras);
  return dated(m, c, cell);
}

const numeric = (kind) => kind === 'number' || kind === 'bar';

function cellLabel(c, index, spec, rec) {
  if (rec) return `${spec.extras.recommended.label} (recommended)`;
  return c.shared.pyStr(spec.columns[index]);
}

function cellAttrs(c, cell, index, spec, tag, rec) {
  const attrs = { 'data-label': cellLabel(c, index, spec, rec) };
  if (tag === 'th') attrs.scope = 'row';
  if (spec.kinds[index] === 'progress') attrs['data-sort'] = cell[1] ? cell[0] / cell[1] : 0;
  return attrs;
}

function rowCell(m, c, cell, index, spec) {
  const tag = spec.rowHeader && index === 0 ? 'th' : 'td';
  const rec = spec.extras.recommended && spec.extras.recommended.index === index;
  const attrs = cellAttrs(c, cell, index, spec, tag, rec);
  const cls = rec ? '.vd-matrix-rec' : numeric(spec.kinds[index]) ? '.vb-num' : '';
  return m(tag + cls, attrs, cellView(m, c, cell, spec.kinds[index], spec.tops[index], spec.extras));
}

function row(m, c, cells, spec) {
  return m('tr', cells.map((cell, index) => rowCell(m, c, cell, index, spec)));
}

function head(m, c, spec) {
  const rec = spec.extras.recommended;
  return m(
    'thead',
    m(
      'tr',
      spec.columns.map((col, index) => {
        if (rec && rec.index === index) {
          return m('th.vd-matrix-rec', { scope: 'col', 'aria-label': `${rec.label}, Recommended` }, c.shared.pyStr(col));
        }
        return m(`th${numeric(spec.kinds[index]) ? '.vb-num' : ''}`, { scope: 'col' }, c.shared.pyStr(col));
      })
    )
  );
}

function bodies(m, c, rows, labels, spec) {
  const out = [];
  let previous = null;
  rows.forEach((cells, n) => {
    const label = labels.length ? labels[n] : '';
    if (label !== previous || !out.length) {
      out.push({ head: labels.length ? label : null, rows: [] });
      previous = label;
    }
    out[out.length - 1].rows.push(row(m, c, cells, spec));
  });
  return out.map((body) =>
    m('tbody', [
      body.head === null ? null : m('tr.vb-group-head', m('th', { scope: 'colgroup', colspan: String(spec.columns.length) }, body.head)),
      body.rows
    ])
  );
}

// Largest value of each bar column (0 for other columns): the bar scale.
function columnTops(rows, kinds) {
  return kinds.map((kind, i) => (kind === 'bar' ? Math.max(0, ...rows.map((r) => Number(String(r[i])))) : 0));
}

// An untyped column is a status column when its header names a status or every value is a status word.
function inferredKind(col, values) {
  const namedStatus = STATUS_HEADERS.includes(String(col).trim().toLowerCase());
  const allStatusWords = values.length > 0 && values.every((value) => statusKind(value) !== 'neutral');
  return namedStatus || allStatusWords ? 'status' : 'text';
}

export function tableView(m, props, c, extras) {
  const columns = asList(props.columns);
  const rows = asList(props.rows).map(asList);
  const types = props.types || {};
  const kinds = columns.map((col, index) => {
    if (Object.hasOwn(types, String(col))) return String(types[String(col)]);
    const values = rows.map((row) => c.shared.pyStr(row[index] ?? '').trim()).filter(Boolean);
    return inferredKind(col, values);
  });
  const labels = groupLabels(props, rows.length);
  const sticky = props.sticky_column === true;
  const name = String(props.caption ?? 'Table');
  const size = `${rows.length} rows, ${columns.length} columns`;
  const spec = { columns, kinds, tops: columnTops(rows, kinds), rowHeader: sticky, extras };
  const grid = m(`table.vb-table${props.stack !== false ? '.vb-table-stack' : ''}${sticky ? '.vb-table-sticky' : ''}`, { 'aria-label': `${name} (${size})` }, [
    head(m, c, spec),
    bodies(m, c, rows, labels, spec)
  ]);
  const body = [
    m('div.vb-scroll', { role: 'region', tabindex: '0', 'aria-label': name }, grid),
    // The size count is for screen readers unless a filter is shown (40-table.css).
    'footnote' in props ? m('p.vb-alt.vb-foot', String(props.footnote)) : m('p.vb-alt.vb-foot.vb-sr', size)
  ];
  return m(extras.root || 'div.vb.table', { 'data-copy': extras.copy ?? copyText(c, columns, rows, labels) }, [
    m('section.vb-card', ['caption' in props ? m('h4.vb-title', String(props.caption)) : null, body]),
    extras.after || null
  ]);
}

export function view(m, props, c) {
  return tableView(m, props, c, {});
}
