// Code, annotated code and image enhancers: copy button, note highlight, print folds, zoom dialog.
import { enhanceCode } from '@ui/static/code.js';
import { enhanceAnnotated } from '@ui/static/annotated.js';
import { enhanceImage } from '@ui/static/image.js';
import { fragment } from './canonical.js';
import code from './fixtures/code.json';
import annotated from './fixtures/annotated-code.json';
import image from './fixtures/image.json';

const fixtureBlock = (list, name) => {
  const block = fragment(list.find((c) => c.name === name).html).firstElementChild;
  document.body.append(block);
  return block;
};

const flush = async () => {
  for (let i = 0; i < 5; i += 1) await Promise.resolve();
};

function setOwn(target, name, value) {
  Object.defineProperty(target, name, { configurable: true, writable: true, value });
}

function click(node, init = {}) {
  const event = new MouseEvent('click', { bubbles: true, cancelable: true, button: 0, ...init });
  node.dispatchEvent(event);
  return event;
}

const fire = (node, type) => node.dispatchEvent(new Event(type));
const copyButton = (block) => block.querySelector('.vd-code-copy');
const status = (block) => block.querySelector('.vd-code-status').textContent;
const activeLines = (block) => Array.from(block.querySelectorAll('[data-active]'), (line) => line.dataset.line);

afterEach(() => {
  document.body.replaceChildren();
  delete navigator.clipboard;
  delete document.execCommand;
  vi.useRealTimers();
  vi.unstubAllGlobals();
  if (HTMLDialogElement) {
    delete HTMLDialogElement.prototype.showModal;
    delete HTMLDialogElement.prototype.close;
  }
  vi.restoreAllMocks();
});

describe('enhanceCode', () => {
  it('does nothing for a block that is not vd-code or has no head', () => {
    const plain = fragment(
      '<figure class="vb"><figcaption class="vd-code-head"></figcaption></figure>'
    ).firstElementChild;
    const headless = fragment('<figure class="vd-code"></figure>').firstElementChild;
    enhanceCode(plain);
    enhanceCode(headless);
    expect(plain.querySelector('button')).toBeNull();
    expect(headless.querySelector('button')).toBeNull();
  });

  it('adds a Copy button and a polite status in the head', () => {
    const block = fixtureBlock(code, 'python');
    enhanceCode(block);
    const button = copyButton(block);
    expect(button.textContent).toBe('Copy');
    expect(button.getAttribute('aria-label')).toBe('Copy code');
    expect(button.parentElement.className).toBe('vd-code-head');
    const live = block.querySelector('.vd-code-status');
    expect(live.getAttribute('role')).toBe('status');
    expect(live.getAttribute('aria-live')).toBe('polite');
  });

  it('writes the raw source from data-copy, not the line numbers, and confirms', async () => {
    const writeText = vi.fn(() => Promise.resolve());
    setOwn(navigator, 'clipboard', { writeText });
    const block = fixtureBlock(code, 'python');
    enhanceCode(block);
    copyButton(block).click();
    await flush();
    expect(writeText).toHaveBeenCalledWith(code.find((c) => c.name === 'python').props.copy);
    expect(status(block)).toBe('Copied ✓');
  });

  it('falls back to a readonly textarea and execCommand when the clipboard is missing', async () => {
    const copied = [];
    setOwn(
      document,
      'execCommand',
      vi.fn(() => {
        copied.push(document.querySelector('textarea.vd-code-scratch').value);
        return true;
      })
    );
    const block = fixtureBlock(code, 'json');
    enhanceCode(block);
    copyButton(block).click();
    await flush();
    expect(copied).toEqual([block.dataset.copy]);
    expect(document.querySelector('textarea.vd-code-scratch')).toBeNull();
    expect(status(block)).toBe('Copied ✓');
  });

  it('falls back when the clipboard write rejects', async () => {
    setOwn(navigator, 'clipboard', { writeText: vi.fn(() => Promise.reject(new Error('denied'))) });
    setOwn(
      document,
      'execCommand',
      vi.fn(() => true)
    );
    const block = fixtureBlock(code, 'json');
    enhanceCode(block);
    copyButton(block).click();
    await flush();
    expect(document.execCommand).toHaveBeenCalledWith('copy');
    expect(status(block)).toBe('Copied ✓');
  });

  it.each([
    ['execCommand reports false', () => false],
    [
      'execCommand throws',
      () => {
        throw new Error('no');
      }
    ]
  ])('says the copy failed when %s', async (_label, run) => {
    setOwn(document, 'execCommand', vi.fn(run));
    const block = fixtureBlock(code, 'json');
    enhanceCode(block);
    copyButton(block).click();
    await flush();
    expect(status(block)).toBe('Copy failed: select the text instead');
    expect(document.querySelector('textarea.vd-code-scratch')).toBeNull();
  });

  it('clears the message 2500ms after it, and a second click restarts the timer', async () => {
    vi.useFakeTimers();
    setOwn(navigator, 'clipboard', { writeText: vi.fn(() => Promise.resolve()) });
    const block = fixtureBlock(code, 'json');
    enhanceCode(block);
    copyButton(block).click();
    await flush();
    vi.advanceTimersByTime(2000);
    copyButton(block).click();
    await flush();
    vi.advanceTimersByTime(2000);
    expect(status(block)).toBe('Copied ✓');
    vi.advanceTimersByTime(500);
    expect(status(block)).toBe('');
  });
});

