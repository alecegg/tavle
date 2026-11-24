// Markup contracts of the input widgets (group semantics, ids that tie labels, hints and errors
// together, ticks, field order). The DOM-equality fixtures in inputs.test.js pin the whole tree;
// these name the accessibility and design facts that the stylesheets and scripts rely on.
import { loadComponents } from './registry.js';

const { m, components } = loadComponents();

// The component's DOM for props as the server prepares them (see blocks_render/inputs*.py).
function mount(block, props, id = 'w') {
  const host = document.createElement('div');
  m.render(host, components[block].view(m, props, components, id));
  return host;
}

const option = (label, extra = {}) => ({ label, value: label, detail: '', recommended: false, ...extra });
const choice = (options, extra = {}) => ({ question: 'Which?', options, multiple: false, comment: false, maxNote: 8000, ...extra });

describe('choice markup', () => {
  it('sits in a fieldset with a legend, required inputs and an error the group points at', () => {
    const host = mount('choice', choice([option('a'), option('b')]));
    expect(host.querySelector('fieldset > legend').textContent).toBe('Which?');
    expect(host.querySelectorAll('input[aria-required="true"]').length).toBe(2);
    expect(host.querySelector('#choice-error-w').getAttribute('role')).toBe('alert');
    expect(host.querySelector('fieldset').getAttribute('aria-describedby')).toBe('choice-error-w');
    expect(host.querySelector('[style], script')).toBeNull();
  });

  it('makes each option one label card with the detail as text, never markup', () => {
    const host = mount('choice', choice([option('A', { detail: '<b>d</b>' })]));
    const card = host.querySelector('label.choice-option');
    expect(card.querySelectorAll('input').length).toBe(1);
    expect(card.querySelector('.choice-detail').textContent).toBe('<b>d</b>');
    expect(card.querySelector('b')).toBeNull();
  });

  it('uses checkboxes for several picks and radios for one', () => {
    expect(mount('choice', choice([option('a')], { multiple: true })).querySelector('input').type).toBe('checkbox');
    expect(mount('choice', choice([option('a')])).querySelector('input').type).toBe('radio');
  });

  it('names the recommended option as described by its badge', () => {
    const host = mount('choice', choice([option('a'), option('b', { recommended: true })]));
    const badge = host.querySelector('.choice-rec');
    expect(badge.textContent).toBe('Recommended');
    expect(host.querySelectorAll('.choice-rec').length).toBe(1);
    expect(host.querySelector('input[aria-describedby]').getAttribute('aria-describedby')).toBe(badge.id);
  });

  it('adds the capped note box only when asked', () => {
    expect(mount('choice', choice([option('a')])).querySelector('textarea')).toBeNull();
    const note = mount('choice', choice([option('a')], { comment: true })).querySelector('textarea');
    expect(note.getAttribute('maxlength')).toBe('8000');
  });
});

describe('comment markup', () => {
  const host = () => mount('comment', { label: 'Why?', submit: 'Send', maxNote: 8000 });

  it('links the label to the textarea and the counter describes it', () => {
    const el = host();
    expect(el.querySelector('label.comment-note').getAttribute('for')).toBe('comment-text-w');
    expect(el.querySelector('#comment-text-w').getAttribute('aria-describedby')).toBe('comment-count-w');
    expect(el.querySelector('#comment-count-w').textContent).toBe('0 / 8000');
    expect(el.querySelector('.comment-announce').getAttribute('aria-live')).toBe('polite');
    expect(el.querySelector('[style], script')).toBeNull();
  });

  it('keeps the state and alert regions beside the send button', () => {
    const el = host();
    expect(el.querySelector('button.comment-send').type).toBe('submit');
    expect(el.querySelector('.comment-state').getAttribute('aria-live')).toBe('polite');
    expect(el.querySelector('#comment-error-w').getAttribute('role')).toBe('alert');
  });
});

