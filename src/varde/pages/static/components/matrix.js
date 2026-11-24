// Matrix block as a component: a typed table of options by criteria, with the
// recommended column marked, level ratings toned and a weighted total.
const SCALES = {
  verdict: { yes: 2, partial: 1, no: 0 },
  level: { high: 2, medium: 1, low: 0 }
};
const FIRST_COLUMN = 'Criterion';
const TOTAL_LABEL = 'Weighted total';
const NOT_RATED = 'Not rated';
const LEVEL_TONES = { high: 'ok', medium: 'warn', low: 'bad' };

function ratingScale(cell) {
  const word = typeof cell === 'string' ? cell.trim().toLowerCase() : '';
  return Object.keys(SCALES).find((name) => Object.hasOwn(SCALES[name], word)) || null;
}

function scaleOf(cells) {
  return cells.flat().map(ratingScale).find((scale) => scale) || 'verdict';
}

function points(cell, scale) {
  const word = String(cell).trim().toLowerCase();
  return Object.hasOwn(SCALES[scale], word) ? SCALES[scale][word] : 0;
}

// (score, best possible) per option column.
function totals(cells, weights, scale) {
  const best = 2 * weights.reduce((a, b) => a + b, 0);
  const width = cells.length ? cells[0].length : 0;
  return Array.from({ length: width }, (_, i) => [cells.reduce((sum, row, n) => sum + weights[n] * points(row[i], scale), 0), best]);
}

// The text alternative: sizes, the recommendation and the scoring rule.
function alternative(c, props, options, criteria, weighted) {
  const parts = [`${c.shared.countNoun(options.length, 'option', 'options')} compared on ${c.shared.countNoun(criteria.length, 'criterion', 'criteria')}.`];
  const chosen = options.find((o) => o.id === props.recommended);
  if (chosen) parts.push(`Recommended: ${chosen.label}.`);
  if (weighted) parts.push('Weighted total: yes or high scores 2, partial or medium 1, no or low 0, times the weight.');
  return parts.join(' ');
}

// The table block props the matrix is shown with.
function tableProps(c, props, options, criteria, cells) {
  const weighted = criteria.some((criterion) => 'weight' in criterion);
  const rows = criteria.map((criterion, n) => [
    criterion.label + ('weight' in criterion ? ` (weight ${criterion.weight})` : ''),
    ...cells[n].map((cell) => String(cell).trim() || NOT_RATED)
  ]);
  if (weighted) {
    const weights = criteria.map((criterion) => Number(criterion.weight ?? 1));
    rows.push([TOTAL_LABEL, ...totals(cells, weights, scaleOf(cells)).map(([got, best]) => `${got} of ${best}`)]);
  }
  const labels = options.map((o) => String(o.label));
  return {
    caption: String(props.title ?? 'Options compared'),
    columns: [FIRST_COLUMN, ...labels],
    rows,
    types: Object.fromEntries(labels.map((label) => [label, 'status'])),
    footnote: alternative(c, props, options, criteria, weighted),
    stack: true
  };
}

function copyText(c, table, recommended) {
  const columns = table.columns.map((col) => (col === recommended ? `${col} (recommended)` : col));
  const lines = [columns, columns.map(() => '---'), ...table.rows];
  return lines.map((line) => `| ${line.map((cell) => c.shared.words(String(cell)).replaceAll('|', '\\|')).join(' | ')} |`).join('\n');
}

function notes(m, options) {
  const items = options.filter((o) => 'note' in o);
  if (!items.length) return null;
  return m('div.vd-matrix-notes', { role: 'region', tabindex: '0', 'aria-label': 'Option notes' }, [
    m('ul', items.map((o) => m('li', [m('strong', o.label), `: ${o.note}`])))
  ]);
}

// A plain rating word on the level scale is toned: high good, low bad.
function levelTone(text) {
  const word = text.toLowerCase();
  return Object.hasOwn(LEVEL_TONES, word) ? LEVEL_TONES[word] : null;
}

export function view(m, props, c) {
  const options = c.shared.objects(props.options);
  const criteria = c.shared.objects(props.criteria);
  const cells = (Array.isArray(props.cells) ? props.cells : []).map((row) => (Array.isArray(row) ? row : []));
  const table = tableProps(c, props, options, criteria, cells);
  const chosen = options.find((o) => o.id === props.recommended);
  return c.table.tableView(m, table, c, {
    root: 'div.vb.matrix.vd-matrix',
    copy: copyText(c, table, chosen ? String(chosen.label) : null),
    recommended: chosen ? { index: options.indexOf(chosen) + 1, label: String(chosen.label) } : null,
    statusKind: scaleOf(cells) === 'level' ? levelTone : null,
    after: notes(m, options)
  });
}
