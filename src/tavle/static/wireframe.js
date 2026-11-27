// wireframe: enhance the server-drawn SVG frames of a `wireframe` block. Pan and zoom
// come from viewport.js (one shared bar: + - Fit); double-tap or double-click fits.
// Regions are the controls: select one (click, tap, Enter, Space) and an announced panel
// reads its kind and notes while its notes-list entries get a heavy edge. Arrow keys
// move between regions in reading order, Home and End jump, Escape clears.
// No layout runs in the browser.
import { keepInside, statusReadout, swapClassRole } from './dom.js';
import { fitWidth, mountSharedView, sharedBar } from './viewport.js';
import { ARROWS_AND_ENDS, bindHoverAndFocus, handleViewKey, itemAfter, onItemFocus } from './view_keys.js';

const HINT = 'Select a region to read its notes.';
const MIN_FIT = 0.5;
const SCROLLBAR = 18;
const TAP_MS = 350;
const TAP_PX = 30;
const ROLE = / vw-(sel|hot)/g;

function labelOf(region) {
  const title = region.querySelector('title');
  return title ? title.textContent : region.dataset.region;
}

// Two taps close together fit the view; pinches and drags never count as taps.
function bindDoubleTap(svg, fit) {
  let last = null;
  let multi = false;
  let down = 0;
  svg.addEventListener('dblclick', (event) => { event.preventDefault(); fit(); });
  svg.addEventListener('pointerdown', (event) => {
    down += 1;
    if (down > 1) multi = true;
    svg.dataset.tapX = String(event.clientX);
    svg.dataset.tapY = String(event.clientY);
  });
  svg.addEventListener('pointercancel', () => { down = 0; multi = false; });
  svg.addEventListener('pointerup', (event) => {
    down = Math.max(0, down - 1);
    const clean = !multi;
    if (down === 0) multi = false;
    if (event.pointerType !== 'touch' || !clean) return;
    const moved = Math.hypot(event.clientX - Number(svg.dataset.tapX), event.clientY - Number(svg.dataset.tapY));
    if (moved > TAP_PX) { last = null; return; }
    const again = last && event.timeStamp - last.t < TAP_MS && Math.hypot(event.clientX - last.x, event.clientY - last.y) < TAP_PX;
    last = again ? null : { t: event.timeStamp, x: event.clientX, y: event.clientY };
    if (again) fit();
  });
}

function readFrame(fig, index) {
  const view = fig.querySelector('.vw-view');
  const svg = view && view.querySelector('svg');
  if (!svg) return null;
  const regions = Array.from(svg.querySelectorAll('.vw-region'));
  const notes = Array.from(fig.querySelectorAll('.vw-note'));
  const caption = fig.querySelector('figcaption');
  return { index, view, svg, regions, notes, caption: caption ? caption.textContent : '' };
}

function noteText(note) {
  const label = note.querySelector('strong');
  return note.textContent.slice(label ? label.textContent.length + 2 : 0);
}

function describe(frame, region) {
  const found = frame.notes.filter((note) => note.dataset.region === region.dataset.region);
  const said = found.length
    ? found.map((note) => 'Note ' + note.value + ': ' + noteText(note) + '.').join(' ')
    : 'No notes.';
  const prefix = frame.caption ? frame.caption + ': ' : '';
  return prefix + labelOf(region) + '. ' + said;
}

function paintFrame(frame, selected, chosen) {
  for (const region of frame.regions) {
    const key = frame.index + ':' + region.dataset.region;
    const role = key === selected ? ' vw-sel' : key === chosen ? ' vw-hot' : '';
    swapClassRole(region, ROLE, role);
    region.setAttribute('aria-pressed', String(key === selected));
  }
  for (const note of frame.notes) {
    const on = selected === frame.index + ':' + note.dataset.region;
    note.classList.toggle('vw-note-on', on);
  }
}

export function enhanceWireframe(block) {
  if (!block.classList.contains('wireframe')) return;
  const host = block.querySelector('.vw-frames');
  if (!host) return;
  const frames = Array.from(host.querySelectorAll('.vw-fig')).map(readFrame).filter(Boolean);
  if (!frames.length) return;
  const readout = statusReadout(host, 'vw-detail', HINT);
  const state = { selected: null, hover: null, focus: null };

  function paint() {
    const chosen = state.hover || state.focus || state.selected;
    for (const frame of frames) paintFrame(frame, state.selected, chosen);
  }

  function select(frame, region) {
    const key = frame.index + ':' + region.dataset.region;
    state.selected = state.selected === key ? null : key;
    readout.textContent = state.selected ? describe(frame, region) : HINT;
    paint();
  }

  function clear() {
    state.selected = null;
    readout.textContent = HINT;
    paint();
  }

  const viewports = frames.map((frame) => {
    const { view, svg, regions } = frame;
    svg.setAttribute('role', 'group');
    view.setAttribute('aria-label', labelOf(svg) + ' (arrow keys pan, plus and minus zoom, 0 fits to view)');
    for (const region of regions) {
      region.setAttribute('role', 'button');
      region.setAttribute('tabindex', '-1');
      region.setAttribute('aria-pressed', 'false');
      region.setAttribute('aria-label', labelOf(region) + ', region');
    }
    if (regions[0]) regions[0].setAttribute('tabindex', '0');
    const viewport = mountSharedView(view, svg, { minScale: 0.25, maxScale: 8 });
    onItemFocus(view, '.vw-region', (target) => {
      for (const other of regions) other.setAttribute('tabindex', other === target ? '0' : '-1');
      keepInside(view, target, { margin: 8 });
      state.focus = frame.index + ':' + target.dataset.region;
      paint();
    });
    bindHoverAndFocus(view, {
      selector: '.vw-region',
      state,
      keyOf: (target) => (target ? frame.index + ':' + target.dataset.region : null),
      paint,
    });
    view.addEventListener('click', (event) => {
      const target = event.target.closest('.vw-region');
      if (target) select(frame, target);
    });
    view.addEventListener('keydown', (event) => {
      const target = event.target.closest('.vw-region');
      if (!target || event.target !== target) return;
      handleViewKey(event, {
        activate: () => select(frame, target),
        clear,
        move: (key) => itemAfter(regions, target, key).focus(),
        moveKeys: ARROWS_AND_ENDS,
      });
    });
    return viewport;
  });

  function fit() {
    for (const [i, frame] of frames.entries()) {
      fitWidth(frame.svg, frame.view.clientWidth - SCROLLBAR, MIN_FIT);
      viewports[i].reset();
      frame.view.scrollTo(0, 0);
    }
  }

  for (const frame of frames) bindDoubleTap(frame.svg, fit);
  host.before(sharedBar(viewports, fit, { label: 'Fit', aria: 'Fit whole wireframe' }));
}
