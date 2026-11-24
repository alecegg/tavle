// Code panel: header, a line-numbered <pre>, tokens highlighted by the server.
// Props: title, language, langClass, wrap, numbers, first, lines (per line: [class suffix, text] pairs),
// marked (line numbers), note (the header's marked-lines text). The text is never changed by
// highlighting: the tokens of a line concatenate to it. The Copy button comes from code.js (static).
const MAX_DIGIT_CLASS = 6;

export function tokenNodes(m, tokens) {
  return tokens.map(([kind, text]) => (kind ? m(`span.vd-code-${kind}`, text) : text));
}

export function lineNode(m, number, tokens, marked) {
  const attrs = { class: 'vd-code-line', 'data-line': String(number) };
  if (marked) attrs['data-mark'] = '1';
  return m('span', attrs, [tokenNodes(m, tokens), '\n']);
}

// opts: cls (leading classes), line(number, tokens, marked) for a custom line, arrange(items) to group lines.
export function panel(m, props, opts = {}) {
  const first = props.first;
  const last = first + props.lines.length - 1;
  const marked = new Set(props.marked);
  const makeLine = opts.line || ((number, tokens, isMarked) => lineNode(m, number, tokens, isMarked));
  const items = props.lines.map((tokens, i) => ({ number: first + i, node: makeLine(first + i, tokens, marked.has(first + i)) }));
  const arrange = opts.arrange || ((all) => all.map((item) => item.node));
  const raw = props.lines.map((line) => line.map((token) => token[1]).join('')).join('\n');
  const digits = Math.min(String(last).length, MAX_DIGIT_CLASS);
  const lead = opts.cls === undefined ? 'vb code' : opts.cls;
  const classes = [lead, 'vd-code-panel', 'vd-code', `vd-code-d${digits}`, props.wrap && 'vd-code-wrap', !props.numbers && 'vd-code-nonum']
    .filter((name) => name)
    .join(' ');
  const label = props.language || 'text';
  const region = `${props.title || 'Code'}, ${label}, lines ${first} to ${last}`;
  return m('figure', { class: classes, 'data-copy': raw }, [
    m('figcaption.vd-code-head', [
      props.title ? m('span.vd-code-title', props.title) : null,
      m('span.vd-code-lang', label),
      props.note ? m('span.vd-code-marks', props.note) : null
    ]),
    m('div.vd-code-scroll', { role: 'region', 'aria-label': region, tabindex: '0' }, [
      m('pre.vd-code-pre', m('code', { class: props.language ? `language-${props.langClass}` : undefined }, arrange(items)))
    ])
  ]);
}

export function view(m, props) {
  return panel(m, props);
}
