// Tabs container enhancer (containers.js): the vd-ctabs tablist and its panels.
import { fragment } from './canonical.js';
import { enhanceContainers } from '@ui/static/containers.js';
import containers from './fixtures/containers.json';

const tabsHtml = containers.find((c) => c.name === 'tabs-three').html;

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

afterEach(() => {
  document.body.replaceChildren();
  history.replaceState(null, '', location.pathname + location.search);
});

const ctabsOf = (root) => Array.from(root.querySelectorAll('.vd-ctabs-tab'));
const panelsOf = (root) => Array.from(root.querySelectorAll('.vd-ctabs-panel'));
const hiddenFlags = (nodes) => nodes.map((node) => node.hidden);
const selectedFlags = (tabs) => tabs.map((tab) => tab.getAttribute('aria-selected'));

describe('enhanceContainers', () => {
  function enhanced(html = tabsHtml) {
    const block = mount(html);
    enhanceContainers(block);
    return block;
  }

  describe('which blocks get tabs', () => {
    it('ignores a block without the vd-ctabs class', () => {
      const block = mount(tabsHtml);
      block.classList.remove('vd-ctabs');
      enhanceContainers(block);
      expect(block.classList.contains('vd-ctabs-on')).toBe(false);
      expect(block.querySelector('[role="tablist"]')).toBeNull();
    });

    it('does nothing when the block has no panels', () => {
      const block = enhanced('<section class="vd-ctabs"></section>');
      expect(block.classList.contains('vd-ctabs-on')).toBe(false);
      expect(block.children).toHaveLength(0);
    });

    it('does nothing when a panel has no label', () => {
      const block = mount(tabsHtml);
      panelsOf(block)[1].querySelector('.vd-containers-label').remove();
      enhanceContainers(block);
      expect(block.classList.contains('vd-ctabs-on')).toBe(false);
      expect(block.querySelector('[role="tablist"]')).toBeNull();
    });
  });

  describe('structure', () => {
    it('builds one tab per panel, named by its label', () => {
      const block = enhanced();
      expect(block.classList.contains('vd-ctabs-on')).toBe(true);
      const tabs = ctabsOf(block);
      expect(tabs.map((tab) => tab.textContent)).toEqual(['Code', 'Change', 'Checks']);
      tabs.forEach((tab) => {
        expect(tab.getAttribute('role')).toBe('tab');
        expect(tab.type).toBe('button');
      });
    });

    it('labels the tablist with the block aria-label', () => {
      const block = mount(tabsHtml);
      block.setAttribute('aria-label', 'Results');
      enhanceContainers(block);
      expect(block.querySelector('[role="tablist"]').getAttribute('aria-label')).toBe('Results');
    });

    it('labels the tablist "Tabs" when the block has no aria-label', () => {
      const block = mount(tabsHtml);
      block.removeAttribute('aria-label');
      enhanceContainers(block);
      expect(block.querySelector('[role="tablist"]').getAttribute('aria-label')).toBe('Tabs');
    });

    it('puts a focusable Tab list region first in the block', () => {
      const block = enhanced();
      const region = block.firstElementChild;
      expect(region.getAttribute('role')).toBe('region');
      expect(region.getAttribute('aria-label')).toBe('Tab list');
      expect(region.tabIndex).toBe(0);
      expect(region.querySelector('[role="tablist"]')).not.toBeNull();
    });

    it('links each tab to its panel and each panel back to its tab', () => {
      const block = enhanced();
      const panels = panelsOf(block);
      ctabsOf(block).forEach((tab, i) => {
        expect(tab.getAttribute('aria-controls')).toBe(panels[i].id);
        expect(panels[i].getAttribute('aria-labelledby')).toBe(tab.id);
        expect(panels[i].getAttribute('role')).toBe('tabpanel');
      });
    });
  });

  describe('selection', () => {
    it('shows the first panel at first', () => {
      const block = enhanced();
      const tabs = ctabsOf(block);
      expect(hiddenFlags(panelsOf(block))).toEqual([false, true, true]);
      expect(selectedFlags(tabs)).toEqual(['true', 'false', 'false']);
      expect(tabs.map((tab) => tab.tabIndex)).toEqual([0, -1, -1]);
    });

    it('starts on the panel that holds the location hash', () => {
      history.replaceState(null, '', '#blk-c');
      const block = enhanced();
      expect(hiddenFlags(panelsOf(block))).toEqual([true, false, true]);
      expect(selectedFlags(ctabsOf(block))).toEqual(['false', 'true', 'false']);
    });

    it('starts on the first panel when no panel holds the location hash', () => {
      history.replaceState(null, '', '#nowhere');
      expect(hiddenFlags(panelsOf(enhanced()))).toEqual([false, true, true]);
    });

    it('shows the clicked panel', () => {
      const block = enhanced();
      const tabs = ctabsOf(block);
      tabs[2].click();
      expect(hiddenFlags(panelsOf(block))).toEqual([true, true, false]);
      expect(selectedFlags(tabs)).toEqual(['false', 'false', 'true']);
      expect(tabs.map((tab) => tab.tabIndex)).toEqual([-1, -1, 0]);
    });
  });

  describe('keys', () => {
    it('moves with the arrow keys, wrapping at both ends, and focuses the new tab', () => {
      const block = enhanced();
      const tabs = ctabsOf(block);
      tabs[0].focus();
      press(tabs[0], 'ArrowDown');
      expect(document.activeElement).toBe(tabs[1]);
      expect(hiddenFlags(panelsOf(block))).toEqual([true, false, true]);
      press(tabs[1], 'ArrowUp');
      expect(document.activeElement).toBe(tabs[0]);
      press(tabs[0], 'ArrowLeft');
      expect(document.activeElement).toBe(tabs[2]);
      press(tabs[2], 'ArrowRight');
      expect(document.activeElement).toBe(tabs[0]);
    });

    it('jumps to the first and last tab with Home and End', () => {
      const block = enhanced();
      const tabs = ctabsOf(block);
      tabs[0].focus();
      press(tabs[0], 'End');
      expect(document.activeElement).toBe(tabs[2]);
      expect(hiddenFlags(panelsOf(block))).toEqual([true, true, false]);
      press(tabs[2], 'Home');
      expect(document.activeElement).toBe(tabs[0]);
    });

    it('prevents the keys it handles and ignores other keys', () => {
      const tabs = ctabsOf(enhanced());
      tabs[0].focus();
      expect(press(tabs[0], 'ArrowRight').defaultPrevented).toBe(true);
      expect(press(tabs[0], 'a').defaultPrevented).toBe(false);
    });
  });
});
