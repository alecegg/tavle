import { enhanceWireframe } from '@ui/static/wireframe.js';
import fixtures from './fixtures/wireframe.json';
import { fragment } from './canonical.js';
import { stubBox } from './stub-layout.js';

function setup() {
  const root = fragment(fixtures.find((item) => item.name === 'rich-wireframe:w2').html);
  document.body.append(...root.childNodes);
  const block = document.querySelector('.wireframe');
  const views = [...block.querySelectorAll('.vw-view')];
  for (const view of views) {
    stubBox(view, { width: 218 });
    view.scrollTo = vi.fn();
  }
  enhanceWireframe(block);
  const frames = [...block.querySelectorAll('.vw-fig')].map((fig) => ({
    svg: fig.querySelector('svg'),
    home: fig.querySelector('svg').getAttribute('viewBox'),
    view: fig.querySelector('.vw-view'),
    regions: [...fig.querySelectorAll('.vw-region')],
    notes: [...fig.querySelectorAll('.vw-note')]
  }));
  return { block, views, frames, readout: block.querySelector('.vw-detail') };
}

// A pointer event with the fields the handlers read; jsdom has no PointerEvent.
function pointer(node, type, { x = 0, y = 0, pointerType = 'touch', time = 0 } = {}) {
  const event = new MouseEvent(type, { bubbles: true, cancelable: true, clientX: x, clientY: y });
  Object.defineProperties(event, { pointerType: { value: pointerType }, timeStamp: { value: time } });
  node.dispatchEvent(event);
  return event;
}

function tap(node, { x = 0, y = 0, time = 0, pointerType = 'touch' } = {}) {
  pointer(node, 'pointerdown', { x, y, time, pointerType });
  pointer(node, 'pointerup', { x, y, time, pointerType });
}

function key(node, value) {
  const event = new KeyboardEvent('keydown', { key: value, bubbles: true, cancelable: true });
  node.dispatchEvent(event);
  return event;
}

function click(node) {
  node.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
}

function byLabel(block, label) {
  return block.querySelector(`[aria-label="${label}"]`);
}

function regionKeyed(frame, id) {
  return frame.regions.find((region) => region.dataset.region === id);
}

afterEach(() => {
  document.body.replaceChildren();
  vi.restoreAllMocks();
});

