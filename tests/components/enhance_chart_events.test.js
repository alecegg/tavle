// Chart enhancer: Events list items as buttons, and the event shapes in the SVG.
import { enhanceChart } from '@ui/static/chart.js';
import { fragment } from './canonical.js';
import chart from './fixtures/chart.json';

const START = 'Hover, focus or tap a point.';

function mount(name) {
  const block = fragment(chart.find((c) => c.name === name).html).firstElementChild;
  document.body.append(block);
  const svg = block.querySelector('svg.vb-chart');
  Object.defineProperty(svg, 'viewBox', { configurable: true, value: { baseVal: { width: 360, height: 220 } } });
  return block;
}

const readout = (block) => block.querySelector('.vb-readout').textContent;
const eventItem = (block, n) => block.querySelector(`li[data-event="${n}"]`);
const eventButton = (block, n) => eventItem(block, n).querySelector('button.vb-ev-btn');
const shapes = (block, n) => Array.from(block.querySelectorAll(`svg.vb-chart [data-event="${n}"]`));
const litShapes = (block, n) => shapes(block, n).filter((node) => node.classList.contains('vb-on'));
const keydown = (node, key) => node.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true }));

// jsdom has no text layout: tooltip labels measure a fixed box.
beforeEach(() => {
  Object.defineProperty(SVGElement.prototype, 'getBBox', {
    configurable: true,
    value: () => ({ x: 0, y: 0, width: 100, height: 40 })
  });
});

afterEach(() => {
  document.body.replaceChildren();
  delete SVGElement.prototype.getBBox;
  vi.restoreAllMocks();
});

describe('event items', () => {
  it('wraps each item in a button and keeps its tone and kind', () => {
    const block = mount('rich-chart-events:ce-scatter');
    enhanceChart(block);
    const button = eventButton(block, 1);
    expect(button.type).toBe('button');
    expect(button.textContent).toContain('slow window');
  });

  it('focus shows the event, lights its item and its shapes', () => {
    const block = mount('rich-chart-events:ce-scatter');
    enhanceChart(block);
    eventButton(block, 1).dispatchEvent(new Event('focus'));
    expect(readout(block)).toBe('Event 1 / slow window / band, 3 to 5, warning');
    expect(eventItem(block, 1).classList.contains('vb-on')).toBe(true);
    expect(litShapes(block, 1).length).toBe(shapes(block, 1).length);
    expect(shapes(block, 1).length).toBeGreaterThan(0);
  });

  it('blur unlights the item and its shapes', () => {
    const block = mount('rich-chart-events:ce-scatter');
    enhanceChart(block);
    const button = eventButton(block, 1);
    button.dispatchEvent(new Event('focus'));
    button.dispatchEvent(new Event('blur'));
    expect(eventItem(block, 1).classList.contains('vb-on')).toBe(false);
    expect(litShapes(block, 1)).toEqual([]);
  });

  it('hover and click show the event', () => {
    const block = mount('rich-chart-events:ce-scatter');
    enhanceChart(block);
    eventButton(block, 2).dispatchEvent(new Event('pointerenter'));
    expect(readout(block)).toBe('Event 2 / cache / marker, at 7, success');
    eventButton(block, 1).click();
    expect(readout(block)).toBe('Event 1 / slow window / band, 3 to 5, warning');
  });

  it('a mouse leave keeps a focused event and clears an unfocused one', () => {
    const block = mount('rich-chart-events:ce-scatter');
    enhanceChart(block);
    const button = eventButton(block, 1);
    button.focus();
    button.dispatchEvent(Object.assign(new Event('pointerleave'), { pointerType: 'mouse' }));
    expect(litShapes(block, 1).length).toBeGreaterThan(0);
    button.blur();
    button.dispatchEvent(new Event('pointerenter'));
    button.dispatchEvent(Object.assign(new Event('pointerleave'), { pointerType: 'mouse' }));
    expect(litShapes(block, 1)).toEqual([]);
  });

  it('Escape on an item clears the readout', () => {
    const block = mount('rich-chart-events:ce-scatter');
    enhanceChart(block);
    const button = eventButton(block, 1);
    button.dispatchEvent(new Event('pointerenter'));
    keydown(button, 'Escape');
    expect(readout(block)).toBe(START);
    expect(litShapes(block, 1)).toEqual([]);
  });
});

describe('event shapes in the SVG', () => {
  it('pointing at an event shape shows its item', () => {
    const block = mount('rich-chart-events:ce-scatter');
    enhanceChart(block);
    shapes(block, 2)[0].dispatchEvent(new Event('pointerover', { bubbles: true }));
    expect(readout(block)).toBe('Event 2 / cache / marker, at 7, success');
  });
});
