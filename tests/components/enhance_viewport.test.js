import { mountViewport } from '@ui/static/viewport.js';
import { stubBox } from './stub-layout.js';

function setup(options) {
  const frame = document.createElement('div');
  frame.innerHTML =
    '<svg width="400" height="200" viewBox="0 0 400 200"><rect x="0" y="0" width="10" height="10"></rect></svg>';
  document.body.append(frame);
  const svg = frame.querySelector('svg');
  stubBox(svg, { width: 400, height: 200 });
  const viewport = mountViewport(frame, svg, options);
  return { frame, svg, viewport, bar: viewport.bar };
}

function viewBoxOf(svg) {
  return svg.getAttribute('viewBox').split(/\s+/).map(Number);
}

function expectView(svg, expected) {
  const actual = viewBoxOf(svg);
  expect(actual).toHaveLength(4);
  expected.forEach((value, i) => expect(actual[i]).toBeCloseTo(value, 6));
}

function button(bar, label) {
  return bar.querySelector(`[aria-label="${label}"]`);
}

function keyOn(target, key) {
  const event = new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true });
  target.dispatchEvent(event);
  return event;
}

function pointer(type, target, { x = 0, y = 0, id = 1, buttons = 1 } = {}) {
  const event = new Event(type, { bubbles: true, cancelable: true });
  Object.defineProperties(event, {
    clientX: { value: x },
    clientY: { value: y },
    pointerId: { value: id },
    buttons: { value: buttons }
  });
  target.dispatchEvent(event);
  return event;
}

function wheel(target, { x = 0, y = 0, deltaY = 0, ctrlKey = false, metaKey = false } = {}) {
  const event = new Event('wheel', { bubbles: true, cancelable: true });
  Object.defineProperties(event, {
    clientX: { value: x },
    clientY: { value: y },
    deltaY: { value: deltaY },
    ctrlKey: { value: ctrlKey },
    metaKey: { value: metaKey }
  });
  target.dispatchEvent(event);
  return event;
}

