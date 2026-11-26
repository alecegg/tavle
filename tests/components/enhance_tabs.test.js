// ui-states tab enhancer (tabs.js): one tab per state tile in a grid.
import { fragment } from './canonical.js';
import { enhanceStates } from '@ui/static/tabs.js';
import uiStates from './fixtures/ui-states.json';

const statesHtml = uiStates.find((c) => c.html.includes('class="vb ui-states"')).html;

function mount(html) {
  const block = fragment(html).firstElementChild;
  document.body.append(block);
  return block;
}

function press(target, key) {
  const event = new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true });
  target.dispatchEvent(event);
  return event;
}

const tile = (name) => `<div class="vb-state"><h5>${name}</h5></div>`;
const grid = (...names) => `<div class="vb-grid">${names.map((name) => tile(name)).join('')}</div>`;

afterEach(() => {
  document.body.replaceChildren();
  history.replaceState(null, '', location.pathname + location.search);
});

const tabsOf = (root) => Array.from(root.querySelectorAll('.vb-tab'));
const tilesOf = (root) => Array.from(root.querySelectorAll('.vb-state'));
const hiddenFlags = (nodes) => nodes.map((node) => node.hidden);
const selectedFlags = (tabs) => tabs.map((tab) => tab.getAttribute('aria-selected'));

describe('enhanceStates', () => {
  function enhanced(html) {
    const block = mount(html);
    enhanceStates(block);
    return block;
  }

  describe('which grids get tabs', () => {
    it('leaves a grid asked to wrap as it is', () => {
      const block = enhanced(
        `<div class="vb"><div class="vb-grid" data-layout="grid">${tile('a')}${tile('b')}</div></div>`
      );
      expect(block.querySelector('[role="tablist"]')).toBeNull();
      expect(hiddenFlags(tilesOf(block))).toEqual([false, false]);
    });

    it('leaves a grid with fewer than two tiles as it is', () => {
      const block = enhanced(`<div class="vb">${grid('only')}</div>`);
      expect(block.querySelector('[role="tablist"]')).toBeNull();
      expect(hiddenFlags(tilesOf(block))).toEqual([false]);
    });
  });

  describe('structure', () => {
    it('puts the tablist before its grid, one tab per tile labelled by its heading', () => {
      const block = enhanced(statesHtml);
      const list = block.querySelector('[role="tablist"]');
      expect(list.getAttribute('aria-label')).toBe('Screen states');
      expect(list.nextElementSibling).toBe(block.querySelector('.vb-grid'));
      expect(tabsOf(list).map((tab) => tab.textContent)).toEqual(['empty', 'loading', 'error', 'offline', 'partial']);
    });

    it('names a tab "state" when its tile has no heading', () => {
      const block = enhanced(
        `<div class="vb"><div class="vb-grid"><div class="vb-state"><p>x</p></div><div class="vb-state"><p>y</p></div></div></div>`
      );
      expect(tabsOf(block).map((tab) => tab.textContent)).toEqual(['state', 'state']);
    });

    it('links each tab to its tile and each tile back to its tab', () => {
      const block = enhanced(statesHtml);
      const tiles = tilesOf(block);
      tabsOf(block).forEach((tab, i) => {
        expect(tab.getAttribute('role')).toBe('tab');
        expect(tab.getAttribute('aria-controls')).toBe(tiles[i].id);
        expect(tiles[i].getAttribute('aria-labelledby')).toBe(tab.id);
        expect(tiles[i].getAttribute('role')).toBe('tabpanel');
        expect(tiles[i].tabIndex).toBe(0);
      });
    });

    it('gives the tiles of two grids distinct ids', () => {
      const block = enhanced(`<div class="vb">${grid('a', 'b')}${grid('c', 'd')}</div>`);
      expect(new Set(tilesOf(block).map((tile) => tile.id)).size).toBe(4);
    });
  });

  describe('selection', () => {
    it('shows only the first tile at first', () => {
      const block = enhanced(statesHtml);
      const tabs = tabsOf(block);
      expect(hiddenFlags(tilesOf(block))).toEqual([false, true, true, true, true]);
      expect(selectedFlags(tabs)).toEqual(['true', 'false', 'false', 'false', 'false']);
      expect(tabs.map((tab) => tab.tabIndex)).toEqual([0, -1, -1, -1, -1]);
    });

    it('shows the clicked tile and makes its tab the tab stop', () => {
      const block = enhanced(statesHtml);
      const tabs = tabsOf(block);
      tabs[2].click();
      expect(hiddenFlags(tilesOf(block))).toEqual([true, true, false, true, true]);
      expect(selectedFlags(tabs)).toEqual(['false', 'false', 'true', 'false', 'false']);
      expect(tabs.map((tab) => tab.tabIndex)).toEqual([-1, -1, 0, -1, -1]);
    });
  });

  describe('keys', () => {
    it('moves with the arrow keys, wrapping at both ends, and focuses the new tab', () => {
      const block = enhanced(statesHtml);
      const tabs = tabsOf(block);
      tabs[0].focus();
      press(tabs[0], 'ArrowRight');
      expect(document.activeElement).toBe(tabs[1]);
      expect(hiddenFlags(tilesOf(block))).toEqual([true, false, true, true, true]);
      press(tabs[1], 'ArrowLeft');
      expect(document.activeElement).toBe(tabs[0]);
      press(tabs[0], 'ArrowUp');
      expect(document.activeElement).toBe(tabs[4]);
      press(tabs[4], 'ArrowDown');
      expect(document.activeElement).toBe(tabs[0]);
      expect(selectedFlags(tabs)[0]).toBe('true');
    });

    it('jumps to the first and last tab with Home and End', () => {
      const block = enhanced(statesHtml);
      const tabs = tabsOf(block);
      tabs[0].focus();
      press(tabs[0], 'End');
      expect(document.activeElement).toBe(tabs[4]);
      expect(hiddenFlags(tilesOf(block))).toEqual([true, true, true, true, false]);
      press(tabs[4], 'Home');
      expect(document.activeElement).toBe(tabs[0]);
      expect(hiddenFlags(tilesOf(block))).toEqual([false, true, true, true, true]);
    });

    it('prevents the keys it handles', () => {
      const tabs = tabsOf(enhanced(statesHtml));
      tabs[0].focus();
      expect(press(tabs[0], 'ArrowRight').defaultPrevented).toBe(true);
    });

    it('leaves Home alone on the first tab, where nothing moves', () => {
      const tabs = tabsOf(enhanced(statesHtml));
      tabs[0].focus();
      expect(press(tabs[0], 'Home').defaultPrevented).toBe(false);
      expect(selectedFlags(tabs)[0]).toBe('true');
    });

    it('ignores an unrelated key and does not prevent it', () => {
      const block = enhanced(statesHtml);
      const tabs = tabsOf(block);
      tabs[0].focus();
      expect(press(tabs[0], 'a').defaultPrevented).toBe(false);
      expect(hiddenFlags(tilesOf(block))[0]).toBe(false);
    });

    it('ignores keys when no tab has focus', () => {
      const block = enhanced(statesHtml);
      const event = press(tabsOf(block)[2], 'ArrowRight');
      expect(event.defaultPrevented).toBe(false);
      expect(hiddenFlags(tilesOf(block))).toEqual([false, true, true, true, true]);
    });
  });
});
