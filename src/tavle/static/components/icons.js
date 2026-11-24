// The one owner of the icon drawings. Not a block: it has no `view`.
// Icons are drawn, never typed: a glyph needs a font the machine may lack. Each is a list of
// [element, attributes] on a 16-unit box. Strokes and fills take the text colour (`currentColor`),
// so a tone class on the parent sets the colour.
const FILLED = { fill: 'currentColor', stroke: 'none' };
const ICONS = {
  check: [['path', { d: 'M3 8.5l3.2 3.2L13 4.5' }]],
  'check-circle': [['circle', { cx: '8', cy: '8', r: '6.5' }], ['path', { d: 'M5 8.2l2.1 2.1L11 5.8' }]],
  cross: [['path', { d: 'M4 4l8 8M12 4l-8 8' }]],
  dot: [['circle', { cx: '8', cy: '8', r: '4', ...FILLED }]],
  ring: [['circle', { cx: '8', cy: '8', r: '5' }]],
  half: [['circle', { cx: '8', cy: '8', r: '5' }], ['path', { d: 'M8 3a5 5 0 0 0 0 10Z', ...FILLED }]],
  triangle: [['path', { d: 'M8 2L14.5 13.5H1.5Z', ...FILLED }]],
  'triangle-down': [['path', { d: 'M8 14L14.5 2.5H1.5Z', ...FILLED }]],
  bar: [['path', { d: 'M2 6.5h12v3H2Z', ...FILLED }]],
  diamond: [['path', { d: 'M8 1.5L14.5 8L8 14.5L1.5 8Z', ...FILLED }]],
  info: [['circle', { cx: '8', cy: '8', r: '6.5' }], ['path', { d: 'M8 7.2v4' }], ['circle', { cx: '8', cy: '4.9', r: '0.9', ...FILLED }]],
  alert: [['circle', { cx: '8', cy: '8', r: '6.5' }], ['path', { d: 'M8 4.4v4.3' }], ['circle', { cx: '8', cy: '11.2', r: '0.9', ...FILLED }]],
  pencil: [['path', { d: 'M3 13l0.8-3.2L10.6 3a1.4 1.4 0 0 1 2 0l0.4 0.4a1.4 1.4 0 0 1 0 2L6.2 12.2Z' }], ['path', { d: 'M9.3 4.4l2.3 2.3' }]]
};

// An `svg.<cls>` icon: decorative (`aria-hidden`), sized and placed by the caller's css class.
export function icon(m, name, cls) {
  const attrs = {
    viewBox: '0 0 16 16',
    'aria-hidden': 'true',
    focusable: 'false',
    fill: 'none',
    stroke: 'currentColor',
    'stroke-width': '1.8',
    'stroke-linecap': 'round',
    'stroke-linejoin': 'round'
  };
  return m(`svg.${cls}`, attrs, ICONS[name].map(([tag, shape]) => m(tag, shape)));
}