describe('wireframe enhancement', () => {
  it('ignores other blocks', () => {
    const other = document.createElement('div');
    enhanceWireframe(other);
    expect(other.children).toHaveLength(0);
  });

  it('gives regions roles, labels and one tab stop per frame', () => {
    const { frames, readout } = setup();
    const [before, after] = frames;
    expect(before.svg.getAttribute('role')).toBe('group');
    expect(before.view.getAttribute('aria-label')).toContain('Checkout: before (arrow keys pan');
    expect(regionKeyed(before, 'B').getAttribute('role')).toBe('button');
    expect(regionKeyed(before, 'B').getAttribute('aria-label')).toBe('pay button (action), region');
    expect(regionKeyed(before, 'B').getAttribute('aria-pressed')).toBe('false');
    for (const frame of frames) {
      expect(frame.regions.filter((region) => region.getAttribute('tabindex') === '0')).toHaveLength(1);
    }
    expect(before.regions[0].getAttribute('tabindex')).toBe('0');
    expect(after.regions[0].getAttribute('tabindex')).toBe('0');
    expect(readout.textContent).toBe('Select a region to read its notes.');
  });

  it('keeps one shared bar and removes the per-frame viewport bars', () => {
    const { block } = setup();
    expect(block.querySelectorAll('[aria-label="Zoom in"]')).toHaveLength(1);
    expect(block.querySelectorAll('[aria-label="Reset view"]')).toHaveLength(0);
  });

  it('reads the caption, region and notes on click, and clears on a second click', () => {
    const { frames, readout } = setup();
    click(regionKeyed(frames[0], 'B'));
    expect(readout.textContent).toBe('Before: pay button (action). Note 1: Disabled until the card is valid.');
    expect(regionKeyed(frames[0], 'B').classList.contains('vw-sel')).toBe(true);
    expect(regionKeyed(frames[0], 'B').getAttribute('aria-pressed')).toBe('true');
    click(regionKeyed(frames[0], 'B'));
    expect(readout.textContent).toBe('Select a region to read its notes.');
    expect(regionKeyed(frames[0], 'B').classList.contains('vw-sel')).toBe(false);
  });

  it('reads "No notes." for a region without notes and selects with Enter and Space', () => {
    const { frames, readout } = setup();
    key(regionKeyed(frames[0], 'T'), 'Enter');
    expect(readout.textContent).toBe('Before: title. No notes.');
    expect(key(regionKeyed(frames[0], 'T'), ' ').defaultPrevented).toBe(true);
    expect(readout.textContent).toBe('Select a region to read its notes.');
  });

  it('keeps the selection per frame and lights only the selected note', () => {
    const { frames, readout } = setup();
    click(regionKeyed(frames[0], 'B'));
    click(regionKeyed(frames[1], 'S'));
    expect(readout.textContent).toBe('After: saved cards (list). Note 1: New: pick a saved card.');
    expect(regionKeyed(frames[0], 'B').classList.contains('vw-sel')).toBe(false);
    expect(regionKeyed(frames[1], 'S').classList.contains('vw-sel')).toBe(true);
    expect(frames[1].notes[0].classList.contains('vw-note-on')).toBe(true);
    expect(frames[0].notes[0].classList.contains('vw-note-on')).toBe(false);
    click(regionKeyed(frames[0], 'T'));
    expect(regionKeyed(frames[1], 'S').classList.contains('vw-sel')).toBe(false);
    expect(regionKeyed(frames[1], 'T').classList.contains('vw-sel')).toBe(false);
  });

  it('marks hover and focus with vw-hot and gives hover the priority', () => {
    const { frames } = setup();
    click(regionKeyed(frames[0], 'B'));
    regionKeyed(frames[0], 'T').focus();
    expect(regionKeyed(frames[0], 'T').classList.contains('vw-hot')).toBe(true);
    expect(regionKeyed(frames[0], 'B').classList.contains('vw-sel')).toBe(true);
    regionKeyed(frames[0], 'M').dispatchEvent(new Event('pointerover', { bubbles: true }));
    expect(regionKeyed(frames[0], 'M').classList.contains('vw-hot')).toBe(true);
    expect(regionKeyed(frames[0], 'T').classList.contains('vw-hot')).toBe(false);
    regionKeyed(frames[0], 'M').dispatchEvent(new Event('pointerleave', { bubbles: true }));
    expect(regionKeyed(frames[0], 'T').classList.contains('vw-hot')).toBe(true);
  });

  it('moves focus with arrows wrapping at both ends, and Home and End jump', () => {
    const { frames } = setup();
    const [t, m, b] = frames[0].regions;
    t.focus();
    expect(key(t, 'ArrowRight').defaultPrevented).toBe(true);
    expect(document.activeElement).toBe(m);
    expect(key(m, 'ArrowDown').defaultPrevented).toBe(true);
    expect(document.activeElement).toBe(b);
    key(b, 'ArrowRight');
    expect(document.activeElement).toBe(t);
    key(t, 'ArrowUp');
    expect(document.activeElement).toBe(b);
    key(b, 'Home');
    expect(document.activeElement).toBe(t);
    key(t, 'End');
    expect(document.activeElement).toBe(b);
    expect(regionKeyed(frames[0], 'B').getAttribute('tabindex')).toBe('0');
    expect(t.getAttribute('tabindex')).toBe('-1');
  });

  it('clears the selection on Escape and ignores other keys', () => {
    const { frames, readout } = setup();
    click(regionKeyed(frames[0], 'B'));
    expect(key(regionKeyed(frames[0], 'B'), 'Escape').defaultPrevented).toBe(true);
    expect(readout.textContent).toBe('Select a region to read its notes.');
    expect(key(regionKeyed(frames[0], 'B'), 'x').defaultPrevented).toBe(false);
  });

  it('zooms every frame from the shared bar and Fit resets each view', () => {
    const { block, frames } = setup();
    const [before, after] = frames.map((frame) => frame.svg);
    byLabel(block, 'Zoom in').click();
    expect(Number(before.getAttribute('viewBox').split(' ')[2])).toBeCloseTo(204 / 1.25);
    expect(Number(after.getAttribute('viewBox').split(' ')[2])).toBeCloseTo(204 / 1.25);
    byLabel(block, 'Fit whole wireframe').click();
    expect(before.getAttribute('viewBox')).toBe(frames[0].home);
    expect(after.getAttribute('viewBox')).toBe(frames[1].home);
    for (const view of frames.map((frame) => frame.view)) expect(view.scrollTo).toHaveBeenCalledWith(0, 0);
  });

  it('sizes each svg to the view width, never above 1:1 and never below 0.5', () => {
    const { block, views, frames } = setup();
    const fit = () => byLabel(block, 'Fit whole wireframe').click();
    stubBox(views[1], { width: 218 });
    fit();
    expect(frames[1].svg.getAttribute('width')).toBe('200');
    expect(frames[1].svg.getAttribute('height')).toBe('255');
    stubBox(views[1], { width: 1000 });
    fit();
    expect(frames[1].svg.getAttribute('width')).toBe('204');
    expect(frames[1].svg.getAttribute('height')).toBe('260');
    stubBox(views[1], { width: 0 });
    fit();
    expect(frames[1].svg.getAttribute('width')).toBe('102');
    expect(frames[1].svg.getAttribute('height')).toBe('130');
  });

  it('fits on double-click and prevents the default', () => {
    const { block, frames } = setup();
    const svg = frames[0].svg;
    byLabel(block, 'Zoom in').click();
    const event = new MouseEvent('dblclick', { bubbles: true, cancelable: true });
    svg.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
    expect(svg.getAttribute('viewBox')).toBe(frames[0].home);
  });

  it('fits on two quick touch taps close together', () => {
    const { block, frames } = setup();
    const svg = frames[0].svg;
    byLabel(block, 'Zoom in').click();
    tap(svg, { x: 10, y: 10, time: 100 });
    expect(svg.getAttribute('viewBox')).not.toBe(frames[0].home);
    tap(svg, { x: 12, y: 10, time: 300 });
    expect(svg.getAttribute('viewBox')).toBe(frames[0].home);
  });

  // Each case zooms in first; a fit would reset the viewBox to VIEW_BOX.
  function expectNoFit(taps) {
    const { block, frames } = setup();
    const svg = frames[0].svg;
    byLabel(block, 'Zoom in').click();
    const zoomed = svg.getAttribute('viewBox');
    taps(svg);
    expect(svg.getAttribute('viewBox')).toBe(zoomed);
  }

  it('does not fit two taps more than 350ms apart', () => {
    expectNoFit((svg) => {
      tap(svg, { x: 10, y: 10, time: 100 });
      tap(svg, { x: 10, y: 10, time: 500 });
    });
  });

  it('does not fit two taps more than 30px apart', () => {
    expectNoFit((svg) => {
      tap(svg, { x: 0, y: 0, time: 100 });
      tap(svg, { x: 40, y: 0, time: 200 });
    });
  });

  it('does not count a tap that moved more than 30px', () => {
    expectNoFit((svg) => {
      pointer(svg, 'pointerdown', { x: 0, y: 0, time: 100 });
      pointer(svg, 'pointerup', { x: 40, y: 0, time: 110 });
      tap(svg, { x: 40, y: 0, time: 200 });
    });
  });

  it('does not count multi-touch taps', () => {
    expectNoFit((svg) => {
      for (const time of [800, 900]) {
        pointer(svg, 'pointerdown', { x: 0, y: 0, time });
        pointer(svg, 'pointerdown', { x: 0, y: 0, time: time + 1 });
        pointer(svg, 'pointerup', { x: 0, y: 0, time: time + 2 });
        pointer(svg, 'pointerup', { x: 0, y: 0, time: time + 3 });
      }
    });
  });

  it('does not count mouse taps', () => {
    expectNoFit((svg) => {
      tap(svg, { x: 0, y: 0, time: 100, pointerType: 'mouse' });
      tap(svg, { x: 0, y: 0, time: 150, pointerType: 'mouse' });
    });
  });
});
