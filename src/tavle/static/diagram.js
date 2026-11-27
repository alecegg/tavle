// diagram: enhance the server-laid-out SVG states of a `diagram` block.
// Pan and zoom come from viewport.js (its Reset button becomes Fit). A node focus
// or hover highlights its neighbours; click or Enter selects it and announces its
// detail; group headers collapse and expand by showing another pre-computed state;
// arrow keys on a node move along its edges. No layout runs in the browser.
import { control, make, statusReadout, takeTabStop, whileConnected } from './dom.js';
import { fitWidth, mountSharedView } from './viewport.js';
import { ARROWS, bindHoverAndFocus, handleViewKey, onItemFocus } from './view_keys.js';
import { readAdjacency } from './view_graph.js';

const HINT = 'Select a node for details.';
const FOLLOW = { ArrowRight: 'out', ArrowDown: 'out', ArrowLeft: 'in', ArrowUp: 'in' };

function nodeLabel(node) {
  const title = node.querySelector('title');
  return title ? title.textContent : node.dataset.id;
}

function prepareNode(node) {
  node.setAttribute('role', 'button');
  node.setAttribute('tabindex', '-1');
  if (node.classList.contains('vd-super')) {
    node.setAttribute('aria-expanded', 'false');
    node.setAttribute('aria-label', nodeLabel(node) + ', collapsed group');
    return;
  }
  node.setAttribute('aria-pressed', 'false');
  node.setAttribute('aria-label', nodeLabel(node) + ', ' + shapeOf(node) + ' node');
}

function shapeOf(node) {
  for (const name of ['box', 'rounded', 'cylinder', 'diamond']) {
    if (node.classList.contains('vd-' + name)) return name;
  }
  return 'box';
}

function prepareHead(head) {
  head.setAttribute('role', 'button');
  head.setAttribute('tabindex', '-1');
  head.setAttribute('aria-expanded', 'true');
  head.setAttribute('aria-label', head.querySelector('.vd-group-label').textContent + ', group');
}

function nodeRole(name, id, near) {
  if (!id) return '';
  if (name === id) return ' vd-sel';
  return near.has(name) ? ' vd-near' : ' vd-dim';
}

function edgeRole(edge, id) {
  if (!id) return '';
  const touches = edge.dataset.from === id || edge.dataset.to === id;
  return touches ? ' vd-hot' : ' vd-dim';
}

function neighbours(adjacency, id) {
  const near = new Set();
  if (!id) return near;
  for (const to of adjacency.out.get(id) || []) near.add(to);
  for (const from of adjacency.into.get(id) || []) near.add(from);
  return near;
}

function paint(view, adjacency, id, selected) {
  const near = neighbours(adjacency, id);
  for (const node of view.querySelectorAll('.vd-node')) {
    const name = node.dataset.id;
    const role = nodeRole(name, id, near);
    node.setAttribute('class', node.getAttribute('class').replace(/ vd-(sel|near|dim)/g, '') + role);
    if (node.hasAttribute('aria-pressed')) node.setAttribute('aria-pressed', String(name === selected));
  }
  for (const edge of view.querySelectorAll('.vd-edge')) {
    const base = edge.getAttribute('class').replace(/ vd-(hot|dim)/g, '');
    edge.setAttribute('class', base + edgeRole(edge, id));
  }
}

function detailFor(block, id, node) {
  const item = Array.from(block.querySelectorAll('.vb-data li[data-node]')).find((li) => li.dataset.node === id);
  const note = item && item.querySelector('.vd-detail-text');
  return note ? nodeLabel(node) + ': ' + note.textContent : nodeLabel(node);
}

const MIN_FIT = 0.25; // the whole graph fits the width down to the viewport's own minimum zoom
const SCROLLBAR = 18;
const ZOOM_IN = 1.25;
const ZOOM_OUT = 0.8;

