// Callout block as a component. Same DOM as blocks_render/callout.py.
// A component file has no imports: it exports `view(m, props, components)` and may export helpers;
// `components.shared` holds the helpers blocks have in common.
// Each tone has a word and an icon of its own shape, drawn on a 16-unit box so no font is needed.
const FILLED = { fill: 'currentColor' };
const TONES = {
  info: ['Info', [['circle', { cx: '8', cy: '8', r: '6.5' }], ['path', { d: 'M8 7.2v4' }], ['circle', { cx: '8', cy: '4.9', r: '0.9', ...FILLED }]]],
  decision: ['Decision', [['path', { d: 'M8 1.5L14.5 8L8 14.5L1.5 8Z', ...FILLED }]]],
  risk: ['Risk', [['path', { d: 'M8 2L14.5 13.5H1.5Z', ...FILLED }]]],
  warning: ['Warning', [['circle', { cx: '8', cy: '8', r: '6.5' }], ['path', { d: 'M8 4.4v4.3' }], ['circle', { cx: '8', cy: '11.2', r: '0.9', ...FILLED }]]],
  success: ['Success', [['circle', { cx: '8', cy: '8', r: '6.5' }], ['path', { d: 'M5 8.2l2.1 2.1L11 5.8' }]]]
};

function icon(m, shapes) {
  return m('svg.vd-callout-glyph', { viewBox: '0 0 16 16', 'aria-hidden': 'true', focusable: 'false' }, shapes.map(([tag, attrs]) => m(tag, attrs)));
}

export function copyText(props) {
  return [props.title, props.text].filter((part) => part).join('\n');
}

export function view(m, props, c) {
  const [word, shapes] = TONES[props.tone];
  const paragraphs = props.text.split(/\n\s*\n/).filter((p) => p.trim());
  return m(`aside.vb.callout.vd-callout.vd-callout-${props.tone}`, { 'data-copy': copyText(props) }, [
    m('p.vd-callout-label', [icon(m, shapes), ` ${word}`]),
    props.title === undefined ? null : m('p.vd-callout-title', props.title),
    paragraphs.map((p) => m('p.vd-callout-text', c.shared.inline(m, p.trim())))
  ]);
}
