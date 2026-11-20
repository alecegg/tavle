// The tabs and columns components' DOM equals the DOM of the former Python renderer after
// `fill_containers`, recorded in fixtures/containers.json. Held blocks are the page's own nodes
// that mount lifts out of the host and each slot adopts.
import { canonical, fragment } from './canonical.js';
import { loadComponents } from './registry.js';
import { mountComponents } from '@varde/pages-static/components/mount.js';
import cases from './fixtures/containers.json';

const { m, components } = loadComponents();

function heldMap(c) {
  const held = new Map();
  for (const [id, html] of Object.entries(c.held)) {
    const slot = document.createElement('div');
    slot.dataset.hold = id;
    slot.innerHTML = html;
    held.set(id, slot);
  }
  return held;
}

function render(c, blockId = 't') {
  const host = document.createElement('div');
  m.render(host, components[c.kind].view(m, c.props, components, blockId, heldMap(c)));
  return host;
}

// The host element the server writes: props, noscript source, then one filled slot per held block.
function hostMarkup(c, source = 'src') {
  const slots = Object.entries(c.held).map(([id, html]) => `<div class="vd-containers-slot" data-hold="${id}">${html}</div>`).join('');
  const props = JSON.stringify(c.props).replace(/</g, '\\u003c');
  return `<div data-mithril="${c.kind}" data-block-id="t" data-copy=""><noscript><pre>${source}</pre></noscript><script type="application/json">${props}</script>${slots}</div>`;
}

describe('container blocks', () => {
  it.each(cases.map((c) => [c.name, c]))('component DOM equals the Python DOM: %s', (_name, c) => {
    const expected = fragment(c.html);
    expected.firstElementChild.removeAttribute('data-copy'); // the host carries the copy text
    expect(canonical(render(c))).toBe(canonical(expected));
  });

  it('puts each held node, not a copy, into its slot in order', () => {
    const c = cases.find((x) => x.name === 'tabs-three');
    const held = heldMap(c);
    const first = held.get('a').firstElementChild;
    const host = document.createElement('div');
    m.render(host, components.tabs.view(m, c.props, components, 't', held));
    expect([...host.querySelectorAll('.block')].map((b) => b.id)).toEqual(['blk-a', 'blk-b', 'blk-c', 'blk-d']);
    expect(host.querySelector('#blk-a')).toBe(first);
  });
});

describe('mounting a container host', () => {
  it('lifts the held children out, draws the panels and mounts the hosts nested inside', () => {
    const c = { ...cases.find((x) => x.name === 'columns-two') };
    c.held = {
      a: '<div class="block" id="blk-a"><div data-mithril="callout" data-block-id="a"><script type="application/json">{"tone":"info","text":"Nested A"}</script></div></div>',
      b: '<div class="block" id="blk-b"><p>plain</p></div>',
      c: '<div class="block" id="blk-c"><p>plain c</p></div>'
    };
    document.body.innerHTML = `<main data-role="page"><div class="block" id="blk-t">${hostMarkup(c)}</div></main>`;
    const events = [];
    document.body.addEventListener('vd-mounted', (event) => events.push(event.target.dataset.mithril));
    expect(mountComponents(document, m, components)).toBe(2);
    expect(events).toEqual(['columns', 'callout']);
    const nested = document.querySelector('#blk-a [data-mithril="callout"]');
    expect(nested.dataset.mounted).toBe('1');
    expect(nested.textContent).toContain('Nested A');
    expect(document.querySelectorAll('.vd-columns-panel .vd-containers-slot').length).toBe(3);
    expect(document.querySelector('[data-hold]')).toBeNull();
    expect(document.querySelector('[data-mithril="columns"] > section.vd-columns')).not.toBeNull();
  });

  it('keeps nested hosts working when the page remounts a replaced container block', () => {
    const c = cases.find((x) => x.name === 'tabs-single');
    document.body.innerHTML = `<main data-role="page"><div class="block" id="blk-t">${hostMarkup(c)}</div></main>`;
    mountComponents(document, m, components);
    document.body.innerHTML = `<main data-role="page"><div class="block" id="blk-t">${hostMarkup(c, 'again')}</div></main>`;
    expect(mountComponents(document, m, components)).toBe(1);
    expect(document.querySelectorAll('#blk-a').length).toBe(1);
  });
});

describe('container markup contracts', () => {
  const tabs = () => render(cases.find((x) => x.name === 'tabs-three'));

  it('labels each tab panel by its heading and shows every panel (containers.js hides them)', () => {
    const panels = [...tabs().querySelectorAll(':scope > section > .vd-ctabs-panel')];
    expect(panels.map((p) => p.querySelector(':scope > .vd-containers-label').textContent)).toEqual(['Code', 'Change', 'Checks']);
    expect(panels[0].getAttribute('aria-labelledby')).toBe('vd-ctab-t-1-h');
    expect(panels.every((p) => !p.hidden)).toBe(true);
  });

  it('names unlabelled columns by number and sizes the grid by their count', () => {
    const host = render(cases.find((x) => x.name === 'columns-two'));
    expect(host.querySelector('.vd-columns-grid').classList.contains('vd-columns-n2')).toBe(true);
    expect([...host.querySelectorAll('.vd-columns-panel')].map((p) => p.getAttribute('aria-label'))).toEqual(['Column 1', 'Column 2']);
  });

  it('keeps hostile labels as text', () => {
    const host = render(cases.find((x) => x.name === 'tabs-hostile'));
    expect(host.querySelector('script')).toBeNull();
    expect(host.querySelector('.vd-containers-label').textContent).toContain('<script>');
  });
});
