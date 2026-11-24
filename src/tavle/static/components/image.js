// Image: a figure with the picture (a link to the file, an inline data URL, or a note), caption and alt line.
// Props: alt, caption, narrow, picture ({kind: link|inline|missing, ...}), summary, copy.
// static/image.js adds the zoom dialog on the mounted link.
function img(m, p, alt) {
  return m('img.vd-image-img', { src: p.src, alt, width: p.width, height: p.height, loading: 'lazy', decoding: 'async' });
}

function picture(m, props) {
  const p = props.picture;
  if (p.kind === 'inline') return img(m, p, props.alt);
  if (p.kind === 'link') return m('a.vd-image-link', { href: p.href, 'aria-label': p.label }, img(m, p, props.alt));
  return m('p.vd-image-missing', [m('span', { 'aria-hidden': 'true' }, '⚠ '), p.note]);
}

export function view(m, props) {
  const width = props.narrow ? 'vd-image-narrow' : 'vd-image-full';
  return m(`figure.vb.image.vd-image.${width}`, { 'data-copy': props.copy }, [
    picture(m, props),
    props.caption ? m('figcaption.vd-image-caption', props.caption) : null,
    m('p.vb-alt.vd-image-alt', props.summary)
  ]);
}
