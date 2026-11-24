// Form block as a component: typed fields, a count of required fields left and a send row.
// `props.fields[].client` is the whitelist recap.js reads back; the rest is what is drawn.

// A text field allowed more characters than this is a textarea; shorter ones are one line.
const LONG_TEXT_LIMIT = 100;

function isLongText(f) {
  return f.type === 'text' && f.limit > LONG_TEXT_LIMIT;
}

// An unchosen select shows `Choose…`. A required one cannot go back to it, so it is disabled;
// its empty value still fails the required check in recap.js.
function select(m, f, attrs) {
  // The attribute, not the property, so a serialised page keeps the choice too.
  const keepSelected = (vnode) => vnode.dom.setAttribute('selected', '');
  const placeholder = m('option', { value: '', disabled: f.required, oncreate: keepSelected }, 'Choose…');
  return m('select', attrs, [placeholder, ...f.options.map((o) => m('option', o))]);
}

function control(m, f, attrs) {
  if (f.type === 'checkbox') return m('input', { type: 'checkbox', ...attrs });
  if (f.type === 'select') return select(m, f, attrs);
  if (f.type === 'number') return m('input', { type: 'number', step: 'any', ...attrs, min: f.minText, max: f.maxText });
  if (isLongText(f)) return m('textarea', { rows: '4', maxlength: f.limit, ...attrs });
  return m('input', { type: 'text', maxlength: f.limit, ...attrs });
}

function row(m, f, group) {
  const hintId = `${group}-${f.name}-hint`;
  const attrs = { 'data-field': f.name, name: `${group}-${f.name}` };
  if (f.required) attrs['aria-required'] = 'true';
  if (f.hint) attrs['aria-describedby'] = hintId;
  const label = m('span.form-label', f.label + (f.required ? ' *' : ''));
  const input = control(m, f, attrs);
  return m(`div.form-row.form-${f.type}${isLongText(f) ? '.form-long' : ''}`, [
    m('label.form-field', f.type === 'checkbox' ? [input, label] : [label, input]),
    f.hint ? m('span.form-hint', { id: hintId }, f.hint) : null
  ]);
}

export function view(m, props, c, blockId) {
  const id = c.shared.pyStr(blockId);
  const group = `form-${blockId ?? ''}`;
  const form = m('form.form-item', { 'data-item': id, novalidate: true }, [
    props.title ? m('p.form-title', props.title) : null,
    m('div.form-body', m('div.form-grid', props.fields.map((f) => row(m, f, group)))),
    m('p.form-remaining', { 'aria-live': 'polite' }),
    c.shared.inputFooter(m, 'form', props.submit, id)
  ]);
  return c.shared.inputRoot(m, 'form', { fields: props.fields.map((f) => f.client) }, '', form);
}
