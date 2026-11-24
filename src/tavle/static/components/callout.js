// Callout block as a component. Same DOM as blocks_render/callout.py.
// A component file has no imports: it exports `view(m, props, components)` and may export helpers;
// `components.shared` holds the helpers blocks have in common.
// Each tone has a word and an icon of its own shape (see icons.js).
const TONES = { info: ['Info', 'info'], decision: ['Decision', 'diamond'], risk: ['Risk', 'triangle'], warning: ['Warning', 'alert'], success: ['Success', 'check-circle'] };

export function copyText(props) {
  return [props.title, props.text].filter((part) => part).join('\n');
}

export function view(m, props, c) {
  const [word, shape] = TONES[props.tone];
  const paragraphs = props.text.split(/\n\s*\n/).filter((p) => p.trim());
  return m(`aside.vb.callout.vd-callout.vd-callout-${props.tone}`, { 'data-copy': copyText(props) }, [
    m('p.vd-callout-label', [c.icons.icon(m, shape, 'vd-callout-glyph'), ` ${word}`]),
    props.title === undefined ? null : m('p.vd-callout-title', props.title),
    paragraphs.map((p) => m('p.vd-callout-text', c.shared.inline(m, p.trim())))
  ]);
}
