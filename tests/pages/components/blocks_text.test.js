// Each text block's component DOM equals the DOM of the former Python renderer,
// recorded in fixtures/<block>.json (props and the HTML it produced).
import { canonical, fragment } from './canonical.js';
import { loadComponents } from './registry.js';
import urls from './fixtures/classify-url.json';
import stats from './fixtures/stats.json';
import timeline from './fixtures/timeline.json';
import checklist from './fixtures/checklist.json';
import risks from './fixtures/risks.json';
import table from './fixtures/table.json';
import matrix from './fixtures/matrix.json';
import decision from './fixtures/decision.json';
import recap from './fixtures/recap.json';

const blocks = { stats, timeline, checklist, risks, table, matrix, decision, recap };
const { m, components } = loadComponents();

for (const [block, cases] of Object.entries(blocks)) {
  describe(`${block} block`, () => {
    it.each(cases.map((c) => [c.name, c]))('component DOM equals the Python DOM: %s', (_name, c) => {
      const host = document.createElement('div');
      m.render(host, components[block].view(m, c.props, components, c.id ?? undefined));
      expect(canonical(host)).toBe(canonical(fragment(c.html)));
    });
  });
}

describe('shared number formatting', () => {
  const { formatNumber } = components.shared;
  it.each([
    [1234567, undefined, '1,234,567'],
    [1234.5, undefined, '1,234.5'],
    [-9876543, undefined, '-9,876,543'],
    [1234567.891, 1, '1,234,567.9'],
    [2.5, 0, '2'],
    [3.5, 0, '4'],
    [0.5, 0, '0'],
    [0.125, 2, '0.12'],
    [2.675, 2, '2.67'],
    [999, 2, '999.00'],
    [-0.4, 0, '-0'],
    [1000, 6, '1,000.000000']
  ])('formats %s with %s places as Python does', (value, places, expected) => {
    expect(formatNumber(value, places)).toBe(expected);
  });
});

describe('table url classes', () => {
  it.each(urls.map((u) => [JSON.stringify(u.url), u]))('classifies %s as Python does', (_name, u) => {
    expect(components.table.classifyUrl(u.url)).toBe(u.kind);
  });
});
