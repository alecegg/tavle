import { enhanceEr } from '@ui/static/er.js';
import { enhanceSequence } from '@ui/static/sequence.js';
import models from './fixtures/data-model.json';
import sequences from './fixtures/sequence.json';

function fixture(cases, name) {
  document.body.innerHTML = cases.find((item) => item.name === name).html;
  return document.body.firstElementChild;
}
function key(node, value) {
  const event = new KeyboardEvent('keydown', { key: value, bubbles: true, cancelable: true });
  node.dispatchEvent(event);
  return event;
}
afterEach(() => document.body.replaceChildren());

describe('entity highlighting', () => {
  it('ignores other blocks and SVG focus, but highlights related nodes on pointer and card focus', () => {
    const block = fixture(models, 'graph-basic');
    const card = block.querySelector('.vd-er-card');
    const svg = block.querySelector('svg [data-entity]');
    const other = block.querySelector('[data-entity="1"]');
    const edge = block.querySelector('[data-ends]');
    block.classList.remove('vd-er');
    enhanceEr(block);
    card.dispatchEvent(new Event('pointerenter'));
    expect(block.classList.contains('vd-er-active')).toBe(false);
    block.classList.add('vd-er');
    enhanceEr(block);
    svg.dispatchEvent(new FocusEvent('focusin', { bubbles: true }));
    expect(block.classList.contains('vd-er-active')).toBe(false);
    svg.dispatchEvent(new Event('pointerenter'));
    expect(block.classList.contains('vd-er-active')).toBe(true);
    expect(card.classList.contains('vd-er-on')).toBe(true);
    expect(other.classList.contains('vd-er-near')).toBe(true);
    expect(edge.classList.contains('vd-er-hot')).toBe(true);
    svg.dispatchEvent(new Event('pointerleave'));
    expect(block.querySelector('.vd-er-hot')).toBeNull();
    const link = card.querySelector('a');
    link.dispatchEvent(new FocusEvent('focusin', { bubbles: true }));
    expect(card.classList.contains('vd-er-on')).toBe(true);
    link.dispatchEvent(new FocusEvent('focusout', { bubbles: true, relatedTarget: card.querySelector('table') }));
    expect(block.classList.contains('vd-er-active')).toBe(true);
    link.dispatchEvent(new FocusEvent('focusout', { bubbles: true, relatedTarget: document.body }));
    expect(block.classList.contains('vd-er-active')).toBe(false);
  });
});

describe('sequence highlighting', () => {
  it('requires the class and items', () => {
    const block = fixture(sequences, 'rich-sequence:s1');
    block.classList.remove('vd-sequence');
    enhanceSequence(block);
    expect(block.querySelector('.vd-sequence-readout')).toBeNull();
    block.classList.add('vd-sequence');
    block.querySelectorAll('li[data-step]').forEach((item) => item.remove());
    enhanceSequence(block);
    expect(block.querySelector('.vd-sequence-readout')).toBeNull();
  });

  it('links drawing and list, navigates without wrapping, and clears highlights', () => {
    const block = fixture(sequences, 'rich-sequence:s1');
    enhanceSequence(block);
    const items = [...block.querySelectorAll('li[data-step]')];
    const readout = block.querySelector('.vd-sequence-readout');
    const row = block.querySelector('.vd-sequence-row[data-step="0"]');
    expect(readout.nextElementSibling).toBe(block.querySelector('.vd-sequence-steps'));
    expect(items.map((item) => item.tabIndex)).toEqual([0, ...items.slice(1).map(() => -1)]);
    row.dispatchEvent(new Event('pointerenter'));
    expect(readout.textContent).toBe(`Step 1 of ${items.length}: ${items[0].textContent}`);
    expect(
      [...block.querySelectorAll('[data-step="0"]')].every((node) => node.classList.contains('vd-sequence-on'))
    ).toBe(true);
    row.dispatchEvent(new Event('pointerleave'));
    expect(readout.textContent).toBe('');
    items[0].focus();
    expect(key(items[0], 'ArrowUp').defaultPrevented).toBe(true);
    expect(document.activeElement).toBe(items[0]);
    key(items[0], 'ArrowRight');
    expect(document.activeElement).toBe(items[1]);
    expect(items[1].tabIndex).toBe(0);
    expect(items[0].tabIndex).toBe(-1);
    key(items[1], 'End');
    expect(document.activeElement).toBe(items.at(-1));
    key(items.at(-1), 'ArrowDown');
    expect(document.activeElement).toBe(items.at(-1));
    key(items.at(-1), 'Home');
    key(items[0], 'ArrowLeft');
    expect(document.activeElement).toBe(items[0]);
    expect(key(block, 'End').defaultPrevented).toBe(false);
    expect(key(items[0], 'x').defaultPrevented).toBe(false);
    key(items[0], 'Escape');
    expect(readout.textContent).toBe('');
    items[1].focus();
    items[1].blur();
    expect(readout.textContent).toBe('');
  });
});
