// Helpers the block components share. Not a block: it has no `view`.
export function inline(m, text) {
  return text.split(/`([^`\n]+)`/).map((part, i) => (i % 2 ? m('code', part) : part));
}

// Python's str() of a JSON value, for text a block shows from a cell.
export function pyStr(value) {
  if (value === true) return 'True';
  if (value === false) return 'False';
  if (value === null || value === undefined) return 'None';
  return String(value);
}

export function words(text) {
  return text.split(/\s+/).filter((word) => word).join(' ');
}

export function groupThousands(digits) {
  return digits.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Python's f"{value:.{places}f}": exact value, ties to even (toFixed rounds ties up).
export function fixed(value, places) {
  const scaled = Math.abs(value) * 10 ** places;
  const tieDown = scaled % 1 === 0.5 && Math.floor(scaled) % 2 === 0;
  return tieDown ? (Math.floor(scaled) / 10 ** places).toFixed(places) : Math.abs(value).toFixed(places);
}

// Python's f"{value:,}" or f"{value:,.{decimals}f}": commas, and fixed places when asked.
export function formatNumber(value, decimals) {
  const sign = value < 0 || Object.is(value, -0) ? '-' : '';
  const hasPlaces = Number.isInteger(decimals);
  const digits = hasPlaces ? fixed(value, decimals) : String(Math.abs(value));
  const [whole, fraction] = digits.split('.');
  return sign + groupThousands(whole) + (fraction === undefined ? '' : `.${fraction}`);
}

export function countNoun(count, one, many) {
  return `${count} ${count === 1 ? one : many}`;
}

export function objects(list) {
  return Array.isArray(list) ? list.filter((item) => item !== null && typeof item === 'object' && !Array.isArray(item)) : [];
}

const CHANGE_GLYPHS = { added: '+', modified: '~', removed: '-', renamed: '->' };

// The shared change vocabulary: glyph, word, and the previous value (a rename shows it in the name).
export function changeBadge(m, change, was) {
  const glyph = m('span.vd-change-glyph', { 'aria-hidden': 'true' }, CHANGE_GLYPHS[change]);
  const badge = m(`span.vd-change-badge.vd-change-${change}`, [glyph, ` ${change}`]);
  if (!was || change === 'renamed') return badge;
  return [badge, ' ', m('span.vd-change-was', `was ${was}`)];
}

// A name with the change styling; a rename reads `old -> new`.
export function changeName(m, name, change, was, tag = 'span') {
  if (!change) return name;
  const shown = m(`${tag}.vd-change-name`, name);
  if (change !== 'renamed') return shown;
  return [m(`${tag}.vd-change-old`, was), ' → ', shown];
}

// Shapes the server computed ([tag, attributes, text or child shapes], see blocks_render/svg.py) as SVG nodes.
export function scene(m, shapes) {
  return shapes.map(([tag, attrs, content]) => m(tag, attrs, Array.isArray(content) ? scene(m, content) : content));
}

// A keyboard-focusable sideways-scrolling region around a data grid.
export function dataScroll(m, grid, label) {
  return m('div.vb-data-scroll', { role: 'region', 'aria-label': label, tabindex: '0' }, grid);
}

// A titled card: the heading is dropped when empty.
export function card(m, title, body, kind = '') {
  const classes = kind.split(' ').filter((name) => name).map((name) => `.${name}`).join('');
  return m(`section.vb-card${classes}`, [title ? m('h4.vb-title', title) : null, body]);
}

// The SVG root with a text alternative: role=img, <title>, <desc>.
export function svgRoot(m, title, desc, box, cls, inner, extra = {}) {
  const attrs = { ...extra, viewBox: box, role: 'img', 'aria-label': title };
  if (cls) attrs.class = cls;
  return m('svg', attrs, [m('title', title), m('desc', desc), inner]);
}

// The send row every input widget ends with: the button, its status and its error line.
export function inputFooter(m, kind, label, id) {
  return [
    m(`button.${kind}-send`, { type: 'submit' }, label),
    m(`span.${kind}-state`, { 'aria-live': 'polite' }),
    m(`p.${kind}-error`, { id: `${kind}-error-${id}`, role: 'alert' })
  ];
}

// An input widget's root: recap.js hydrates `data-component` with the whitelisted `data-props`.
export function inputRoot(m, kind, props, title, form) {
  return m(`div.vb.${kind}`, { 'data-component': kind, 'data-props': JSON.stringify(props) }, card(m, title, form));
}

export function badge(m, text, kind = '') {
  return m(`span.vb-badge${kind ? `.${kind}` : ''}`, text);
}

// A scrolling table of rows with a change column. Header cells are text or nodes; a row is
// { cells, change, was, label }: any change adds a `change` column holding each row's badge.
export function changeTable(m, header, rows, label) {
  const changed = rows.some((row) => row.change);
  const heads = [...header, ...(changed ? ['change'] : [])];
  const body = rows.map((row) => {
    const badgeCell = changed ? [m('td', row.change ? changeBadge(m, row.change, row.was) : null)] : [];
    const attrs = row.change ? { class: `vd-change-row vd-change-${row.change}`, 'aria-label': `${row.change} ${row.label}` } : {};
    return m('tr', attrs, [...row.cells.map((cell) => m('td', cell)), ...badgeCell]);
  });
  return m('div.vb-fields-scroll', { role: 'region', 'aria-label': label, tabindex: '0' },
    m('table.vb-fields', [m('thead', m('tr', heads.map((head) => m('th', head)))), m('tbody', body)]));
}

// The key marker cell of a field row, empty for any other field.
export function keyCell(m, isKey) {
  return isKey ? badge(m, 'key', 'vb-badge-key') : '';
}

// Rows of a table of fields: the name (with its change styling), the type and, with `withKey`, the key marker.
export function typedRows(m, fields, withKey) {
  return fields.map((f) => ({
    cells: [changeName(m, f.name, f.change, f.was), f.type, ...(withKey ? [keyCell(m, f.key)] : [])],
    change: f.change,
    was: f.was,
    label: f.name
  }));
}

// Tabs and columns. `held` maps a held block id to the element the server filled (mount.js lifts it
// out of the host before drawing); each slot adopts that element's children, so held blocks are
// the page's own nodes: they mount, enhance and update on their own, not through this view.
function slot(m, held, id) {
  const nodes = held.has(id) ? [...held.get(id).childNodes] : [];
  return m('div.vd-containers-slot', { oncreate: (vnode) => vnode.dom.append(...nodes), onbeforeupdate: () => false });
}

function panel(m, kind, held, prefix, n, spec) {
  const headId = `${prefix}-${n}-h`;
  const heading = spec.label ? m('h4.vd-containers-label', { id: headId }, spec.label) : null;
  const name = spec.label ? { 'aria-labelledby': headId } : { 'aria-label': `Column ${n}` };
  const cls = kind === 'tabs' ? 'vd-ctabs-panel' : 'vd-columns-panel';
  return m(`section.vd-containers-panel.${cls}`, name, [heading, spec.blocks.map((id) => slot(m, held, id))]);
}

export function containerView(m, kind, props, blockId, held) {
  const panels = props.panels;
  const prefix = `vd-c${kind.slice(0, 3)}-${blockId || 'x'}`;
  const inner = panels.map((spec, i) => panel(m, kind, held, prefix, i + 1, spec));
  const noun = kind === 'tabs' ? 'tab' : 'column';
  const names = panels.filter((spec) => spec.label).map((spec) => spec.label).join(', ');
  const count = `${panels.length} ${noun}${panels.length === 1 ? '' : 's'}`;
  const grid = kind === 'columns' ? m(`div.vd-columns-grid.vd-columns-n${panels.length}`, inner) : inner;
  const cls = kind === 'tabs' ? 'vd-ctabs' : 'vd-columns';
  // The page contents already lists tab names, so only columns draw an index line.
  const index = kind === 'tabs' ? [] : [m('p.vb-alt.vb-sr.vd-containers-alt', names ? `${count}: ${names}` : count)];
  return m(`section.vb.${kind}.vd-containers.${cls}`, { 'aria-label': kind === 'tabs' ? 'Tabs' : 'Columns' }, [
    ...index,
    grid
  ]);
}
