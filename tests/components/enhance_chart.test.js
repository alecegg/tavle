// Chart enhancer: readout, tooltip, pointer and keyboard reading over the server SVG.
import { enhanceChart } from '@ui/static/chart.js';
import { fragment } from './canonical.js';
import chart from './fixtures/chart.json';

const START = 'Hover, focus or tap a point.';
const TIP_TEXT = { x: 0, y: 0, width: 100, height: 40 };

function mount(name) {
  const block = fragment(chart.find((c) => c.name === name).html).firstElementChild;
  document.body.append(block);
  const svg = block.querySelector('svg.vb-chart');
  Object.defineProperty(svg, 'viewBox', { configurable: true, value: { baseVal: { width: 360, height: 220 } } });
  return block;
}

// jsdom has no text layout: every label measures TIP_TEXT; a test gives one mark its own box with boxAt.
function stubTextBox() {
  Object.defineProperty(SVGElement.prototype, 'getBBox', { configurable: true, value: () => TIP_TEXT });
}

function boxAt(node, box) {
  Object.defineProperty(node, 'getBBox', { configurable: true, value: () => box });
}

const readout = (block) => block.querySelector('.vb-readout').textContent;
const tipRows = (block) => Array.from(block.querySelectorAll('g.vb-tip .vb-tip-text tspan'), (row) => row.textContent);
const tipTransform = (block) => block.querySelector('g.vb-tip')?.getAttribute('transform');
const litMarks = (block) =>
  Array.from(block.querySelectorAll('.vb-mark.vb-on'), (mark) => `${mark.dataset.series}-${mark.dataset.index}`);
const at = (block, selector) => block.querySelector(selector);

function fire(node, type, init = {}) {
  node.dispatchEvent(new Event(type, { bubbles: true, ...init }));
}

function press(node, key) {
  const event = new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true });
  node.dispatchEvent(event);
  return event;
}

beforeEach(stubTextBox);

afterEach(() => {
  document.body.replaceChildren();
  delete SVGElement.prototype.getBBox;
  vi.restoreAllMocks();
});

describe('enhanceChart on a block without its parts', () => {
  it.each([
    ['no svg.vb-chart', '<div class="vb chart"><div class="vb-plot"></div></div>'],
    ['no .vb-plot', '<div class="vb chart"><svg class="vb-chart"></svg></div>']
  ])('does nothing with %s', (_label, html) => {
    const block = fragment(html).firstElementChild;
    document.body.append(block);
    enhanceChart(block);
    expect(block.querySelector('.vb-readout')).toBeNull();
  });
});

describe('readout and plot region', () => {
  it('adds a polite readout after the plot with the start text', () => {
    const block = mount('rich-chart:c-bar');
    enhanceChart(block);
    const out = at(block, '.vb-readout');
    expect(out.textContent).toBe(START);
    expect(out.getAttribute('aria-live')).toBe('polite');
    expect(at(block, '.vb-plot').nextElementSibling).toBe(out);
  });

  it('makes the plot a focusable region named after the chart', () => {
    const block = mount('rich-chart:c-bar');
    enhanceChart(block);
    const plot = at(block, '.vb-plot');
    expect(plot.getAttribute('role')).toBe('region');
    expect(plot.getAttribute('tabindex')).toBe('0');
    expect(plot.getAttribute('aria-label')).toBe('Latency by build (arrow keys read values)');
  });
});

describe('pointer and click readouts', () => {
  it('reads a column as label, then series and value, and lights its marks', () => {
    const block = mount('rich-chart:c-bar');
    enhanceChart(block);
    fire(at(block, 'rect.vb-col[data-index="0"]'), 'pointerover');
    expect(readout(block)).toBe('before: p50: 120 ms; p95: 400 ms');
    expect(litMarks(block)).toEqual(['0-0', '1-0']);
  });

  it('reads the column of a bar hit under the pointer', () => {
    const block = mount('rich-chart:c-bar');
    enhanceChart(block);
    fire(at(block, 'rect.vb-bar[data-series="0"][data-index="2"]'), 'pointerover');
    expect(readout(block)).toBe('index: p50: 88 ms; p95: 260 ms');
  });

  it('reads a column on click too', () => {
    const block = mount('rich-chart:c-bar');
    enhanceChart(block);
    at(block, 'rect.vb-col[data-index="1"]').dispatchEvent(new MouseEvent('click', { bubbles: true }));
    expect(readout(block)).toBe('cache: p50: 95 ms; p95: 310 ms');
  });

  it('reads a point as series, label and value', () => {
    const block = mount('rich-chart:c-scatter');
    enhanceChart(block);
    fire(at(block, 'g.vb-mark[data-series="0"][data-index="2"]'), 'pointerover');
    expect(readout(block)).toBe('small / x 3 / 1.1 s');
    expect(litMarks(block)).toEqual(['0-2']);
  });

  it('clips tooltip lines to 28 characters but not the readout', () => {
    const block = mount('rich-chart:c-scatter');
    enhanceChart(block);
    const mark = at(block, 'g.vb-mark[data-series="0"][data-index="0"]');
    mark.setAttribute('aria-label', 'a very long series name that goes past the limit / x 1 / 0.4 s');
    fire(mark, 'pointerover');
    expect(tipRows(block)[0]).toBe('a very long series name tha…');
    expect(readout(block)).toBe('a very long series name that goes past the limit / x 1 / 0.4 s');
  });
});

