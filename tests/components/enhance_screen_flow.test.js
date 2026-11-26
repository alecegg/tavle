import { enhanceScreenFlow } from '@ui/static/screen_flow.js';
import fixtures from './fixtures/screen-flow.json';
import { fragment } from './canonical.js';

function setup() {
  const root = fragment(fixtures.find((item) => item.name === 'rich-screen-flow:f1').html);
  document.body.append(...root.childNodes);
  const block = document.querySelector('.screen-flow');
  const views = [...block.querySelectorAll('.vd-sf-view')];
  views.forEach((view) => (view.scrollTo = vi.fn()));
  enhanceScreenFlow(block);
  return { block, views, readout: block.querySelector('.vd-sf-detail') };
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

describe('screen flow enhancement', () => {
  it('leaves unrelated blocks and views without an SVG alone', () => {
    const block = document.createElement('div');
    block.innerHTML = '<div class="vd-sf-views"><div class="vd-sf-view"></div></div>';
    const before = block.innerHTML;
    enhanceScreenFlow(block);
    expect(block.innerHTML).toBe(before);
    block.className = 'screen-flow';
    enhanceScreenFlow(block);
    expect(block.innerHTML).toBe(before);
  });

  it('sets accessible screen controls and one tab stop in each view', () => {
    const { views } = setup();
    expect(views).toHaveLength(2);
    for (const view of views) {
      const screens = [...view.querySelectorAll('.vd-sf-screen')];
      expect(screens.length).toBe(5);
      expect(screens.filter((screen) => screen.getAttribute('tabindex') === '0')).toHaveLength(1);
      expect(screens[0].getAttribute('role')).toBe('button');
      expect(screens[0].getAttribute('aria-label')).toBe(screens[0].querySelector('title').textContent);
      expect(screens[0].getAttribute('aria-pressed')).toBe('false');
    }
  });

  it('selects copies and list items, describes notes, and clears', () => {
    const { block, views, readout } = setup();
    const cart = views[0].querySelector('[data-screen="cart"].vd-sf-screen');
    cart.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    expect(readout.textContent).toBe(
      'Cart. 4 regions: header, lines, summary, pay button. Note 1: pay button: Disabled while the cart is empty. Note 2: lines: Quantity changes save at once. next: Payment (Pay).'
    );
    for (const view of views) {
      const copy = view.querySelector('[data-screen="cart"].vd-sf-screen');
      expect(copy.classList.contains('vd-sf-sel')).toBe(true);
      expect(copy.getAttribute('aria-pressed')).toBe('true');
    }
    expect(block.querySelector('.vd-sf-item[data-screen="cart"]').classList.contains('vd-sf-item-on')).toBe(true);
    cart.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    expect(readout.textContent).toContain('Select a screen');
    const done = views[0].querySelector('.vd-sf-screen[data-screen="done"]');
    key(done, 'Enter');
    expect(readout.textContent).toBe('Thanks. 2 regions: header, confirmation. No notes. end of flow.');
    expect(key(done, 'Escape').defaultPrevented).toBe(true);
    expect(readout.textContent).toContain('Select a screen');
    key(done, ' ');
    expect(done.getAttribute('aria-pressed')).toBe('true');
  });

  it('highlights hover and focus across views and moves focus with keys', () => {
    const { views } = setup();
    const screens = [...views[0].querySelectorAll('.vd-sf-screen')];
    screens[1].dispatchEvent(new Event('pointerover', { bubbles: true }));
    expect(views[1].querySelector('.vd-sf-screen[data-screen="pay"]').classList.contains('vd-sf-hot')).toBe(true);
    views[0].dispatchEvent(new Event('pointerleave'));
    expect(screens[1].classList.contains('vd-sf-hot')).toBe(false);
    screens[0].focus();
    expect(screens[0].classList.contains('vd-sf-hot')).toBe(true);
    expect(key(screens[0], 'ArrowLeft').defaultPrevented).toBe(true);
    expect(document.activeElement).toBe(screens[4]);
    expect(screens[4].getAttribute('tabindex')).toBe('0');
    key(screens[4], 'Home');
    expect(document.activeElement).toBe(screens[0]);
    key(screens[0], 'End');
    expect(document.activeElement).toBe(screens[4]);
    key(screens[4], 'ArrowRight');
    expect(document.activeElement).toBe(screens[0]);
  });

  it('zooms both views and resets their original viewBoxes', () => {
    const { block, views } = setup();
    const svgs = views.map((view) => view.querySelector('svg'));
    const original = svgs.map((svg) => svg.getAttribute('viewBox'));
    block.querySelector('[aria-label="Zoom in"]').click();
    svgs.forEach((svg, i) => expect(svg.getAttribute('viewBox')).not.toBe(original[i]));
    block.querySelector('[aria-label="Zoom out"]').click();
    block.querySelector('[aria-label="Reset flow view"]').click();
    svgs.forEach((svg, i) => expect(svg.getAttribute('viewBox')).toBe(original[i]));
    views.forEach((view) => expect(view.scrollTo).toHaveBeenCalledWith(0, 0));
  });
});
