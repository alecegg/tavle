// flow: enhance the server-laid-out SVG of a `flow` block. Pan and zoom come from
// viewport.js (its Reset button becomes the one shared Fit button). Selecting a step
// highlights what must come before it (dotted outline) and what follows (heavy
// outline) and says so in the readout; arrow keys on a step follow its edges.
// No layout runs in the browser.
import { control, make, statusReadout, swapClassRole, takeTabStop, whileConnected } from './dom.js';
import { fitWidth, mountSharedView } from './viewport.js';
import { bindHoverAndFocus, onItemFocus } from './view_keys.js';
import { readAdjacency } from './view_graph.js';

const HINT = 'Select a step to see what comes before and after it.';
const FOLLOW = { ArrowRight: 'out', ArrowDown: 'out', ArrowLeft: 'in', ArrowUp: 'in' };
const MIN_FIT = 0.25; // the whole flow fits the width down to the viewport's own minimum zoom
const SCROLLBAR = 18;
const ZOOM_IN = 1.25;
const ZOOM_OUT = 0.8;
const ROLE = / vd-(sel|dim)| vf-(up|down)/g;

function reachable(start, edges) {
  const seen = new Set();
  const queue = [start];
  while (queue.length) {
    for (const id of edges.get(queue.shift()) || []) {
      if (seen.has(id)) continue;
      seen.add(id);
      queue.push(id);
    }
  }
  seen.delete(start);
  return seen;
}

function labelOf(node) {
  const title = node.querySelector('title');
  return title ? title.textContent : node.dataset.id;
}

function naming(ids, byId) {
  return ids.length ? ids.map((id) => labelOf(byId.get(id))).join(', ') : 'none';
}

function nodeRole(name, id, before, after) {
  if (!id) return '';
  if (name === id) return ' vd-sel';
  if (before.has(name)) return ' vf-up';
  if (after.has(name)) return ' vf-down';
  return ' vd-dim';
}

function edgeRole(edge, id, upSet, downSet) {
  if (!id) return '';
  const { from, to } = edge.dataset;
  const hot = (upSet.has(from) && upSet.has(to)) || (downSet.has(from) && downSet.has(to));
  return hot ? ' vd-hot' : ' vd-dim';
}

export function enhanceFlow(block) {
  if (!block.classList.contains('flow')) return;
  const view = block.querySelector('.vd-view');
  const host = block.querySelector('.vd-views');
  const svg = view && view.querySelector('svg');
  if (!svg || !host) return;
  const nodes = Array.from(view.querySelectorAll('.vd-node'));
  const byId = new Map(nodes.map((n) => [n.dataset.id, n]));
  const { out, into } = readAdjacency(view);
  const readout = statusReadout(host, 'vd-detail', HINT);
  const state = { selected: null, hover: null, focus: null };
  const cycle = new Map();

  function paint() {
    const id = state.hover || state.focus || state.selected;
    const before = id ? reachable(id, into) : new Set();
    const after = id ? reachable(id, out) : new Set();
    for (const [name, node] of byId) {
      const role = nodeRole(name, id, before, after);
      swapClassRole(node, ROLE, role);
      node.setAttribute('aria-pressed', String(name === state.selected));
    }
    const upSet = new Set([...before, id]);
    const downSet = new Set([...after, id]);
    for (const edge of view.querySelectorAll('.vd-edge')) {
      const base = edge.getAttribute('class').replace(/ vd-(hot|dim)/g, '');
      edge.setAttribute('class', base + edgeRole(edge, id, upSet, downSet));
    }
  }

  function describe(id) {
    const before = reachable(id, into);
    const after = reachable(id, out);
    return labelOf(byId.get(id)) + '. Before it: ' + naming([...before], byId) + '. After it: ' + naming([...after], byId) + '.';
  }

  function select(node) {
    const id = node.dataset.id;
    state.selected = state.selected === id ? null : id;
    readout.textContent = state.selected ? describe(id) : HINT;
    paint();
  }

  function follow(node, direction) {
    const ids = (direction === 'out' ? out : into).get(node.dataset.id) || [];
    if (!ids.length) return;
    const key = direction + node.dataset.id;
    const count = cycle.get(key) || 0;
    cycle.set(key, count + 1);
    byId.get(ids[count % ids.length]).focus();
  }

  function refit() {
    fitWidth(svg, host.clientWidth - SCROLLBAR, MIN_FIT);
  }

  svg.setAttribute('role', 'group');
  view.tabIndex = 0;
  view.setAttribute('role', 'region');
  view.setAttribute('aria-label', 'Flow: arrow keys pan, plus and minus zoom, 0 fits to view');
  for (const node of nodes) {
    node.setAttribute('role', 'button');
    node.setAttribute('tabindex', '-1');
    node.setAttribute('aria-pressed', 'false');
    node.setAttribute('aria-label', labelOf(node) + ', step');
  }
  if (nodes[0]) nodes[0].setAttribute('tabindex', '0');
  const viewport = mountSharedView(view, svg, { minScale: 0.25, maxScale: 8 });

  onItemFocus(view, '.vd-node', (target) => {
    takeTabStop(view, target);
    state.focus = target.dataset.id;
    paint();
  });
  bindHoverAndFocus(view, {
    selector: '.vd-node',
    state,
    keyOf: (node) => (node ? node.dataset.id : null),
    paint,
  });
  view.addEventListener('click', (event) => {
    const node = event.target.closest('.vd-node');
    if (node) select(node);
  });
  view.addEventListener('keydown', (event) => {
    const node = event.target.closest('.vd-node');
    if (!node || event.target !== node) return;
    const activate = event.key === 'Enter' || event.key === ' ';
    const direction = FOLLOW[event.key];
    if (!activate && !direction && event.key !== 'Escape') return;
    event.preventDefault();
    if (event.key === 'Escape') {
      state.selected = null;
      readout.textContent = HINT;
      paint();
    } else if (activate) {
      select(node);
    } else {
      follow(node, direction);
    }
  });

  const bar = make('div', 'vb-controls vb-flowbar');
  bar.append(
    control('+', () => viewport.zoom(ZOOM_IN), 'vb-ctl', 'Zoom in'),
    control('−', () => viewport.zoom(ZOOM_OUT), 'vb-ctl', 'Zoom out'),
    control('Fit', () => { refit(); viewport.reset(); view.scrollTo(0, 0); }, 'vb-ctl', 'Fit whole flow'),
  );
  host.before(bar);
  refit();
  whileConnected(host, 'resize', refit);
}