describe('enhanceAnnotated', () => {
  it('does nothing for a block that is not vd-annotated-code', () => {
    const block = fragment(
      '<div class="vb"><figure class="vd-code"><figcaption class="vd-code-head"></figcaption></figure></div>'
    ).firstElementChild;
    document.body.append(block);
    enhanceAnnotated(block);
    expect(block.querySelector('.vd-code-copy')).toBeNull();
  });

  it('adds Copy to the code panel', () => {
    const block = fixtureBlock(annotated, 'range-and-kinds');
    enhanceAnnotated(block);
    expect(block.querySelector('.vd-code-head .vd-code-copy')).not.toBeNull();
  });

  it('lights the lines of a note on hover and focus, and clears them on leave and blur', () => {
    const block = fixtureBlock(annotated, 'range-and-kinds');
    enhanceAnnotated(block);
    const note = block.querySelector('#note-d111aff1-1');
    fire(note, 'mouseenter');
    expect(activeLines(block)).toEqual(['5', '6', '7']);
    fire(note, 'mouseleave');
    expect(activeLines(block)).toEqual([]);
    fire(note, 'focus');
    expect(activeLines(block)).toEqual(['5', '6', '7']);
    fire(note, 'blur');
    expect(activeLines(block)).toEqual([]);
  });

  it('lights the note lines from its pin, using the pin number to find the note', () => {
    const block = fixtureBlock(annotated, 'range-and-kinds');
    enhanceAnnotated(block);
    fire(block.querySelector('#pin-d111aff1-2'), 'mouseenter');
    expect(activeLines(block)).toEqual(['20']);
    fire(block.querySelector('#pin-d111aff1-2'), 'mouseleave');
    expect(activeLines(block)).toEqual([]);
  });

  it('moves focus to the target of a pin or back link after the click', () => {
    vi.useFakeTimers();
    const block = fixtureBlock(annotated, 'range-and-kinds');
    enhanceAnnotated(block);
    const note = block.querySelector('#note-d111aff1-1');
    click(block.querySelector('#pin-d111aff1-1'));
    vi.runAllTimers();
    expect(document.activeElement).toBe(note);
    note.blur();
    click(note.querySelector('.vd-annotated-back'));
    vi.runAllTimers();
    expect(document.activeElement).toBe(block.querySelector('#pin-d111aff1-1'));
  });

  it('leaves focus alone for a click that is not on a pin or back link', () => {
    vi.useFakeTimers();
    const block = fixtureBlock(annotated, 'range-and-kinds');
    enhanceAnnotated(block);
    const before = document.activeElement;
    click(block.querySelector('.vd-code-line'));
    vi.runAllTimers();
    expect(document.activeElement).toBe(before);
  });

  it('opens closed folds before print and closes only those after', () => {
    const block = fixtureBlock(annotated, 'range-and-kinds');
    const folds = [...block.querySelectorAll('details.vd-annotated-fold')];
    folds[0].open = true;
    enhanceAnnotated(block);
    window.dispatchEvent(new Event('beforeprint'));
    expect(folds.every((fold) => fold.open)).toBe(true);
    window.dispatchEvent(new Event('afterprint'));
    expect(folds.map((fold) => fold.open)).toEqual([true, false]);
  });
});

describe('enhanceImage', () => {
  const link = (block) => block.querySelector('a.vd-image-link');
  const dialog = () => document.querySelector('dialog.vd-image-dialog');

  beforeEach(() => {
    setOwn(HTMLDialogElement.prototype, 'showModal', vi.fn());
    setOwn(
      HTMLDialogElement.prototype,
      'close',
      vi.fn(function closeDialog() {
        this.dispatchEvent(new Event('close'));
      })
    );
  });

  it('opens the picture in a labelled dialog and prevents the link', () => {
    const block = fixtureBlock(image, 'link');
    enhanceImage(block);
    const event = click(link(block));
    expect(event.defaultPrevented).toBe(true);
    const shown = dialog();
    expect(shown.getAttribute('aria-label')).toBe('A swatch');
    const big = shown.querySelector('img.vd-image-zoomed');
    expect(big.src).toBe(block.querySelector('img').src);
    expect(big.alt).toBe('A swatch');
    expect(HTMLDialogElement.prototype.showModal).toHaveBeenCalledTimes(1);
  });

  it.each([
    ['ctrl', { ctrlKey: true }],
    ['meta', { metaKey: true }],
    ['shift', { shiftKey: true }],
    ['middle button', { button: 1 }]
  ])('lets a %s click through to the link', (_label, init) => {
    const block = fixtureBlock(image, 'link');
    enhanceImage(block);
    link(block).setAttribute('href', '#');
    expect(click(link(block), init).defaultPrevented).toBe(false);
    expect(dialog()).toBeNull();
  });

  it('removes the dialog when Close is pressed', () => {
    const block = fixtureBlock(image, 'link');
    enhanceImage(block);
    click(link(block));
    click(dialog().querySelector('.vd-image-close'));
    expect(HTMLDialogElement.prototype.close).toHaveBeenCalled();
    expect(dialog()).toBeNull();
  });

  it('does nothing without dialog support', () => {
    vi.stubGlobal('HTMLDialogElement', undefined);
    const block = fixtureBlock(image, 'link');
    enhanceImage(block);
    link(block).setAttribute('href', '#');
    expect(click(link(block)).defaultPrevented).toBe(false);
    expect(dialog()).toBeNull();
  });

  it('does nothing for a figure without a linked image', () => {
    const block = fixtureBlock(image, 'export-missing');
    expect(() => enhanceImage(block)).not.toThrow();
    expect(block.querySelector('a')).toBeNull();
  });
});
