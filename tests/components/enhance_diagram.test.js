import { enhanceDiagram } from '@ui/static/diagram.js';
import fixtures from './fixtures/diagram.json';
import { fragment } from './canonical.js';
import { stubBox } from './stub-layout.js';

const hint = 'Select a node for details.';
function setup(width = 600) {
  const root = fragment(fixtures.find((item) => item.name === 'rich-diagram:d1').html);
  document.body.append(root);
  const block = root.firstElementChild;
  const host = block.querySelector('.vd-views');
  let size = width;
  Object.defineProperty(host, 'clientWidth', { configurable: true, get: () => size });
  const views = [...block.querySelectorAll('.vd-view')];
  views.forEach((view) => {
    view.scrollTo = vi.fn();
  });
  enhanceDiagram(block);
  return {
    block,
    host,
    views,
    resize: (value) => {
      size = value;
      window.dispatchEvent(new Event('resize'));
    }
  };
}
const node = (view, id) => view.querySelector(`.vd-node[data-id="${id}"]`);
const key = (target, value) => target.dispatchEvent(new KeyboardEvent('keydown', { key: value, bubbles: true }));

afterEach(() => {
  document.body.replaceChildren();
  vi.restoreAllMocks();
});

test('ignores other blocks and prepares accessible nodes and group heads', () => {
  const other = document.createElement('div');
  enhanceDiagram(other);
  expect(other.innerHTML).toBe('');
  const { views } = setup();
  expect(views).toHaveLength(4);
  expect(node(views[0], 'auth').getAttribute('aria-label')).toBe('Valid token?, diamond node');
  expect(views[0].querySelector('.vd-group-head').getAttribute('aria-label')).toBe('Edge, group');
  expect(views[1].querySelector('.vd-super').getAttribute('aria-label')).toContain('collapsed group');
  expect(views[0].querySelectorAll('.vd-node[tabindex="0"], .vd-group-head[tabindex="0"]')).toHaveLength(1);
  expect(node(views[0], 'auth').getAttribute('role')).toBe('button');
});

test('hover and focus highlight neighbours and edges and clear on leaving', () => {
  const { views } = setup();
  const view = views[0],
    auth = node(view, 'auth');
  auth.dispatchEvent(new Event('pointerover', { bubbles: true }));
  expect(auth.classList.contains('vd-sel')).toBe(true);
  expect(node(view, 'api').classList.contains('vd-near')).toBe(true);
  expect(node(view, 'db').classList.contains('vd-dim')).toBe(true);
  expect(view.querySelector('[data-from="auth"][data-to="api"]').classList.contains('vd-hot')).toBe(true);
  expect(view.querySelector('[data-from="api"][data-to="db"]').classList.contains('vd-dim')).toBe(true);
  view.dispatchEvent(new Event('pointerleave'));
  expect(auth.classList.contains('vd-sel')).toBe(false);
  auth.focus();
  expect(auth.classList.contains('vd-sel')).toBe(true);
  auth.blur();
  expect(auth.classList.contains('vd-sel')).toBe(false);
});

test('click and keyboard toggle selection, detail and escape', () => {
  const { block, views } = setup();
  const user = node(views[0], 'user'),
    readout = block.querySelector('.vd-detail');
  user.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  const detail = block.querySelector('.vb-data li[data-node="user"] .vd-detail-text');
  expect(readout.textContent).toBe(detail ? `User: ${detail.textContent}` : 'User');
  expect(user.getAttribute('aria-pressed')).toBe('true');
  key(user, 'Enter');
  expect(readout.textContent).toBe(hint);
  key(user, ' ');
  expect(user.getAttribute('aria-pressed')).toBe('true');
  key(user, 'Escape');
  expect(user.getAttribute('aria-pressed')).toBe('false');
  expect(readout.textContent).toBe(hint);
});

test('arrows follow and cycle outgoing and incoming edges', () => {
  const { views } = setup();
  const view = views[0],
    auth = node(view, 'auth');
  auth.focus();
  key(auth, 'ArrowRight');
  expect(document.activeElement).toBe(node(view, 'api'));
  auth.focus();
  key(auth, 'ArrowDown');
  expect(document.activeElement).toBe(node(view, 'user'));
  key(auth, 'ArrowLeft');
  expect(document.activeElement).toBe(node(view, 'gw'));
});

test('group toggle switches masks, clears selection and focuses the matching head', () => {
  const { block, views } = setup();
  node(views[0], 'user').dispatchEvent(new MouseEvent('click', { bubbles: true }));
  views[0].querySelector('[data-bit="1"]').dispatchEvent(new MouseEvent('click', { bubbles: true }));
  expect(views[0].hidden).toBe(true);
  expect(views[1].hidden).toBe(false);
  expect(document.activeElement).toBe(views[1].querySelector('[data-bit="1"]'));
  expect(block.querySelector('.vd-detail').textContent).toBe(hint);
  key(document.activeElement, 'Enter');
  expect(views[0].hidden).toBe(false);
  expect(document.activeElement).toBe(views[0].querySelector('[data-bit="1"]'));
});

test('zoom controls affect the shown view and Fit resets it', () => {
  const { block, views } = setup();
  const svg = views[0].querySelector('svg'),
    initial = svg.getAttribute('viewBox');
  block.querySelector('[aria-label="Zoom in"]').click();
  expect(svg.getAttribute('viewBox')).not.toBe(initial);
  block.querySelector('[aria-label="Zoom out"]').click();
  expect(Number(svg.getAttribute('viewBox').split(' ')[2])).toBeCloseTo(Number(initial.split(' ')[2]));
  block.querySelector('[aria-label="Zoom in"]').click();
  block.querySelector('[aria-label="Fit whole diagram"]').click();
  expect(svg.getAttribute('viewBox')).toBe(initial);
  expect(views[0].scrollTo).toHaveBeenCalledWith(0, 0);
});

test('fit clamps width and resize stops after detachment', () => {
  const { block, views, resize } = setup(10000);
  const svg = views[0].querySelector('svg'),
    natural = Number(svg.dataset.natW);
  expect(Number(svg.getAttribute('width'))).toBe(Math.round(natural));
  resize(1);
  expect(Number(svg.getAttribute('width'))).toBe(Math.round(natural * 0.25));
  resize(500);
  expect(Number(svg.getAttribute('width'))).toBe(482);
  block.remove();
  resize(1000);
  expect(Number(svg.getAttribute('width'))).toBe(482);
});

test('focus scrolls a node inside the view and moves the tab stop', () => {
  const { views } = setup();
  const view = stubBox(views[0], { width: 100, height: 100 });
  const target = stubBox(node(view, 'auth'), { left: 90, top: 90, width: 20, height: 20 });
  target.focus();
  expect(view.scrollLeft).toBe(14);
  expect(view.scrollTop).toBe(14);
  expect(target.getAttribute('tabindex')).toBe('0');
  expect(node(view, 'user').getAttribute('tabindex')).toBe('-1');
});
