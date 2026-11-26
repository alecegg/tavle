import { enhanceFlow } from '@ui/static/flow.js';
import fixtures from './fixtures/flow.json';
import { fragment } from './canonical.js';

function setup(
  edges = [
    ['a', 'b'],
    ['b', 'c'],
    ['a', 'd']
  ]
) {
  const block = document.createElement('div');
  block.className = 'flow';
  block.innerHTML = `<div class="vd-views"><div class="vd-view"><svg width="400" height="200" viewBox="0 0 400 200">
    ${['a', 'b', 'c', 'd', 'e'].map((id) => `<g class="vd-node" data-id="${id}"><title>${id.toUpperCase()}</title></g>`).join('')}
    ${edges.map(([from, to]) => `<path class="vd-edge" data-from="${from}" data-to="${to}"></path>`).join('')}
    </svg></div></div>`;
  document.body.append(block);
  const host = block.querySelector('.vd-views');
  Object.defineProperty(host, 'clientWidth', { configurable: true, value: 218 });
  const view = block.querySelector('.vd-view');
  view.scrollTo = vi.fn();
  enhanceFlow(block);
  const nodes = Object.fromEntries([...block.querySelectorAll('.vd-node')].map((n) => [n.dataset.id, n]));
  return { block, host, view, nodes, svg: block.querySelector('svg'), readout: block.querySelector('.vd-detail') };
}

function key(node, value) {
  const event = new KeyboardEvent('keydown', { key: value, bubbles: true, cancelable: true });
  node.dispatchEvent(event);
  return event;
}

afterEach(() => {
  document.body.replaceChildren();
  vi.restoreAllMocks();
});

describe('flow enhancement', () => {
  it('enhances the rendered rich flow fixture', () => {
    const root = fragment(fixtures.find((item) => item.name === 'rich-flow:f1').html);
    document.body.append(...root.childNodes);
    const block = document.querySelector('.flow');
    const host = block.querySelector('.vd-views');
    Object.defineProperty(host, 'clientWidth', { configurable: true, value: 400 });
    enhanceFlow(block);
    const steps = block.querySelectorAll('.vd-node');
    expect(steps.length).toBeGreaterThan(1);
    expect(steps[0].getAttribute('role')).toBe('button');
    steps[0].dispatchEvent(new MouseEvent('click', { bubbles: true }));
    expect(block.querySelector('.vd-detail').textContent).toContain('Before it:');
  });

  it('ignores other blocks and gives steps accessible roles and one tab stop', () => {
    const other = document.createElement('div');
    enhanceFlow(other);
    expect(other.children).toHaveLength(0);
    const { nodes, readout } = setup();
    expect(nodes.a.getAttribute('role')).toBe('button');
    expect(nodes.a.getAttribute('aria-label')).toBe('A, step');
    expect(nodes.a.getAttribute('aria-pressed')).toBe('false');
    expect(Object.values(nodes).filter((n) => n.getAttribute('tabindex') === '0')).toHaveLength(1);
    expect(readout.textContent).toBe('Select a step to see what comes before and after it.');
  });

  it('selects transitive relations and clears on a second click or Escape', () => {
    const { nodes, block, readout } = setup();
    nodes.c.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    expect(readout.textContent).toBe('C. Before it: B, A. After it: none.');
    expect(nodes.c.classList.contains('vd-sel')).toBe(true);
    expect(nodes.a.classList.contains('vf-up')).toBe(true);
    expect(nodes.b.classList.contains('vf-up')).toBe(true);
    expect(nodes.d.classList.contains('vd-dim')).toBe(true);
    expect(nodes.c.getAttribute('aria-pressed')).toBe('true');
    const edges = block.querySelectorAll('.vd-edge');
    expect(edges[0].classList.contains('vd-hot')).toBe(true);
    expect(edges[2].classList.contains('vd-dim')).toBe(true);
    nodes.c.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    expect(readout.textContent).toContain('Select a step');
    key(nodes.c, 'Enter');
    expect(key(nodes.c, 'Escape').defaultPrevented).toBe(true);
    expect(readout.textContent).toContain('Select a step');
    expect(nodes.c.getAttribute('aria-pressed')).toBe('false');
  });

  it('marks successors and activates with Space', () => {
    const { nodes, readout } = setup();
    expect(key(nodes.a, ' ').defaultPrevented).toBe(true);
    expect(readout.textContent).toBe('A. Before it: none. After it: B, D, C.');
    expect(nodes.b.classList.contains('vf-down')).toBe(true);
    expect(nodes.c.classList.contains('vf-down')).toBe(true);
    expect(nodes.e.classList.contains('vd-dim')).toBe(true);
  });

  it('terminates cycles without including the selected step in its own relations', () => {
    const { nodes, readout } = setup([
      ['a', 'b'],
      ['b', 'c'],
      ['c', 'a']
    ]);
    nodes.a.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    expect(readout.textContent).toBe('A. Before it: C, B. After it: B, C.');
    expect(nodes.a.classList.contains('vd-sel')).toBe(true);
  });

  it('prioritizes hover over focus over selection and follows cycling edges', () => {
    const { nodes, view } = setup();
    nodes.c.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    nodes.a.focus();
    expect(nodes.a.classList.contains('vd-sel')).toBe(true);
    nodes.b.dispatchEvent(new Event('pointerover', { bubbles: true }));
    expect(nodes.b.classList.contains('vd-sel')).toBe(true);
    view.dispatchEvent(new Event('pointerleave'));
    expect(nodes.a.classList.contains('vd-sel')).toBe(true);
    expect(key(nodes.a, 'ArrowRight').defaultPrevented).toBe(true);
    expect(document.activeElement).toBe(nodes.b);
    nodes.a.focus();
    key(nodes.a, 'ArrowDown');
    expect(document.activeElement).toBe(nodes.d);
    expect(key(nodes.d, 'x').defaultPrevented).toBe(false);
    nodes.d.blur();
    expect(nodes.c.classList.contains('vd-sel')).toBe(true);
  });

  it('zooms, fits, and refits on resize', () => {
    const { block, host, view, svg } = setup();
    expect(svg.getAttribute('width')).toBe('200');
    const initial = svg.getAttribute('viewBox');
    block.querySelector('[aria-label="Zoom in"]').click();
    expect(svg.getAttribute('viewBox')).not.toBe(initial);
    block.querySelector('[aria-label="Zoom out"]').click();
    expect(svg.getAttribute('viewBox').split(' ').map(Number)).toEqual([0, 0, 400, 200]);
    Object.defineProperty(host, 'clientWidth', { configurable: true, value: 118 });
    block.querySelector('[aria-label="Fit whole flow"]').click();
    expect(svg.getAttribute('width')).toBe('100');
    expect(view.scrollTo).toHaveBeenCalledWith(0, 0);
    Object.defineProperty(host, 'clientWidth', { configurable: true, value: 418 });
    window.dispatchEvent(new Event('resize'));
    expect(svg.getAttribute('width')).toBe('400');
  });
});
