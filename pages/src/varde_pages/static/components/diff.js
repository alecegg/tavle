// Diff: header, unified and side-by-side tables, folded runs, numbered notes. Props come from the
// server, which computes the rows (difflib or a patch), the folds and the highlighting: name,
// language, uid, digits, split, change, was, count, copy, blocks (rows with `code` token pairs)
// and notes. A `split` diff holds both tables; the stylesheet shows one by container width.
const MARKS = { add: ['+', 'added'], del: ['-', 'removed'], same: ['', ''] };

function codeNodes(m, c, row) {
  return c.code.tokenNodes(m, row.code);
}

function pins(m, props, side, line) {
  if (line === null || line === undefined) return null;
  const found = props.notes.filter((n) => n.side === side && n.start === line);
  if (!found.length) return null;
  return m('span.vd-diff-pins', found.map((n) =>
    m('a.vd-diff-pin', { href: `#note-${props.uid}-${n.number}`, 'aria-label': `Note ${n.number}, ${n.where}` }, String(n.number))));
}

function mark(m, kind, extra) {
  const klass = `vd-diff-mark${extra}`;
  const [glyph, word] = MARKS[kind];
  if (!glyph) return m('td', { class: klass });
  return m('td', { class: klass }, [m('span', { 'aria-hidden': 'true' }, glyph), m('span.vd-diff-sr', word)]);
}

function unifiedRow(m, c, props, row) {
  const text = [pins(m, props, 'before', row.old), pins(m, props, 'after', row.new)];
  return m('tr', { class: `vd-diff-row vd-diff-${row.kind}` }, [
    m('td.vd-diff-num', row.old === null ? '' : String(row.old)),
    m('td.vd-diff-num', row.new === null ? '' : String(row.new)),
    mark(m, row.kind, ''),
    m('td.vd-diff-text', [text, codeNodes(m, c, row)])
  ]);
}

// Side-by-side pairs: deletions go left and additions right.
function pairs(rows) {
  const out = [];
  let dels = [];
  let adds = [];
  const flush = () => {
    for (let i = 0; i < Math.max(dels.length, adds.length); i += 1) out.push([dels[i] || null, adds[i] || null]);
    dels = [];
    adds = [];
  };
  for (const row of rows) {
    if (row.kind === 'del') dels.push(row);
    else if (row.kind === 'add') adds.push(row);
    else {
      flush();
      out.push([row, row]);
    }
  }
  flush();
  return out;
}

function sideCells(m, c, props, row, side) {
  if (!row) {
    return [m('td.vd-diff-num.vd-diff-empty'), m('td.vd-diff-mark.vd-diff-empty'), m('td.vd-diff-text.vd-diff-empty')];
  }
  const tone = ` vd-diff-${row.kind}`;
  const number = side === 'before' ? row.old : row.new;
  return [
    m('td', { class: `vd-diff-num${tone}` }, String(number)),
    mark(m, row.kind, tone),
    m('td', { class: `vd-diff-text${tone}` }, [pins(m, props, side, number), codeNodes(m, c, row)])
  ];
}

function cols(m, split) {
  const side = () => [m('col.vd-diff-c-num'), m('col.vd-diff-c-mark'), m('col')];
  if (split) return m('colgroup', [side(), side()]);
  return m('colgroup', [m('col.vd-diff-c-num'), m('col.vd-diff-c-num'), m('col.vd-diff-c-mark'), m('col')]);
}

function body(m, c, props, rows, split) {
  if (!split) return rows.map((row) => unifiedRow(m, c, props, row));
  return pairs(rows).map(([left, right]) =>
    m('tr.vd-diff-row', [sideCells(m, c, props, left, 'before'), sideCells(m, c, props, right, 'after')]));
}

function table(m, rows, split) {
  return m('table.vd-diff-table', [cols(m, split), m('tbody', rows)]);
}

function fold(m, c, props, block, split) {
  const count = block.rows.length;
  const first = block.rows[0].new;
  const last = block.rows[count - 1].new;
  const where = first && last ? ` (lines ${first}-${last})` : '';
  return m('details.vd-diff-fold', [
    m('summary.vd-diff-fold-row', [
      m('span.vd-diff-fold-closed', `${count} unchanged lines hidden${where}`),
      m('span.vd-diff-fold-open', `Hide ${count} unchanged lines`)
    ]),
    table(m, body(m, c, props, block.rows, split), split)
  ]);
}

function blockView(m, c, props, block, split) {
  if (block.kind === 'rows') {
    const span = split ? '6' : '4';
    const hunk = m('tr.vd-diff-hunk', m('td', { colspan: span }, block.header));
    return table(m, [hunk, body(m, c, props, block.rows, split)], split);
  }
  if (block.kind === 'fold') return fold(m, c, props, block, split);
  if (block.kind === 'gap') return m('p.vd-diff-gap', `${block.rows[0].text} unchanged lines not in the patch`);
  return m('p.vd-diff-more', `${block.header} more lines not shown`);
}

function region(m, kind, label, content) {
  return m('div', { class: `vd-diff-view ${kind}`, role: 'region', 'aria-label': label, tabindex: '0' }, content);
}

function header(m, c, props) {
  const { name, change, was } = props;
  return m('figcaption.vd-code-head.vd-diff-head', [
    m('span.vd-diff-name', change ? c.shared.changeName(m, name, change, was) : name),
    change ? c.shared.changeBadge(m, change, '') : null,
    m('span.vd-diff-count', props.count),
    props.language ? m('span.vd-diff-lang', props.language) : null
  ]);
}

function noteItem(m, c, props, note) {
  return m('li.vd-diff-note', { id: `note-${props.uid}-${note.number}`, tabindex: '-1' }, [
    m('span.vd-diff-note-n', String(note.number)),
    m('div.vd-diff-note-body', [m('p.vd-diff-note-meta', note.where), m('p.vd-diff-note-text', c.shared.inline(m, note.text))])
  ]);
}

export function view(m, props, c) {
  const label = `Diff of ${props.name}`;
  const unified = props.blocks.map((block) => blockView(m, c, props, block, false));
  const views = [region(m, 'vd-diff-unified', `${label}, unified`, unified)];
  if (props.split) {
    views.push(region(m, 'vd-diff-sbs', `${label}, side by side`, props.blocks.map((block) => blockView(m, c, props, block, true))));
  }
  const classes = `vb diff vd-code-panel vd-diff vd-diff-d${props.digits}${props.split ? ' vd-diff-split-mode' : ''}`;
  return m('figure', { class: classes, 'data-copy': props.copy }, [
    header(m, c, props),
    views,
    props.notes.length
      ? m('ol.vd-diff-notes', { 'aria-label': `Notes on ${props.name}` }, props.notes.map((note) => noteItem(m, c, props, note)))
      : null
  ]);
}