afterEach(() => {
  document.body.replaceChildren();
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe('mountViewport bar', () => {
  it('inserts the bar before the frame with Zoom in, Zoom out and Reset view', () => {
    const { frame, bar } = setup();
    expect(frame.previousElementSibling).toBe(bar);
    expect(bar.className).toBe('vb-flowbar');
    expect(button(bar, 'Zoom in')).not.toBeNull();
    expect(button(bar, 'Zoom out')).not.toBeNull();
    expect(button(bar, 'Reset view')).not.toBeNull();
  });

  it('sets touch-action so one finger still scrolls the page', () => {
    const { svg } = setup();
    expect(svg.getAttribute('style')).toContain('touch-action: pan-x pan-y');
  });

  it('zooms about the centre from the bar buttons and resets from Reset view', () => {
    const { svg, bar } = setup();
    button(bar, 'Zoom in').click();
    expectView(svg, [40, 20, 320, 160]);
    button(bar, 'Zoom out').click();
    expectView(svg, [0, 0, 400, 200]);
    button(bar, 'Zoom in').click();
    button(bar, 'Reset view').click();
    expectView(svg, [0, 0, 400, 200]);
  });
});

describe('mountViewport zoom', () => {
  it('keeps the centre fixed when no point is given', () => {
    const { svg, viewport } = setup();
    viewport.zoom(2);
    expectView(svg, [100, 50, 200, 100]);
  });

  it('keeps the given point at the same fraction of the view', () => {
    const { svg, viewport } = setup();
    viewport.zoom(2, 100, 50);
    expectView(svg, [50, 25, 200, 100]);
    expect((100 - 50) / 200).toBeCloseTo((100 - 0) / 400, 6);
  });

  it('clamps at the default 0.25 to 8 scale', () => {
    const { svg, bar } = setup();
    for (let i = 0; i < 30; i += 1) button(bar, 'Zoom out').click();
    expect(viewBoxOf(svg)[2]).toBeCloseTo(1600, 6);
    for (let i = 0; i < 40; i += 1) button(bar, 'Zoom in').click();
    expect(viewBoxOf(svg)[2]).toBeCloseTo(50, 6);
  });

  it('clamps at the given minScale and maxScale', () => {
    const { svg, bar } = setup({ minScale: 0.5, maxScale: 4 });
    for (let i = 0; i < 30; i += 1) button(bar, 'Zoom out').click();
    expect(viewBoxOf(svg)[2]).toBeCloseTo(800, 6);
    for (let i = 0; i < 40; i += 1) button(bar, 'Zoom in').click();
    expect(viewBoxOf(svg)[2]).toBeCloseTo(100, 6);
  });
});

describe('mountViewport pan and reset', () => {
  it('pan moves the view by the given amount in view units', () => {
    const { svg, viewport } = setup();
    viewport.pan(10, -5);
    expectView(svg, [-10, 5, 400, 200]);
  });

  it('reset restores the viewBox it started with', () => {
    const { svg, viewport } = setup();
    viewport.zoom(2);
    viewport.pan(30, 30);
    viewport.reset();
    expectView(svg, [0, 0, 400, 200]);
  });
});

describe('mountViewport keys', () => {
  it('arrows pan the view and are prevented', () => {
    const { frame, svg } = setup();
    expect(keyOn(frame, 'ArrowLeft').defaultPrevented).toBe(true);
    expectView(svg, [-24, 0, 400, 200]);
    keyOn(frame, 'ArrowRight');
    keyOn(frame, 'ArrowRight');
    expectView(svg, [24, 0, 400, 200]);
    keyOn(frame, 'ArrowUp');
    expectView(svg, [24, -24, 400, 200]);
    keyOn(frame, 'ArrowDown');
    keyOn(frame, 'ArrowDown');
    expectView(svg, [24, 24, 400, 200]);
  });

  it('plus and equals zoom in, minus zooms out, zero resets', () => {
    const { frame, svg } = setup();
    expect(keyOn(frame, '+').defaultPrevented).toBe(true);
    expectView(svg, [40, 20, 320, 160]);
    keyOn(frame, '-');
    expectView(svg, [0, 0, 400, 200]);
    keyOn(frame, '=');
    expectView(svg, [40, 20, 320, 160]);
    expect(keyOn(frame, '0').defaultPrevented).toBe(true);
    expectView(svg, [0, 0, 400, 200]);
  });

  it('ignores keys from children and other keys, which are not prevented', () => {
    const { frame, svg } = setup();
    const child = frame.querySelector('rect');
    expect(keyOn(child, 'ArrowLeft').defaultPrevented).toBe(false);
    expect(keyOn(frame, 'a').defaultPrevented).toBe(false);
    expectView(svg, [0, 0, 400, 200]);
  });
});

describe('mountViewport drag', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it('does nothing for a move under 4px', () => {
    const { svg } = setup();
    pointer('pointerdown', svg, { x: 100, y: 100 });
    pointer('pointermove', svg, { x: 102, y: 101 });
    expectView(svg, [0, 0, 400, 200]);
  });

  it('pans by the drag in view units', () => {
    const { svg } = setup();
    pointer('pointerdown', svg, { x: 100, y: 100 });
    pointer('pointermove', svg, { x: 140, y: 100 });
    expectView(svg, [-40, 0, 400, 200]);
    pointer('pointermove', svg, { x: 150, y: 100 });
    expectView(svg, [-50, 0, 400, 200]);
  });

  it('scales the drag by the zoom level', () => {
    const { svg, bar } = setup();
    button(bar, 'Zoom in').click();
    pointer('pointerdown', svg, { x: 100, y: 100 });
    pointer('pointermove', svg, { x: 140, y: 100 });
    expectView(svg, [8, 20, 320, 160]);
  });

  it('pans only with the primary button held', () => {
    const { svg } = setup();
    pointer('pointerdown', svg, { x: 100, y: 100 });
    pointer('pointermove', svg, { x: 160, y: 100, buttons: 2 });
    expectView(svg, [0, 0, 400, 200]);
  });

  it('stops the click that follows a drag, until the timers run', () => {
    const { frame, svg } = setup();
    const onClick = vi.fn();
    frame.addEventListener('click', onClick);
    pointer('pointerdown', svg, { x: 100, y: 100 });
    pointer('pointermove', svg, { x: 150, y: 100 });
    pointer('pointerup', svg, { x: 150, y: 100, buttons: 0 });
    svg.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    expect(onClick).not.toHaveBeenCalled();
    vi.runAllTimers();
    svg.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('lets a plain click through', () => {
    const { frame, svg } = setup();
    const onClick = vi.fn();
    frame.addEventListener('click', onClick);
    pointer('pointerdown', svg, { x: 100, y: 100 });
    pointer('pointerup', svg, { x: 100, y: 100, buttons: 0 });
    svg.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('ends on pointercancel', () => {
    const { svg } = setup();
    pointer('pointerdown', svg, { x: 100, y: 100 });
    pointer('pointercancel', svg, { x: 100, y: 100, buttons: 0 });
    vi.runAllTimers();
    pointer('pointermove', svg, { x: 200, y: 100 });
    expectView(svg, [0, 0, 400, 200]);
  });

  it('pinch-zooms about the midpoint of two pointers', () => {
    const { svg } = setup();
    pointer('pointerdown', svg, { x: 100, y: 100, id: 1 });
    pointer('pointerdown', svg, { x: 200, y: 100, id: 2 });
    pointer('pointermove', svg, { x: 300, y: 100, id: 2 });
    expectView(svg, [100, 50, 200, 100]);
  });

  it('continues the drag with the remaining pointer after one lifts, without a jump', () => {
    const { svg } = setup();
    pointer('pointerdown', svg, { x: 100, y: 100, id: 1 });
    pointer('pointerdown', svg, { x: 200, y: 100, id: 2 });
    pointer('pointermove', svg, { x: 300, y: 100, id: 2 });
    pointer('pointerup', svg, { x: 100, y: 100, id: 1, buttons: 0 });
    pointer('pointermove', svg, { x: 310, y: 100, id: 2 });
    expectView(svg, [95, 50, 200, 100]);
  });
});

describe('mountViewport wheel', () => {
  it('zooms in with Ctrl and a negative deltaY, about the pointer', () => {
    const { svg } = setup();
    const event = wheel(svg, { x: 200, y: 100, deltaY: -100, ctrlKey: true });
    expect(event.defaultPrevented).toBe(true);
    expectView(svg, [33.333333, 16.666667, 333.333333, 166.666667]);
  });

  it('zooms out with Meta and a positive deltaY', () => {
    const { svg } = setup();
    const event = wheel(svg, { x: 200, y: 100, deltaY: 100, metaKey: true });
    expect(event.defaultPrevented).toBe(true);
    expectView(svg, [-40, -20, 480, 240]);
  });

  it('leaves a wheel without Ctrl or Meta to the page', () => {
    const { svg } = setup();
    const event = wheel(svg, { x: 200, y: 100, deltaY: -100 });
    expect(event.defaultPrevented).toBe(false);
    expectView(svg, [0, 0, 400, 200]);
  });
});
