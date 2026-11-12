// Sample component test: plain ES-module component mounts and redraws under jsdom.
import { loadMithril } from './load-mithril.js';

const m = loadMithril();

const Counter = {
  count: 0,
  view: () => m('button.count', { onclick: () => { Counter.count += 1; } }, `n=${Counter.count}`)
};

describe('mithril under jsdom', () => {
  it('mounts a component and redraws after a state change', () => {
    const root = document.createElement('div');
    m.mount(root, Counter);
    expect(root.querySelector('button.count').textContent).toBe('n=0');
    root.querySelector('button.count').click();
    m.redraw.sync();
    expect(root.querySelector('button.count').textContent).toBe('n=1');
  });
});

describe('read-only pages', () => {
  const host = '<div data-mithril="decision"><script type="application/json">{"question":"Q"}</script></div>';

  it('disables every control of a block mounted marked [data-readonly]', async () => {
    const { loadComponents } = await import('./registry.js');
    const { mountComponents } = await import('@varde/pages-static/components/mount.js');
    const { m, components } = loadComponents();
    const readonly = document.createElement('main');
    readonly.innerHTML = host.replace('<div ', '<div data-readonly ');
    const open = document.createElement('main');
    open.innerHTML = host;
    mountComponents(readonly, m, components);
    mountComponents(open, m, components);
    const disabled = (root) => [...root.querySelectorAll('button, textarea')].map((c) => c.disabled);
    expect(disabled(readonly).length).toBeGreaterThan(0);
    expect(disabled(readonly).every(Boolean)).toBe(true);
    expect(disabled(open).some(Boolean)).toBe(false);
  });
});
