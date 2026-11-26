import '@ui/static/inputs_fields.js';
import '@ui/static/inputs_runtime.js';
import vectors from './fixtures/classify-url.json';

let runtime, ctx, widgets;
beforeEach(() => {
  document.body.replaceChildren();
  widgets = vi.fn();
  globalThis.tavlePageParts.inputWidgets = widgets;
  ctx = {};
  runtime = globalThis.tavlePageParts.inputRuntime(document, ctx);
});
afterEach(() => vi.restoreAllMocks());

it('classifies the shared URL vectors and rejects unsafe values', () => {
  for (const { url, kind } of vectors) expect(runtime.classifyUrl(url), url).toBe(kind);
  expect(runtime.safeUrl('javascript:x')).toBeNull();
  expect(runtime.safeUrl(123)).toBeNull();
  expect(runtime.safeUrl('docs/x')).toBe('docs/x');
});

it('reads only valid own properties of the declared types', () => {
  const el = document.createElement('div');
  const schema = { s: 'string', n: 'number', b: 'boolean', u: 'url', ss: 'strings', f: 'fields', inherited: 'string' };
  for (const raw of ['bad', 'null', '[]']) {
    el.dataset.props = raw;
    expect(runtime.readProps(el, schema)).toEqual({});
  }
  el.dataset.props = JSON.stringify({
    s: 'ok',
    n: 2,
    b: false,
    u: '/ok',
    ss: ['a'],
    f: [{ name: 'a', type: 'text' }],
    extra: 1
  });
  expect(runtime.readProps(el, schema)).toEqual({
    s: 'ok',
    n: 2,
    b: false,
    u: '/ok',
    ss: ['a'],
    f: [{ name: 'a', type: 'text', required: false }]
  });
  el.dataset.props = '{"s":1,"n":1e400,"b":0,"u":"javascript:x","ss":["a",1],"f":[]}';
  expect(runtime.readProps(el, schema)).toEqual({ f: [] });
  el.dataset.props = JSON.stringify({ f: Array(51).fill({ name: 'a', type: 'text' }) });
  expect(runtime.readProps(el, schema)).toEqual({});
});

it('keeps state and isolates throwing watchers until unsubscribed', () => {
  const log = vi.spyOn(console, 'error').mockImplementation(() => {});
  const watcher = vi.fn();
  const off = runtime.formState.watch('x', watcher);
  runtime.formState.watch('x', () => {
    throw new Error('watch');
  });
  runtime.formState.set('x', 3);
  expect(runtime.formState.get('x')).toBe(3);
  expect(watcher).toHaveBeenCalledWith(3);
  expect(log).toHaveBeenCalledOnce();
  off();
  runtime.formState.set('x', 4);
  expect(watcher).toHaveBeenCalledOnce();
});

it('hydrates registered elements once and exposes frozen helpers to widgets', () => {
  document.body.innerHTML =
    '<div data-component="known" data-props=\'{"x":"yes"}\'></div><div data-component="unknown"></div>';
  const hydrate = vi.fn();
  runtime.register('known', { props: { x: 'string' }, hydrate });
  runtime.hydrate(document);
  runtime.hydrate(document);
  expect(hydrate).toHaveBeenCalledOnce();
  expect(hydrate.mock.calls[0][1]).toEqual({ x: 'yes' });
  expect(document.querySelector('[data-component=unknown]').hasAttribute('data-hydrated')).toBe(false);
  runtime.mountInputs();
  expect(widgets).toHaveBeenCalledWith(
    expect.objectContaining({ register: runtime.register, sendAnswer: ctx.inputs.sendAnswer })
  );
  expect(Object.isFrozen(ctx.inputs)).toBe(true);
});

it('sends answers while pausing only enabled controls and restores focus', async () => {
  document.body.innerHTML =
    '<div class="block"><div id="root"><div class="choice-item" data-item="id"></div><button>go</button><input disabled><span class="choice-state"></span></div></div>';
  const root = document.querySelector('#root'),
    button = root.querySelector('button'),
    disabled = root.querySelector('input');
  expect(await ctx.inputs.sendAnswer(root, 'choice', 1)).toBe(false);
  let resolve;
  ctx.answer = vi.fn(
    () =>
      new Promise((r) => {
        resolve = r;
      })
  );
  expect(await ctx.inputs.sendAnswer(document.body, 'missing', 1)).toBe(false);
  button.focus();
  const pending = ctx.inputs.sendAnswer(root, 'choice', 1, 'text');
  expect(ctx.answer).toHaveBeenCalledWith('id', 1, 'text');
  expect(button.disabled).toBe(true);
  resolve(true);
  expect(await pending).toBe(true);
  expect(button.disabled).toBe(false);
  expect(disabled.disabled).toBe(true);
  expect(document.activeElement).toBe(button);
  expect(root.querySelector('.choice-state').textContent).toBe('Sent');
  root.querySelector('.choice-state').textContent = '';
  ctx.answer = vi.fn().mockResolvedValue(false);
  expect(await ctx.inputs.sendAnswer(root, 'choice', 2)).toBe(false);
  expect(root.querySelector('.choice-state').textContent).toBe('');
});

it('reports errors and handles submit and note clearing', () => {
  document.body.innerHTML =
    '<div id="root"><form><input><span class="choice-state">Sent</span><span id="err" class="choice-error"></span></form></div>';
  const root = document.querySelector('#root'),
    input = root.querySelector('input'),
    form = root.querySelector('form');
  ctx.inputs.fail(root, 'choice', 'Oops', input);
  expect(input.getAttribute('aria-describedby')).toBe('err');
  expect(document.activeElement).toBe(input);
  expect(root.querySelector('.choice-error').textContent).toBe('Oops');
  const handler = vi.fn();
  ctx.inputs.onSubmit(root, 'choice', handler);
  const event = new Event('submit', { cancelable: true });
  form.dispatchEvent(event);
  expect(event.defaultPrevented).toBe(true);
  expect(handler).toHaveBeenCalledWith(form);
  for (const type of ['input', 'change']) {
    root.querySelector('.choice-state').textContent = 'Sent';
    input.dispatchEvent(new Event(type, { bubbles: true }));
    expect(root.querySelector('.choice-state').textContent).toBe('');
  }
});
