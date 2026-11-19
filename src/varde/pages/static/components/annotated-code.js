// Annotated code: the code panel plus numbered notes anchored to line ranges. Pins and notes
// link by plain href; quiet stretches fold into a native <details>. Props: the code props plus
// uid, columns, folds ([from, to] runs), copy and notes (number, start, end, label, text, kind,
// glyph, word, tone, where).
function pin(m, uid, note) {
  const name = `Note ${note.number}, ${note.word.toLowerCase()}, ${note.where}`;
  return m('a', {
    class: `vd-annotated-pin vd-annotated-k-${note.kind}`,
    id: `pin-${uid}-${note.number}`,
    href: `#note-${uid}-${note.number}`,
    'aria-label': name
  }, String(note.number));
}

function foldRow(m, first, last) {
  return m('summary.vd-annotated-fold-row', [
    m('span.vd-annotated-fold-closed', `${last - first + 1} lines hidden (lines ${first}-${last})`),
    m('span.vd-annotated-fold-open', `Hide lines ${first}-${last}`)
  ]);
}

function noteItem(m, c, uid, note) {
  return m('li', {
    class: `vd-annotated-note vd-annotated-t-${note.tone}`,
    id: `note-${uid}-${note.number}`,
    tabindex: '-1',
    'data-from': String(note.start),
    'data-to': String(note.end)
  }, [
    m('a.vd-annotated-back', { href: `#pin-${uid}-${note.number}`, 'aria-label': `Note ${note.number}: back to ${note.where}` }, String(note.number)),
    m('div.vd-annotated-body', [
      m('p.vd-annotated-meta', [m('span.vd-annotated-glyph', { 'aria-hidden': 'true' }, note.glyph), ` ${note.word} · ${note.where}`]),
      note.label ? m('span.vd-annotated-label', note.label) : null,
      m('p.vd-annotated-text', c.shared.inline(m, note.text))
    ])
  ]);
}

function arrangeFolds(m, folds) {
  const startAt = new Map(folds.map(([from, to]) => [from, [from, to]]));
  return (items) => {
    const out = [];
    let group = null;
    let closing = 0;
    for (const { number, node } of items) {
      if (startAt.has(number)) {
        const [from, to] = startAt.get(number);
        group = { summary: foldRow(m, from, to), nodes: [] };
        closing = to;
      }
      if (group) group.nodes.push(node);
      else out.push(node);
      if (group && number === closing) {
        out.push(m('details.vd-annotated-fold', [group.summary, group.nodes]));
        group = null;
        closing = 0;
      }
    }
    return out;
  };
}

export function view(m, props, c) {
  const code = c.code;
  if (!props.notes.length) return code.panel(m, props, { cls: 'vb annotated-code' });
  const pinsAt = new Map();
  for (const note of props.notes) {
    if (!pinsAt.has(note.start)) pinsAt.set(note.start, []);
    pinsAt.get(note.start).push(pin(m, props.uid, note));
  }
  const line = (number, tokens, marked) => {
    const pins = pinsAt.get(number);
    const attrs = { class: pins ? 'vd-code-line vd-annotated-pinned' : 'vd-code-line', 'data-line': String(number) };
    if (marked) attrs['data-mark'] = '1';
    return m('span', attrs, [pins ? m('span.vd-annotated-pins', pins) : null, code.tokenNodes(m, tokens), '\n']);
  };
  const figure = code.panel(m, props, { cls: '', line, arrange: arrangeFolds(m, props.folds) });
  return m('div', { class: `vb annotated-code vd-annotated-code vd-annotated-c${props.columns}`, 'data-copy': props.copy }, [
    figure,
    m('ol.vd-annotated-notes', { 'aria-label': `Notes on ${props.title}` }, props.notes.map((note) => noteItem(m, c, props.uid, note)))
  ]);
}