describe('form markup', () => {
  const field = (extra) => ({ label: extra.name, required: false, hint: '', client: { name: extra.name, type: extra.type }, ...extra });
  const fields = [
    field({ name: 'who', type: 'text', required: true, hint: 'Up to 20 characters.', limit: 20 }),
    field({ name: 'n', type: 'number', hint: 'From 1 to 9.', minText: '1', maxText: '9' }),
    field({ name: 'low', type: 'number', hint: 'At least 3.', minText: '3' }),
    field({ name: 'r', type: 'select', options: ['a'] }),
    field({ name: 'ok', type: 'checkbox' })
  ];
  const host = () => mount('form', { title: 'T', submit: 'Submit', fields });

  it('makes each field a row with a label, a control and a hint when it has one', () => {
    const el = host();
    expect(el.querySelectorAll('.form-row').length).toBe(5);
    expect(el.querySelectorAll('label.form-field').length).toBe(5);
    const hint = el.querySelector('#form-w-who-hint');
    expect(hint.className).toBe('form-hint');
    expect(hint.textContent).toBe('Up to 20 characters.');
    expect(el.querySelector('[data-field="who"]').getAttribute('aria-describedby')).toBe('form-w-who-hint');
    expect(el.querySelectorAll('.form-hint').length).toBe(3);
  });

  it('sits the fields in a grid and leaves the required count for the script', () => {
    const el = host();
    expect(el.querySelector('.form-body > .form-grid')).not.toBeNull();
    const remaining = el.querySelector('p.form-remaining');
    expect(remaining.getAttribute('aria-live')).toBe('polite');
    expect(remaining.textContent).toBe('');
    expect(el.querySelector('[style], script')).toBeNull();
  });

  it('puts a checkbox control before its label text', () => {
    const row = host().querySelector('.form-checkbox');
    expect(row.querySelector('input').compareDocumentPosition(row.querySelector('.form-label')) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('starts a select on a Choose… placeholder, disabled when the field is required', () => {
    const select = (required) => mount('form', { title: '', submit: 'Go', fields: [field({ name: 's', type: 'select', options: ['a'], required })] });
    const first = (el) => el.querySelector('select > option');
    expect(first(select(true)).textContent).toBe('Choose…');
    expect(first(select(true)).hasAttribute('disabled')).toBe(true);
    expect(first(select(true)).hasAttribute('selected')).toBe(true);
    expect(first(select(false)).hasAttribute('disabled')).toBe(false);
    expect(first(select(false)).getAttribute('value')).toBe('');
  });

  it('draws a text field above the length threshold as a full-row textarea', () => {
    const text = (limit) => mount('form', { title: '', submit: 'Go', fields: [field({ name: 't', type: 'text', limit })] });
    const long = text(600);
    expect(long.querySelector('textarea[data-field="t"]').getAttribute('maxlength')).toBe('600');
    expect(long.querySelector('.form-row').classList.contains('form-long')).toBe(true);
    const short = text(10);
    expect(short.querySelector('textarea')).toBeNull();
    expect(short.querySelector('input[type="text"]').getAttribute('maxlength')).toBe('10');
  });

  it('marks a required select', () => {
    const el = mount('form', { title: '', submit: 'Go', fields: [field({ name: 's', type: 'select', options: ['a'], required: true })] });
    expect(el.querySelector('select').getAttribute('aria-required')).toBe('true');
    expect(el.querySelector('#form-error-w')).not.toBeNull();
  });
});

describe('ranking markup', () => {
  const items = [{ label: 'Same', value: 'x', detail: '', name: 'Same (x)' }, { label: 'Same', value: 'y', detail: '', name: 'Same (y)' }];
  const host = () => mount('ranking', { question: 'Q', items });

  it('is an ordered list in a fieldset with two labelled move buttons per row', () => {
    const el = host();
    expect(el.querySelector('fieldset > legend').textContent).toBe('Q');
    expect(el.querySelector('ol.ranking-list').getAttribute('aria-describedby')).toBe('ranking-hint-w');
    expect(el.querySelectorAll('.ranking-move').length).toBe(4);
    expect([...el.querySelectorAll('.ranking-move')].map((b) => b.getAttribute('aria-label'))).toEqual([
      'Move Same (x) up', 'Move Same (x) down', 'Move Same (y) up', 'Move Same (y) down'
    ]);
    expect(el.querySelector('.ranking-live').getAttribute('role')).toBe('status');
  });

  it('wraps each row line, hides the grip and keeps the value and label on the row', () => {
    const row = host().querySelector('li.ranking-row');
    expect(row.querySelector(':scope > .ranking-line > .ranking-grip').getAttribute('aria-hidden')).toBe('true');
    expect([...row.querySelectorAll('.ranking-move')].map((b) => b.textContent)).toEqual(['\u2191', '\u2193']); // never left and right
    expect(row.dataset.id).toBe('x');
    expect(row.dataset.label).toBe('Same');
  });
});

describe('slider markup', () => {
  const props = (extra) => ({ label: 'L', min: 0, max: 10, step: 1, minText: '0', maxText: '10', stepText: '1', ends: ['0', '10'], ticks: 0, ...extra });

  it('puts the end labels in order and starts unchosen', () => {
    const el = mount('slider', props({ ends: ['Low', 'High'] }));
    expect([...el.querySelectorAll('.slider-end')].map((e) => e.textContent)).toEqual(['Low', 'High']);
    const input = el.querySelector('input[type="range"]');
    expect(input.getAttribute('aria-valuetext')).toBe('Not chosen yet');
    expect([input.getAttribute('min'), input.getAttribute('max'), input.getAttribute('step')]).toEqual(['0', '10', '1']);
    expect(el.querySelector('output.slider-value').getAttribute('for')).toBe(input.id);
    expect(el.querySelector('[style], script')).toBeNull();
  });

  it('draws one tick mark per position, or none', () => {
    expect(mount('slider', props({ ticks: 6 })).querySelectorAll('.slider-ticks > span').length).toBe(6);
    expect(mount('slider', props()).querySelector('.slider-ticks')).toBeNull();
  });
});
