// Pilot: the callout component's DOM equals the Python renderer's DOM, and a
// standalone export renders with scripts as its only code and no network.
import { JSDOM } from 'jsdom';
import { canonical, fragment } from './canonical.js';
import { loadComponents } from './registry.js';
import cases from './fixtures/callout.json';
import exported from './fixtures/export-callout.html?raw';
import { mountComponents } from '@varde/pages-static/components/mount.js';

describe('callout pilot', () => {
  const { m, components } = loadComponents();

  it.each(cases.map((c) => [c.name, c]))('component DOM equals the Python DOM: %s', (_name, c) => {
    const host = document.createElement('div');
    m.render(host, components.callout.view(m, c.props, components));
    expect(canonical(host)).toBe(canonical(fragment(c.html)));
  });

  it('mounts every host from props and clears the props script and fallback', () => {
    const root = fragment(
      '<div data-mithril="callout"><script type="application/json">' +
        '{"tone":"risk","text":"a `b`"}</script><noscript><pre>fb</pre></noscript></div>'
    );
    expect(mountComponents(root, m, components)).toBe(1);
    expect(root.querySelector('aside.vd-callout-risk code').textContent).toBe('b');
    expect(root.querySelector('script, noscript')).toBeNull();
    expect(mountComponents(root, m, components)).toBe(0);
  });

  it('a standalone export mounts all callouts with no network', async () => {
    const dom = new JSDOM(exported, { runScripts: 'dangerously' });
    await new Promise((resolve) => dom.window.addEventListener('load', resolve));
    const doc = dom.window.document;
    const asides = [...doc.querySelectorAll('main > [data-mithril="callout"] > aside.vd-callout')];
    expect(asides).toHaveLength(cases.length);
    const wanted = cases.map((c) => canonical(fragment(c.html).firstChild));
    expect(asides.map(canonical)).toEqual(wanted);
    expect(doc.querySelectorAll('script[src], link')).toHaveLength(0);
    // the one image the export holds is inline, not fetched
    expect([...doc.querySelectorAll('img')].filter((img) => !img.src.startsWith('data:'))).toHaveLength(0);
  });
});
