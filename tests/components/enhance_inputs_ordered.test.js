import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import '@ui/static/inputs_ordered.js';

let widgets, submit, host;
beforeEach(() => {
  document.body.innerHTML = '';
  widgets = {};
  submit = {};
  host = {
    register: (name, widget) => (widgets[name] = widget),
    onSubmit: (_root, name, callback) => (submit[name] = callback),
    sendAnswer: vi.fn(),
    fail: vi.fn(),
    hydrate: vi.fn()
  };
  vi.stubGlobal('requestAnimationFrame', (callback) => callback());
  vi.stubGlobal(
    'matchMedia',
    vi.fn(() => ({ matches: true }))
  );
  globalThis.tavlePageParts.inputs(document, { inputs: host });
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function ranking(disabled = false) {
  document.body.innerHTML = `<div><p class="ranking-live"></p><ol class="ranking-list">${['A', 'B', 'C'].map((label) => `<li class="ranking-row" data-label="${label}" data-id="${label.toLowerCase()}"><button class="ranking-move" data-dir="-1" ${disabled ? 'disabled' : ''}>up</button><button class="ranking-move" data-dir="1">down</button></li>`).join('')}</ol></div>`;
  const root = document.body.firstElementChild;
  widgets.ranking.hydrate(root);
  return root;
}
function order(root) {
  return [...root.querySelector('.ranking-list').children].map((row) => row.dataset.label);
}
function drag(row, type) {
  const event = new Event(type, { bubbles: true, cancelable: true });
  Object.defineProperty(event, 'dataTransfer', { value: { setData: vi.fn() } });
  row.dispatchEvent(event);
  return event;
}
function slider(props = { min: 0, max: 1, step: 0.1 }) {
  document.body.innerHTML =
    '<div><input class="slider-input" type="range" min="0" max="2" step="any" value="0.5" aria-valuetext="unchosen"><span class="slider-value"></span></div>';
  const root = document.body.firstElementChild;
  widgets.slider.hydrate(root, props);
  return root;
}

describe('ordered inputs', () => {
  it('reports a missing runtime on both widgets', () => {
    document.body.innerHTML = '<p class="ranking-error"></p><p class="slider-error"></p>';
    const error = vi.spyOn(console, 'error').mockImplementation(() => {});
    globalThis.tavlePageParts.inputs(document, {});
    expect(error).toHaveBeenCalled();
    expect([...document.querySelectorAll('p')].every((p) => p.textContent.includes('could not start'))).toBe(true);
  });
  it('moves with buttons, retains focus, announces boundaries and submits ids', () => {
    const root = ranking();
    const first = root.querySelector('.ranking-row');
    const [up, down] = first.querySelectorAll('button');
    up.click();
    expect(root.querySelector('.ranking-live').textContent).toBe('A is at position 1 of 3. Already first.');
    down.click();
    expect(order(root)).toEqual(['B', 'A', 'C']);
    expect(document.activeElement).toBe(down);
    expect(root.querySelector('.ranking-live').textContent).toBe('A is at position 2 of 3.');
    down.click();
    down.click();
    expect(root.querySelector('.ranking-live').textContent).toBe('A is at position 3 of 3. Already last.');
    submit.ranking();
    expect(host.sendAnswer).toHaveBeenCalledWith(root, 'ranking', ['b', 'c', 'a'], '');
  });
  it('does not enable movement when a button is disabled', () => {
    const root = ranking(true);
    root.querySelector('[data-dir="1"]').click();
    expect(order(root)).toEqual(['A', 'B', 'C']);
    expect(root.querySelector('.ranking-row').draggable).toBe(false);
  });
  it('enables drag only for fine pointers and reorders in both directions', () => {
    const root = ranking();
    const [a, b, c] = root.querySelectorAll('.ranking-row');
    expect(window.matchMedia).toHaveBeenCalledWith('(pointer: fine)');
    expect(a.draggable).toBe(true);
    drag(a, 'dragstart');
    drag(c, 'dragover');
    expect(c.classList.contains('over-after')).toBe(true);
    drag(c, 'drop');
    drag(a, 'dragend');
    expect(order(root)).toEqual(['B', 'C', 'A']);
    expect(a.classList.contains('dragging')).toBe(false);
    expect(c.classList.contains('over')).toBe(false);
    drag(a, 'dragstart');
    drag(b, 'dragover');
    expect(b.classList.contains('over-before')).toBe(true);
    drag(b, 'drop');
    drag(a, 'dragend');
    expect(order(root)).toEqual(['A', 'B', 'C']);
    b.querySelector('button').disabled = true;
    expect(drag(a, 'dragstart').defaultPrevented).toBe(true);
    window.matchMedia.mockReturnValue({ matches: false });
    expect(ranking().querySelector('.ranking-row').draggable).toBe(false);
  });
  it('updates the slider and validates before sending', () => {
    const root = slider();
    const input = root.querySelector('input');
    expect(input.style.getPropertyValue('--vd-fill')).toBe('0.5');
    submit.slider();
    expect(host.fail).toHaveBeenLastCalledWith(root, 'slider', 'Move the slider to choose a value.', input);
    input.value = '0.3';
    input.dispatchEvent(new Event('input'));
    expect(root.querySelector('.slider-value').textContent).toBe('0.3');
    expect(input.hasAttribute('aria-valuetext')).toBe(false);
    expect(input.style.getPropertyValue('--vd-fill')).toBe('0.3');
    submit.slider();
    expect(host.sendAnswer).toHaveBeenCalledWith(root, 'slider', 0.3, '');
    input.value = '0.35';
    input.dispatchEvent(new Event('input'));
    submit.slider();
    expect(host.fail).toHaveBeenLastCalledWith(root, 'slider', 'Choose a value on the scale.', input);
    const incomplete = slider({ min: 0, max: 1 });
    submit.slider();
    expect(host.fail).toHaveBeenLastCalledWith(
      incomplete,
      'slider',
      'Slider is incomplete.',
      incomplete.querySelector('input')
    );
  });
  it('mounts only when loaded by a script element', async () => {
    const mount = vi.fn();
    globalThis.tavlePageParts.mountDocument = mount;
    const descriptor = Object.getOwnPropertyDescriptor(document, 'currentScript');
    try {
      Object.defineProperty(document, 'currentScript', { configurable: true, value: null });
      vi.resetModules();
      await import('@ui/static/inputs_ordered.js');
      expect(mount).not.toHaveBeenCalled();
      Object.defineProperty(document, 'currentScript', { configurable: true, value: document.createElement('script') });
      vi.resetModules();
      await import('@ui/static/inputs_ordered.js');
      expect(mount).toHaveBeenCalledOnce();
    } finally {
      if (descriptor) Object.defineProperty(document, 'currentScript', descriptor);
      else delete document.currentScript;
    }
  });
});
