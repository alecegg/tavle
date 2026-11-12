// Callout block as a component. Same DOM as blocks_render/callout.py.
// A component file has no imports: it exports `view(m, props, components)` and may export helpers;
// `components.shared` holds the helpers blocks have in common.
const TONES = {
  info: ['i', 'Info'],
  decision: ['◆', 'Decision'],
  risk: ['▲', 'Risk'],
  warning: ['!', 'Warning'],
  success: ['✓', 'Success']
};

export function copyText(props) {
  return [props.title, props.text].filter((part) => part).join('\n');
}

export function view(m, props, c) {
  const [glyph, word] = TONES[props.tone];
  const paragraphs = props.text.split(/\n\s*\n/).filter((p) => p.trim());
  return m(`aside.vb.callout.vd-callout.vd-callout-${props.tone}`, { 'data-copy': copyText(props) }, [
    m('p.vd-callout-label', [m('span.vd-callout-glyph', { 'aria-hidden': 'true' }, glyph), ` ${word}`]),
    props.title === undefined ? null : m('p.vd-callout-title', props.title),
    paragraphs.map((p) => m('p.vd-callout-text', c.shared.inline(m, p.trim())))
  ]);
}