describe('tooltip placement', () => {
  it('sits beside a point when there is room on the right', () => {
    const block = mount('rich-chart:c-scatter');
    enhanceChart(block);
    const mark = at(block, 'g.vb-mark[data-series="0"][data-index="0"]');
    boxAt(mark, { x: 50, y: 5, width: 20, height: 20 });
    fire(mark, 'pointerover');
    expect(tipTransform(block)).toBe('translate(80.0 33.0)');
  });

  it('flips left without room on the right', () => {
    const block = mount('rich-chart:c-scatter');
    enhanceChart(block);
    const mark = at(block, 'g.vb-mark[data-series="1"][data-index="3"]');
    boxAt(mark, { x: 300, y: 100, width: 20, height: 20 });
    fire(mark, 'pointerover');
    expect(tipTransform(block)).toBe('translate(174.0 36.0)');
  });

  it('drops below a point without room above', () => {
    const block = mount('rich-chart:c-scatter');
    enhanceChart(block);
    const mark = at(block, 'g.vb-mark[data-series="0"][data-index="0"]');
    boxAt(mark, { x: 50, y: 5, width: 20, height: 20 });
    fire(mark, 'pointerover');
    expect(tipTransform(block)).toBe('translate(80.0 33.0)');
  });
});

describe('keyboard reading', () => {
  const columnLabels = ['before', 'cache', 'index', 'after'];

  it('moves one column per arrow and clamps at both ends', () => {
    const block = mount('rich-chart:c-bar');
    enhanceChart(block);
    const plot = at(block, '.vb-plot');
    press(plot, 'ArrowRight');
    expect(readout(block).startsWith('before:')).toBe(true);
    press(plot, 'ArrowRight');
    expect(readout(block).startsWith('cache:')).toBe(true);
    press(plot, 'ArrowLeft');
    press(plot, 'ArrowLeft');
    expect(readout(block).startsWith('before:')).toBe(true);
  });

  it('Home and End jump to the first and last column', () => {
    const block = mount('rich-chart:c-bar');
    enhanceChart(block);
    const plot = at(block, '.vb-plot');
    press(plot, 'End');
    expect(readout(block).startsWith(`${columnLabels[3]}:`)).toBe(true);
    press(plot, 'Home');
    expect(readout(block).startsWith(`${columnLabels[0]}:`)).toBe(true);
  });

  it('prevents handled keys and leaves other keys alone', () => {
    const block = mount('rich-chart:c-bar');
    enhanceChart(block);
    const plot = at(block, '.vb-plot');
    expect(press(plot, 'ArrowRight').defaultPrevented).toBe(true);
    expect(press(plot, 'x').defaultPrevented).toBe(false);
  });

  it('Escape resets the readout and unlights the marks', () => {
    const block = mount('rich-chart:c-bar');
    enhanceChart(block);
    const plot = at(block, '.vb-plot');
    press(plot, 'ArrowRight');
    press(plot, 'Escape');
    expect(readout(block)).toBe(START);
    expect(litMarks(block)).toEqual([]);
  });
});

describe('leaving the chart', () => {
  it('a mouse leave unlights the marks and removes the tooltip', () => {
    const block = mount('rich-chart:c-bar');
    enhanceChart(block);
    fire(at(block, 'rect.vb-col[data-index="0"]'), 'pointerover');
    const svg = at(block, 'svg.vb-chart');
    svg.dispatchEvent(Object.assign(new Event('pointerleave'), { pointerType: 'mouse' }));
    expect(litMarks(block)).toEqual([]);
    expect(at(block, 'g.vb-tip')).toBeNull();
  });

  it('a touch leave keeps the marks lit', () => {
    const block = mount('rich-chart:c-bar');
    enhanceChart(block);
    fire(at(block, 'rect.vb-col[data-index="0"]'), 'pointerover');
    const svg = at(block, 'svg.vb-chart');
    svg.dispatchEvent(Object.assign(new Event('pointerleave'), { pointerType: 'touch' }));
    expect(litMarks(block)).toEqual(['0-0', '1-0']);
  });
});
