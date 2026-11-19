// Each code and diff block's component DOM equals the DOM of the former Python renderer,
// recorded in fixtures/<block>.json (props the server sends and the HTML it produced).
import { JSDOM } from 'jsdom';
import { canonical, fragment } from './canonical.js';
import { loadComponents } from './registry.js';
import code from './fixtures/code.json';
import annotated from './fixtures/annotated-code.json';
import diff from './fixtures/diff.json';
import fileTree from './fixtures/file-tree.json';
import changeSummary from './fixtures/change-summary.json';
import deps from './fixtures/deps.json';
import exported from './fixtures/export-callout.html?raw';

const blocks = { code, 'annotated-code': annotated, diff, 'file-tree': fileTree, 'change-summary': changeSummary, deps };
const { m, components } = loadComponents();

for (const [block, cases] of Object.entries(blocks)) {
  describe(`${block} block`, () => {
    it.each(cases.map((c) => [c.name, c]))('component DOM equals the Python DOM: %s', (_name, c) => {
      const host = document.createElement('div');
      m.render(host, components[block].view(m, c.props, components, undefined));
      expect(canonical(host)).toBe(canonical(fragment(c.html)));
    });
  });
}

// The cases test_export_standalone.py puts into the standalone export.
const exportedCases = { code: 'marks', 'annotated-code': 'range-and-kinds', diff: 'split-fold-notes', 'file-tree': 'links', 'change-summary': 'titled', deps: 'chain' };

describe('standalone export', () => {
  it('mounts each code and diff block with no network', async () => {
    const dom = new JSDOM(exported, { runScripts: 'dangerously' });
    await new Promise((resolve) => dom.window.addEventListener('load', resolve));
    const doc = dom.window.document;
    for (const [block, name] of Object.entries(exportedCases)) {
      const host = doc.querySelector(`[data-mithril="${block}"]`);
      expect(host.dataset.mounted).toBe('1');
      const wanted = blocks[block].find((c) => c.name === name).html;
      const inner = document.createElement('div');
      inner.append(...host.cloneNode(true).childNodes);
      expect(canonical(inner)).toBe(canonical(fragment(wanted)));
    }
    expect(doc.querySelectorAll('script[src], link')).toHaveLength(0);
    // the one image the export holds is inline, not fetched
    expect([...doc.querySelectorAll('img')].filter((img) => !img.src.startsWith('data:'))).toHaveLength(0);
  });
});
