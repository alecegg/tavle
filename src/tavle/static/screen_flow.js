// screen-flow: enhance the server-drawn screens of a `screen-flow` block. Pan and zoom come
// from viewport.js (one shared bar: + - Reset). Screens are the controls: select one (click,
// tap, Enter, Space) and an announced panel reads its regions, notes and next step while its
// entry in the text list gets a heavy edge. Arrow keys follow the reading order (lane by
// lane, step by step), Home and End jump, Escape clears. The layout is drawn on the server
// (an across and a down drawing; CSS shows one), so no layout runs here.
import { keepInside, statusReadout } from './dom.js';
import { mountSharedView, sharedBar } from './viewport.js';
import { ARROWS_AND_ENDS, bindHoverAndFocus, handleViewKey, itemAfter, onItemFocus } from './view_keys.js';

const HINT = 'Select a screen to read its regions, notes and next step.';

function labelOf(screen) {
  const title = screen.querySelector(':scope > title');
  return title ? title.textContent : screen.dataset.screen;
}

function readView(view) {
  const svg = view.querySelector('svg.vd-sf-svg');
  if (!svg) return null;
  return { view, svg, screens: Array.from(svg.querySelectorAll('.vd-sf-screen')) };
}

function describe(item) {
  const text = (selector) => {
    const node = item.querySelector(selector);
    return node ? node.textContent : '';
  };
  const notes = Array.from(item.querySelectorAll('.vd-sf-note'));
  const said = notes.length
    ? notes.map((note) => 'Note ' + note.value + ': ' + note.textContent + '.').join(' ')
    : 'No notes.';
  return text('.vd-sf-name') + '. ' + text('.vd-sf-regions') + '. ' + said + ' ' + text('.vd-sf-next') + '.';
}

export function enhanceScreenFlow(block) {
  if (!block.classList.contains('screen-flow')) return;
  const host = block.querySelector('.vd-sf-views');
  if (!host) return;
  const views = Array.from(host.querySelectorAll('.vd-sf-view')).map(readView).filter(Boolean);
  if (!views.length) return;
  const items = new Map(Array.from(block.querySelectorAll('.vd-sf-item')).map((li) => [li.dataset.screen, li]));
  const readout = statusReadout(host, 'vd-sf-detail', HINT);
  const state = { selected: null, hover: null, focus: null };

  function paint() {
    const chosen = state.hover || state.focus || state.selected;
    for (const { screens } of views) {
      for (const screen of screens) {
        const id = screen.dataset.screen;
        screen.classList.toggle('vd-sf-sel', id === state.selected);
        screen.classList.toggle('vd-sf-hot', id !== state.selected && id === chosen);
        screen.setAttribute('aria-pressed', String(id === state.selected));
      }
    }
    for (const [id, item] of items) item.classList.toggle('vd-sf-item-on', id === state.selected);
  }

  function select(id) {
    state.selected = state.selected === id ? null : id;
    const item = items.get(id);
    readout.textContent = state.selected && item ? describe(item) : HINT;
    paint();
  }

  function clear() {
    state.selected = null;
    readout.textContent = HINT;
    paint();
  }

  const viewports = views.map(({ view, svg, screens }) => {
    svg.setAttribute('role', 'group');
    view.setAttribute('aria-label', svg.getAttribute('aria-label') + ' (arrow keys pan, plus and minus zoom, 0 resets the view)');
    for (const screen of screens) {
      screen.setAttribute('role', 'button');
      screen.setAttribute('tabindex', '-1');
      screen.setAttribute('aria-pressed', 'false');
      screen.setAttribute('aria-label', labelOf(screen));
    }
    if (screens[0]) screens[0].setAttribute('tabindex', '0');
    const viewport = mountSharedView(view, svg, { minScale: 0.5, maxScale: 4 });
    onItemFocus(view, '.vd-sf-screen', (target) => {
      for (const other of screens) other.setAttribute('tabindex', other === target ? '0' : '-1');
      keepInside(view, target, { margin: 8 });
      state.focus = target.dataset.screen;
      paint();
    });
    bindHoverAndFocus(view, {
      selector: '.vd-sf-screen',
      state,
      keyOf: (target) => (target ? target.dataset.screen : null),
      paint,
    });
    view.addEventListener('click', (event) => {
      const target = event.target.closest('.vd-sf-screen');
      if (target) select(target.dataset.screen);
    });
    view.addEventListener('keydown', (event) => {
      const target = event.target.closest('.vd-sf-screen');
      if (!target || event.target !== target) return;
      handleViewKey(event, {
        activate: () => select(target.dataset.screen),
        clear,
        move: (key) => itemAfter(screens, target, key).focus(),
        moveKeys: ARROWS_AND_ENDS,
      });
    });
    return viewport;
  });

  function fit() {
    for (const [i, { view }] of views.entries()) {
      viewports[i].reset();
      view.scrollTo(0, 0);
    }
  }

  host.before(sharedBar(viewports, fit, { label: 'Reset', aria: 'Reset flow view' }));
}
