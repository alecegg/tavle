// Chart enhancer: legend toggles and the data table on print.
import { enhanceChart } from '@ui/static/chart.js';
import { fragment } from './canonical.js';
import chart from './fixtures/chart.json';

function mount(name) {
  const block = fragment(chart.find((c) => c.name === name).html).firstElementChild;
  document.body.append(block);
  const svg = block.querySelector('svg.vb-chart');
  Object.defineProperty(svg, 'viewBox', { configurable: true, value: { baseVal: { width: 360, height: 220 } } });
  return block;
}

const readout = (block) => block.querySelector('.vb-readout').textContent;
const toggleFor = (block, series) =>
  block.querySelector(`.vb-legend li[data-series="${series}"] button.vb-series-toggle`);
const hover = (node) => node.dispatchEvent(new Event('pointerover', { bubbles: true }));

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

describe('legend toggles', () => {
  it('starts pressed and hides its series outside the legend', () => {
    const block = mount('rich-chart:c-bar');
    enhanceChart(block);
    const button = toggleFor(block, 1);
    expect(button.getAttribute('aria-pressed')).toBe('true');
    button.click();
    expect(button.getAttribute('aria-pressed')).toBe('false');
    for (const mark of block.querySelectorAll('.vb-mark[data-series="1"]')) {
      expect(mark.classList.contains('vb-off')).toBe(true);
    }
    expect(block.querySelector('.vb-mark[data-series="0"]').classList.contains('vb-off')).toBe(false);
    expect(block.querySelector('.vb-legend li[data-series="1"]').classList.contains('vb-off')).toBe(false);
  });

  it('turns the series back on when pressed again', () => {
    const block = mount('rich-chart:c-bar');
    enhanceChart(block);
    const button = toggleFor(block, 1);
    button.click();
    button.click();
    expect(button.getAttribute('aria-pressed')).toBe('true');
    expect(block.querySelector('.vb-mark[data-series="1"]').classList.contains('vb-off')).toBe(false);
  });

  it('drops a hidden series from the readout of the shown column', () => {
    const block = mount('rich-chart:c-bar');
    enhanceChart(block);
    hover(block.querySelector('rect.vb-col[data-index="0"]'));
    expect(readout(block)).toBe('before: p50: 120 ms; p95: 400 ms');
    toggleFor(block, 1).click();
    expect(readout(block)).toBe('before: p50: 120 ms');
  });

  it('says no series is shown when every series is hidden', () => {
    const block = mount('rich-chart:c-bar');
    enhanceChart(block);
    hover(block.querySelector('rect.vb-col[data-index="0"]'));
    toggleFor(block, 0).click();
    toggleFor(block, 1).click();
    expect(readout(block)).toContain('No series shown.');
  });

  it('redraws the shown point on the same index after its series is hidden', () => {
    const block = mount('rich-chart:c-scatter');
    enhanceChart(block);
    hover(block.querySelector('g.vb-mark[data-series="0"][data-index="2"]'));
    expect(readout(block)).toBe('small / x 3 / 1.1 s');
    toggleFor(block, 0).click();
    expect(readout(block)).toBe('large / x 6 / 4.4 s');
    expect(block.querySelector('.vb-mark.vb-on').dataset.series).toBe('1');
  });
});

describe('data table on print', () => {
  const printEvent = (type) => window.dispatchEvent(new Event(type));

  it('opens a closed data table for print and closes it after', () => {
    const block = mount('rich-chart:c-bar');
    enhanceChart(block);
    const data = block.querySelector('details.vb-data');
    expect(data.open).toBe(false);
    printEvent('beforeprint');
    expect(data.open).toBe(true);
    printEvent('afterprint');
    expect(data.open).toBe(false);
  });

  it('leaves a table that was already open open after print', () => {
    const block = mount('rich-chart:c-bar');
    enhanceChart(block);
    const closed = block.querySelector('details.vb-data');
    const open = document.createElement('details');
    open.className = 'vb-data';
    open.open = true;
    block.append(open);
    printEvent('beforeprint');
    printEvent('afterprint');
    expect(open.open).toBe(true);
    expect(closed.open).toBe(false);
  });
});