export function enhanceDiagram(block) {
  if (!block.classList.contains('diagram')) return;
  const views = Array.from(block.querySelectorAll('.vd-view'));
  const host = block.querySelector('.vd-views');
  if (!views.length || !host) return;
  const readout = statusReadout(host, 'vb-readout vd-detail', HINT);
  const state = { mask: 0, selected: null, hover: null, focus: null };
  const mounted = new Map();

  function current() {
    return views.find((v) => Number(v.dataset.mask) === state.mask);
  }

  function repaint() {
    const view = current();
    const id = state.hover || state.focus || state.selected;
    paint(view, mounted.get(view).adjacency, id, state.selected);
  }

  function select(node) {
    const id = node.dataset.id;
    state.selected = state.selected === id ? null : id;
    readout.textContent = state.selected ? detailFor(block, id, node) : HINT;
    repaint();
  }

  function showMask(mask, bit) {
    state.mask = mask;
    state.selected = state.hover = state.focus = null;
    readout.textContent = HINT;
    for (const view of views) {
      const on = Number(view.dataset.mask) === mask;
      view.hidden = !on;
    }
    const view = current();
    refit();
    paint(view, mounted.get(view).adjacency, null, null);
    const head = view.querySelector('[data-bit="' + bit + '"]');
    if (head) head.focus();
  }

  function refit() {
    // First paint and resize show the whole graph; + and the pinch zoom back in.
    for (const { svg } of mounted.values()) fitWidth(svg, host.clientWidth - SCROLLBAR, MIN_FIT);
  }

  function toggleGroup(head) {
    const bit = Number(head.dataset.bit);
    showMask(state.mask ^ bit, bit);
  }

  function follow(view, node, direction) {
    const adjacency = mounted.get(view).adjacency;
    const ids = (direction === 'out' ? adjacency.out : adjacency.into).get(node.dataset.id) || [];
    if (!ids.length) return;
    const key = direction + node.dataset.id;
    const step = (mounted.get(view).cycle.get(key) || 0) % ids.length;
    mounted.get(view).cycle.set(key, step + 1);
    const target = Array.from(view.querySelectorAll('.vd-node')).find((n) => n.dataset.id === ids[step]);
    if (target) target.focus();
  }

  for (const view of views) {
    const svg = view.querySelector('svg');
    svg.setAttribute('role', 'group');
    view.tabIndex = 0;
    view.setAttribute('role', 'region');
    view.setAttribute('aria-label', 'Diagram: arrow keys pan, plus and minus zoom, 0 fits to view');
    const nodes = Array.from(view.querySelectorAll('.vd-node'));
    const heads = Array.from(view.querySelectorAll('.vd-group-head'));
    nodes.forEach(prepareNode);
    heads.forEach(prepareHead);
    const first = nodes[0] || heads[0];
    if (first) first.setAttribute('tabindex', '0');
    const adjacency = readAdjacency(view);
    const viewport = mountSharedView(view, svg, { minScale: 0.25, maxScale: 8 });
    mounted.set(view, { adjacency, viewport, svg, cycle: new Map() });

    onItemFocus(view, '.vd-node, .vd-group-head', (target) => {
      takeTabStop(view, target);
      state.focus = target.classList.contains('vd-node') ? target.dataset.id : null;
      repaint();
    });
    bindHoverAndFocus(view, {
      selector: '.vd-node',
      state,
      keyOf: (node) => (node ? node.dataset.id : null),
      paint: repaint,
    });
    view.addEventListener('click', (event) => {
      const group = event.target.closest('.vd-super, .vd-group-head');
      if (group) return toggleGroup(group);
      const node = event.target.closest('.vd-node');
      if (node) select(node);
    });
    view.addEventListener('keydown', (event) => {
      const node = event.target.closest('.vd-node, .vd-group-head');
      if (!node || event.target !== node) return;
      const activate = () => {
        if (node.matches('.vd-super, .vd-group-head')) toggleGroup(node);
        else select(node);
      };
      const clear = () => {
        state.selected = null;
        readout.textContent = HINT;
        repaint();
      };
      handleViewKey(event, {
        activate,
        clear,
        move: (key) => follow(view, node, FOLLOW[key]),
        moveKeys: ARROWS,
      });
    });
  }
  function fitWhole() {
    const { svg, viewport } = mounted.get(current());
    fitWidth(svg, host.clientWidth - SCROLLBAR, MIN_FIT);
    viewport.reset();
    current().scrollTo(0, 0);
  }

  const shown = () => mounted.get(current()).viewport;
  const bar = make('div', 'vb-controls vb-flowbar');
  bar.append(
    control('+', () => shown().zoom(ZOOM_IN), 'vb-ctl', 'Zoom in'),
    control('\u2212', () => shown().zoom(ZOOM_OUT), 'vb-ctl', 'Zoom out'),
    control('Fit', fitWhole, 'vb-ctl', 'Fit whole diagram'),
  );
  host.before(bar);
  refit();
  whileConnected(host, 'resize', refit);
}
